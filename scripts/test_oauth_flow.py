"""Smoke test end-to-end (sin navegador): XID discovery + JWKS + authorize + Ollama + FastAPI.

Uso:
  python scripts/test_oauth_flow.py [--app-url http://localhost:8000]

No completa el OTP (requiere email), pero verifica que todo está reachable
antes de probar el login en navegador.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import httpx

from app import config


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-url", default=config.APP_BASE_URL)
    args = parser.parse_args()

    all_ok = True

    # 1. XID discovery
    try:
        r = httpx.get(config.DISCOVERY_URL, timeout=10)
        doc = r.json()
        all_ok &= check("xid-discovery", r.status_code == 200, f"-> {config.DISCOVERY_URL}")
        assert doc["authorization_endpoint"] == config.AUTHORIZE_URL
        assert doc["token_endpoint"] == config.TOKEN_URL
    except Exception as e:
        all_ok &= check("xid-discovery", False, str(e))

    # 2. JWKS
    try:
        r = httpx.get(config.JWKS_URL, timeout=10)
        keys = r.json().get("keys", [])
        all_ok &= check("xid-jwks", r.status_code == 200 and len(keys) > 0, f"keys={len(keys)}")
    except Exception as e:
        all_ok &= check("xid-jwks", False, str(e))

    # 3. authorize rechaza sin client_id (prueba que el endpoint vive)
    try:
        r = httpx.get(config.AUTHORIZE_URL, params={"client_id": "", "redirect_uri": config.REDIRECT_URI}, timeout=10)
        all_ok &= check("xid-authorize-vivo", r.status_code == 400, f"status={r.status_code}")
    except Exception as e:
        all_ok &= check("xid-authorize-vivo", False, str(e))

    # 4. Ollama (solo si provider=ollama)
    if config.LLM_PROVIDER == "ollama":
        try:
            # /v1 es el endpoint OpenAI-compat; /api/tags es nativo Ollama
            native = config.LLM_BASE_URL.replace("/v1", "/api/tags")
            r = httpx.get(native, timeout=10)
            models = [m.get("name") for m in r.json().get("models", [])]
            has = any(config.LLM_MODEL.split(":")[0] in (m or "") for m in models)
            all_ok &= check("ollama-modelo", has, f"{config.LLM_MODEL} en {models[:5]}")
        except Exception as e:
            all_ok &= check("ollama-modelo", False, str(e))
    else:
        all_ok &= check("openai-key", bool(config.LLM_API_KEY), "OPENAI_API_KEY definida" if config.LLM_API_KEY else "falta OPENAI_API_KEY")

    # 5. App FastAPI
    try:
        r = httpx.get(f"{args.app_url}/health", timeout=10)
        all_ok &= check("app-health", r.status_code == 200, r.text[:120])
    except Exception as e:
        all_ok &= check("app-health", False, f"¿arrancó uvicorn? {e}")

    print("\nSiguiente paso manual: abre /login, entra con bob@example.com:abc123 (dev key, sin Mailpit).")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
