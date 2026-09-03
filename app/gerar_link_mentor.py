"""Gera (ou renova) o link secreto de conexão do Google Agenda de um mentor.

Uso: python -m app.gerar_link_mentor <mentor_id>
Exemplo: python -m app.gerar_link_mentor caroline_bonora
"""

import secrets
import sys

from app.supabase_client import get_admin_client


def gerar_link(mentor_id: str) -> str | None:
    admin = get_admin_client()
    existe = admin.table("mentores").select("id, nome").eq("id", mentor_id).limit(1).execute()
    if not existe.data:
        return None

    token = secrets.token_urlsafe(24)
    admin.table("mentores").update({"link_token": token}).eq("id", mentor_id).execute()

    nome = existe.data[0]["nome"]
    print(f"Mentor: {nome}")
    print(f"Link: https://SEU-DOMINIO/conectar/{mentor_id}/{token}")
    return token


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m app.gerar_link_mentor <mentor_id>")
        sys.exit(1)

    if gerar_link(sys.argv[1]) is None:
        print(f"Mentor '{sys.argv[1]}' não encontrado.")
        sys.exit(1)
