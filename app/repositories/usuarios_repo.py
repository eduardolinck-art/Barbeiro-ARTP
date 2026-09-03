from supabase import Client

from app.models import Perfil


def criar_perfil(client: Client, user_id: str, nome: str, celular: str, email: str) -> Perfil:
    row = {"id": user_id, "nome": nome, "celular": celular, "email": email}
    resposta = client.table("perfis").insert(row).execute()
    return Perfil.from_row(resposta.data[0])


def obter_perfil(client: Client, user_id: str) -> Perfil | None:
    resposta = client.table("perfis").select("*").eq("id", user_id).limit(1).execute()
    if not resposta.data:
        return None
    return Perfil.from_row(resposta.data[0])


def atualizar_perfil(client: Client, user_id: str, **campos) -> Perfil:
    resposta = client.table("perfis").update(campos).eq("id", user_id).execute()
    return Perfil.from_row(resposta.data[0])
