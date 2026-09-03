import random
from datetime import date, datetime, time

from supabase import Client

from app.models import Agendamento
from app.supabase_client import get_admin_client

_SELECT_COM_RELACOES = "*, mentores(nome), cursos(nome)"


def gerar_protocolo(hoje: date | None = None) -> str:
    hoje = hoje or date.today()
    sufixo = random.randint(1000, 9999)
    return f"PM{hoje.strftime('%Y%m%d')}-{sufixo}"


def existe_conflito(mentor_id: str, data: date, hora: time) -> bool:
    """True se já existe um agendamento ativo para esse mentor nesse horário (evita overbooking).
    Usa o client admin porque precisa enxergar agendamentos de QUALQUER mentorado, e a RLS de
    `agendamentos` só deixa cada usuário ver os próprios."""
    resposta = (
        get_admin_client()
        .table("agendamentos")
        .select("id")
        .eq("mentor_id", mentor_id)
        .eq("data", data.isoformat())
        .eq("hora", hora.isoformat())
        .eq("status", "agendado")
        .limit(1)
        .execute()
    )
    return len(resposta.data) > 0


def contar_agendamentos_futuros_por_mentor(mentor_id: str) -> int:
    """Também precisa do client admin, pelo mesmo motivo de existe_conflito."""
    hoje = date.today().isoformat()
    resposta = (
        get_admin_client()
        .table("agendamentos")
        .select("id", count="exact")
        .eq("mentor_id", mentor_id)
        .eq("status", "agendado")
        .gte("data", hoje)
        .execute()
    )
    return resposta.count or 0


def criar_agendamento(
    client: Client,
    mentorado_id: str,
    mentor_id: str,
    curso_id: str,
    data: date,
    hora: time,
    google_event_id: str | None = None,
) -> Agendamento:
    row = {
        "mentorado_id": mentorado_id,
        "mentor_id": mentor_id,
        "curso_id": curso_id,
        "data": data.isoformat(),
        "hora": hora.isoformat(),
        "status": "agendado",
        "protocolo": gerar_protocolo(data),
        "google_event_id": google_event_id,
    }
    resposta = client.table("agendamentos").insert(row).execute()
    return Agendamento.from_row(resposta.data[0])


def listar_agendamentos_usuario(client: Client, mentorado_id: str) -> list[Agendamento]:
    resposta = (
        client.table("agendamentos")
        .select(_SELECT_COM_RELACOES)
        .eq("mentorado_id", mentorado_id)
        .order("data", desc=True)
        .order("hora", desc=True)
        .execute()
    )
    return [Agendamento.from_row(row) for row in resposta.data]


def listar_historico_usuario(client: Client, mentorado_id: str) -> list[Agendamento]:
    """Agendamentos já ocorridos: status 'realizado' ou data/hora no passado."""
    agora = datetime.now()
    agendamentos = listar_agendamentos_usuario(client, mentorado_id)
    return [
        a
        for a in agendamentos
        if a.status == "realizado"
        or a.status == "agendado"
        and datetime.combine(a.data, a.hora) < agora
    ]


def atualizar_status(client: Client, agendamento_id: str, status: str) -> None:
    client.table("agendamentos").update({"status": status}).eq("id", agendamento_id).execute()
