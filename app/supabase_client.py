from supabase import Client, create_client

from app import config

_admin_client: Client | None = None


def novo_client() -> Client:
    """Cria um client novo. IMPORTANTE: cada sessão de usuário (aba/conexão Flet) deve ter o
    seu próprio client, guardado em page.session — nunca compartilhar um client autenticado
    entre usuários diferentes, senão a sessão de um vaza para o outro."""
    return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)


def get_admin_client() -> Client:
    """Client com service role (ignora RLS). Não carrega sessão de usuário, pode ser reutilizado
    entre requisições — usado só para operações administrativas (ex: gravar tokens do mentor)."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    return _admin_client
