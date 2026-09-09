"""Config centralizada del ejercicio.

Variables de entorno (ver .env.example):

App:
  APP_BASE_URL, APP_SECRET_KEY, APP_HOST, APP_PORT

XID (facade Entra, ver ../xid/README.md "Entra ID facade"):
  XID_BASE_URL      -> p.ej. http://localhost:8787 (bun run dev en ../xid)
  XID_TENANT_ID     -> tid configurado en XID (default "xid")
  XID_CLIENT_ID     -> cliente público, sin secret (interactivo = public client)
  XID_REDIRECT_ALLOWLIST -> documentativo aquí; se configura en el lado XID
                           en prod. En dev (XID_ENV=dev) XID lo deja abierto.

LLM (Ollama por defecto, endpoint compatible OpenAI):
  LLM_PROVIDER=ollama|openai
  OLLAMA_BASE_URL/OLLAMA_MODEL/OLLAMA_API_KEY
  OPENAI_API_KEY/OPENAI_MODEL/OPENAI_BASE_URL
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- App ---
APP_BASE_URL = _env("APP_BASE_URL", "http://localhost:8000").rstrip("/")
APP_SECRET_KEY = _env("APP_SECRET_KEY", "dev-secret-key-cambiar-en-prod-32ch")
APP_HOST = _env("APP_HOST", "127.0.0.1")
APP_PORT = int(_env("APP_PORT", "8000") or "8000")

# --- XID / Entra facade ---
XID_BASE_URL = _env("XID_BASE_URL", "http://localhost:8787").rstrip("/")
XID_TENANT_ID = _env("XID_TENANT_ID", "xid")
XID_CLIENT_ID = _env("XID_CLIENT_ID", "ai-ejercicio")

# redirect_uri de esta app
REDIRECT_URI = f"{APP_BASE_URL}/auth/callback"
POST_LOGOUT_REDIRECT_URI = f"{APP_BASE_URL}/"

# URLs derivadas del facade Entra (no hardcodear tenant a mano)
DISCOVERY_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/v2.0/.well-known/openid-configuration"
AUTHORIZE_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/oauth2/v2.0/token"
JWKS_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/discovery/v2.0/keys"
USERINFO_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/openid/userinfo"
LOGOUT_URL = f"{XID_BASE_URL}/{XID_TENANT_ID}/oauth2/v2.0/logout"

# --- LLM ---
LLM_PROVIDER = _env("LLM_PROVIDER", "ollama").lower() or "ollama"

OPENAI_API_KEY = _env("OPENAI_API_KEY", "")
OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "gemma4:e4b-mlx")
OLLAMA_API_KEY = _env("OLLAMA_API_KEY", "ollama")

if LLM_PROVIDER == "openai":
    LLM_MODEL = OPENAI_MODEL
    LLM_BASE_URL = OPENAI_BASE_URL
    LLM_API_KEY = OPENAI_API_KEY
else:
    LLM_MODEL = OLLAMA_MODEL
    LLM_BASE_URL = OLLAMA_BASE_URL
    LLM_API_KEY = OLLAMA_API_KEY
