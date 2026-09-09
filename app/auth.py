"""Lógica OIDC contra OnMind-XID (facade Entra).

Flujo (cliente público + PKCE S256, sin client_secret):
  1. /login  -> genera state/nonce + code_verifier/challenge, guarda en sesión,
               redirige a {tenant}/oauth2/v2.0/authorize
  2. XID muestra form email -> OTP -> 302 redirect_uri?code=&state=
  3. /callback -> valida state, intercambia code+verifier en
                 {tenant}/oauth2/v2.0/token, pide userinfo, guarda tokens en sesión
"""
import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

from app import config


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def new_state() -> str:
    return _b64url(secrets.token_bytes(16))


def new_nonce() -> str:
    return _b64url(secrets.token_bytes(16))


def new_code_verifier() -> str:
    # RFC 7636: 43-128 chars de [A-Z a-z 0-9 - . _ ~]
    return _b64url(secrets.token_bytes(48))


def code_challenge_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return _b64url(digest)


def build_authorize_url(state: str, nonce: str, code_challenge: str) -> str:
    params = {
        "client_id": config.XID_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": config.REDIRECT_URI,
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{config.AUTHORIZE_URL}?{urlencode(params)}"


def build_logout_url(state: str = "") -> str:
    params = {"post_logout_redirect_uri": config.POST_LOGOUT_REDIRECT_URI}
    if state:
        params["state"] = state
    return f"{config.LOGOUT_URL}?{urlencode(params)}"


async def exchange_code(code: str, code_verifier: str) -> dict:
    """Intercambia authorization_code por access/id/refresh (lanza HTTPError si falla)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            config.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": config.XID_CLIENT_ID,
                "code": code,
                "redirect_uri": config.REDIRECT_URI,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            config.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": config.XID_CLIENT_ID,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            config.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


# --- helpers de sesión (servidor, cookie firmada via SessionMiddleware) ---


def save_login(session: dict, tokens: dict, userinfo: dict) -> dict:
    session["access_token"] = tokens.get("access_token")
    session["id_token"] = tokens.get("id_token")
    session["refresh_token"] = tokens.get("refresh_token")
    session["user"] = {
        "email": userinfo.get("email") or userinfo.get("preferred_username") or userinfo.get("sub"),
        "sub": userinfo.get("sub"),
        "name": userinfo.get("name"),
        "tid": userinfo.get("tid"),
    }
    session.pop("oauth_state", None)
    session.pop("oauth_nonce", None)
    session.pop("code_verifier", None)
    return session


def clear_login(session: dict) -> None:
    for key in ("access_token", "id_token", "refresh_token", "user",
                "oauth_state", "oauth_nonce", "code_verifier"):
        session.pop(key, None)


def is_authenticated(session: dict) -> bool:
    return bool(session.get("access_token") and session.get("user"))
