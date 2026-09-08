import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {name}")
    return value


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8550/oauth2callback")

PORT = int(os.getenv("PORT", "8550"))

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _fingerprint(nome: str, valor: str) -> str:
    if not valor:
        return f"{nome}: VAZIO"
    return f"{nome}: len={len(valor)} inicio={valor[:12]!r} fim={valor[-12:]!r}"


print("[config] " + _fingerprint("SUPABASE_URL", SUPABASE_URL), flush=True)
print("[config] " + _fingerprint("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY), flush=True)
print("[config] " + _fingerprint("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY), flush=True)
