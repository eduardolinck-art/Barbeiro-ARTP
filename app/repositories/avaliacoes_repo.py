from supabase import Client

from app.models import Avaliacao


def obter_avaliacao(client: Client, agendamento_id: str) -> Avaliacao | None:
    resposta = (
        client.table("avaliacoes").select("*").eq("agendamento_id", agendamento_id).limit(1).execute()
    )
    if not resposta.data:
        return None
    return Avaliacao.from_row(resposta.data[0])


def salvar_avaliacao(client: Client, agendamento_id: str, nota: int, comentario: str | None = None) -> Avaliacao:
    existente = obter_avaliacao(client, agendamento_id)
    row = {"agendamento_id": agendamento_id, "nota": nota, "comentario": comentario}
    if existente:
        resposta = client.table("avaliacoes").update(row).eq("agendamento_id", agendamento_id).execute()
    else:
        resposta = client.table("avaliacoes").insert(row).execute()
    return Avaliacao.from_row(resposta.data[0])
