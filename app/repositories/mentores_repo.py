from supabase import Client

from app.models import Curso, Mentor
from app.supabase_client import get_admin_client

# anon/authenticated só têm GRANT de leitura em (id, nome) na tabela `mentores` —
# os campos de token do Google só podem ser lidos com o client admin.
_COLUNAS_PUBLICAS = "id, nome"


def listar_mentores(client: Client) -> list[Mentor]:
    resposta = client.table("mentores").select(_COLUNAS_PUBLICAS).order("nome").execute()
    return [Mentor.from_row(row) for row in resposta.data]


def obter_mentor(client: Client, mentor_id: str) -> Mentor | None:
    resposta = (
        client.table("mentores").select(_COLUNAS_PUBLICAS).eq("id", mentor_id).limit(1).execute()
    )
    if not resposta.data:
        return None
    return Mentor.from_row(resposta.data[0])


def obter_mentor_com_credenciais(mentor_id: str) -> Mentor | None:
    """Uso exclusivo do app/google_calendar.py — traz também os tokens OAuth do mentor."""
    resposta = (
        get_admin_client().table("mentores").select("*").eq("id", mentor_id).limit(1).execute()
    )
    if not resposta.data:
        return None
    return Mentor.from_row(resposta.data[0])


def listar_cursos(client: Client) -> list[Curso]:
    resposta = client.table("cursos").select("*").order("nome").execute()
    return [Curso.from_row(row) for row in resposta.data]


def salvar_tokens_google(
    mentor_id: str,
    google_calendar_id: str,
    refresh_token: str,
    access_token: str,
    token_expiry: str | None,
) -> None:
    """Grava as credenciais OAuth do mentor. Usa o client com service role
    porque a tabela `mentores` não pertence a nenhum usuário autenticado específico."""
    get_admin_client().table("mentores").update(
        {
            "google_calendar_id": google_calendar_id,
            "google_refresh_token": refresh_token,
            "google_access_token": access_token,
            "token_expiry": token_expiry,
        }
    ).eq("id", mentor_id).execute()
