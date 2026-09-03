"""Integração com a Google Calendar API.

Cada mentor conecta a própria conta Google (OAuth 2.0, escopo `calendar`).
Os tokens ficam persistidos na tabela `mentores` (via mentores_repo).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import config
from app.models import Agendamento, Mentor
from app.repositories import agendamentos_repo, mentores_repo

HORARIO_EXPEDIENTE = (9, 18)  # 09h às 18h
DURACAO_SLOT_MINUTOS = 60


class GoogleCalendarError(Exception):
    """Erro de integração com o Google Calendar, com mensagem amigável para exibir na UI."""


def _flow(state: str | None = None) -> Flow:
    client_config = {
        "web": {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [config.GOOGLE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=config.GOOGLE_CALENDAR_SCOPES,
        redirect_uri=config.GOOGLE_REDIRECT_URI,
        state=state,
    )


def build_authorization_url(mentor_id: str) -> str:
    """Gera a URL para o mentor autorizar o acesso à própria agenda. `state` carrega o mentor_id."""
    flow = _flow(state=mentor_id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_and_save(mentor_id: str, code: str) -> None:
    """Troca o `code` do callback OAuth pelos tokens e salva no mentor."""
    flow = _flow(state=mentor_id)
    flow.fetch_token(code=code)
    credentials = flow.credentials

    service = build("calendar", "v3", credentials=credentials)
    calendario_primario = service.calendarList().get(calendarId="primary").execute()

    mentores_repo.salvar_tokens_google(
        mentor_id=mentor_id,
        google_calendar_id=calendario_primario["id"],
        refresh_token=credentials.refresh_token,
        access_token=credentials.token,
        token_expiry=credentials.expiry.isoformat() if credentials.expiry else None,
    )


def _build_credentials(mentor: Mentor) -> Credentials:
    if not mentor.google_refresh_token:
        raise GoogleCalendarError(
            f"O mentor {mentor.nome} ainda não conectou a agenda do Google."
        )
    return Credentials(
        token=mentor.google_access_token,
        refresh_token=mentor.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=config.GOOGLE_CALENDAR_SCOPES,
    )


def refresh_access_token_if_needed(mentor_id: str) -> Credentials:
    mentor = mentores_repo.obter_mentor_com_credenciais(mentor_id)
    if mentor is None:
        raise GoogleCalendarError("Mentor não encontrado.")

    credentials = _build_credentials(mentor)
    if not credentials.valid:
        try:
            credentials.refresh(Request())
        except Exception as exc:  # noqa: BLE001 - qualquer falha de refresh vira erro de UI
            raise GoogleCalendarError(
                f"Não foi possível renovar o acesso à agenda de {mentor.nome}. "
                "Ele(a) pode ter revogado a permissão — peça para reconectar em Perfil > Google Agenda."
            ) from exc

        mentores_repo.salvar_tokens_google(
            mentor_id=mentor_id,
            google_calendar_id=mentor.google_calendar_id,
            refresh_token=credentials.refresh_token or mentor.google_refresh_token,
            access_token=credentials.token,
            token_expiry=credentials.expiry.isoformat() if credentials.expiry else None,
        )
    return credentials


def _service_para_mentor(mentor_id: str):
    credentials = refresh_access_token_if_needed(mentor_id)
    return build("calendar", "v3", credentials=credentials)


def get_free_busy(mentor_id: str, data_inicio: date, data_fim: date) -> list[tuple[datetime, datetime]]:
    """Retorna os intervalos ocupados (busy) na agenda do mentor, entre duas datas."""
    mentor = mentores_repo.obter_mentor_com_credenciais(mentor_id)
    if mentor is None or not mentor.google_calendar_id:
        raise GoogleCalendarError(f"Mentor {mentor_id} não tem agenda do Google conectada.")

    try:
        service = _service_para_mentor(mentor_id)
        corpo = {
            "timeMin": datetime.combine(data_inicio, time.min).isoformat() + "Z",
            "timeMax": datetime.combine(data_fim, time.max).isoformat() + "Z",
            "items": [{"id": mentor.google_calendar_id}],
        }
        resposta = service.freebusy().query(body=corpo).execute()
        ocupados_raw = resposta["calendars"][mentor.google_calendar_id]["busy"]
        return [
            (
                datetime.fromisoformat(item["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(item["end"].replace("Z", "+00:00")),
            )
            for item in ocupados_raw
        ]
    except HttpError as exc:
        if exc.resp.status == 403:
            raise GoogleCalendarError(
                "Limite de uso da API do Google Agenda atingido. Tente novamente em alguns minutos."
            ) from exc
        raise GoogleCalendarError(f"Erro ao consultar a agenda de {mentor.nome}: {exc}") from exc


def listar_horarios_livres(mentor_id: str, dia: date) -> list[time]:
    """Cruza a disponibilidade real do Google Agenda com os agendamentos já gravados no Supabase."""
    ocupados_google = get_free_busy(mentor_id, dia, dia)

    candidatos = []
    hora = time(HORARIO_EXPEDIENTE[0], 0)
    while hora.hour < HORARIO_EXPEDIENTE[1]:
        candidatos.append(hora)
        proxima_hora = (hora.hour * 60 + hora.minute + DURACAO_SLOT_MINUTOS) // 60
        proximo_minuto = (hora.hour * 60 + hora.minute + DURACAO_SLOT_MINUTOS) % 60
        hora = time(proxima_hora, proximo_minuto)

    livres = []
    for slot in candidatos:
        inicio_slot = datetime.combine(dia, slot)
        fim_slot = inicio_slot + timedelta(minutes=DURACAO_SLOT_MINUTOS)

        conflita_google = any(
            inicio_slot < fim_ocupado and fim_slot > inicio_ocupado
            for inicio_ocupado, fim_ocupado in ocupados_google
        )
        if conflita_google:
            continue

        if agendamentos_repo.existe_conflito(mentor_id, dia, slot):
            continue

        livres.append(slot)

    return livres


def listar_horarios_livres_varios(mentores_ids: list[str], dia: date) -> list[time]:
    """União dos horários livres entre vários mentores — usado quando o mentorado escolhe
    'Sem preferência'. Mentores sem agenda do Google conectada são ignorados."""
    todos: set[time] = set()
    for mentor_id in mentores_ids:
        try:
            todos.update(listar_horarios_livres(mentor_id, dia))
        except GoogleCalendarError:
            continue
    return sorted(todos)


def escolher_mentor_sem_preferencia(mentores_ids: list[str], dia: date, hora: time) -> str | None:
    """Entre os mentores livres nesse horário, escolhe o que tem menos agendamentos futuros."""
    livres = []
    for mentor_id in mentores_ids:
        try:
            if hora in listar_horarios_livres(mentor_id, dia):
                livres.append(mentor_id)
        except GoogleCalendarError:
            continue
    if not livres:
        return None
    return min(livres, key=agendamentos_repo.contar_agendamentos_futuros_por_mentor)


def create_event(mentor_id: str, agendamento: Agendamento, mentorado_email: str, mentorado_nome: str) -> str:
    mentor = mentores_repo.obter_mentor_com_credenciais(mentor_id)
    if mentor is None:
        raise GoogleCalendarError("Mentor não encontrado.")

    service = _service_para_mentor(mentor_id)
    inicio = datetime.combine(agendamento.data, agendamento.hora)
    fim = inicio + timedelta(minutes=DURACAO_SLOT_MINUTOS)

    evento = {
        "summary": f"Mentoria: {mentorado_nome} com {mentor.nome}",
        "description": f"Protocolo: {agendamento.protocolo}",
        "start": {"dateTime": inicio.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": fim.isoformat(), "timeZone": "America/Sao_Paulo"},
        "attendees": [{"email": mentorado_email}],
    }

    try:
        criado = (
            service.events()
            .insert(calendarId=mentor.google_calendar_id, body=evento, sendUpdates="all")
            .execute()
        )
        return criado["id"]
    except HttpError as exc:
        raise GoogleCalendarError(f"Não foi possível criar o evento na agenda de {mentor.nome}: {exc}") from exc
