"""Endpoints OAuth contra OnMind-XID (facade Entra)."""
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app import auth as auth_logic
from app import llm_client

router = APIRouter(tags=["auth"])


@router.get("/login")
def login(request: Request):
    state = auth_logic.new_state()
    nonce = auth_logic.new_nonce()
    verifier = auth_logic.new_code_verifier()
    challenge = auth_logic.code_challenge_s256(verifier)
    request.session["oauth_state"] = state
    request.session["oauth_nonce"] = nonce
    request.session["code_verifier"] = verifier
    return RedirectResponse(
        auth_logic.build_authorize_url(state, nonce, challenge), status_code=302
    )


@router.get("/auth/callback")
async def auth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return JSONResponse({"error": error, "detail": dict(request.query_params)}, status_code=400)
    expected = request.session.get("oauth_state")
    verifier = request.session.get("code_verifier")
    if not expected or state != expected:
        return JSONResponse({"error": "invalid_state"}, status_code=400)
    if not code or not verifier:
        return JSONResponse({"error": "missing_code_or_verifier"}, status_code=400)
    try:
        tokens = await auth_logic.exchange_code(code, verifier)
        userinfo = await auth_logic.fetch_userinfo(tokens["access_token"])
    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            {"error": "token_exchange_failed", "detail": exc.response.text[:500]},
            status_code=502,
        )
    auth_logic.save_login(request.session, tokens, userinfo)
    return RedirectResponse("/", status_code=302)


@router.get("/me")
def me(request: Request):
    return {
        "authenticated": auth_logic.is_authenticated(request.session),
        "user": request.session.get("user"),
        "llm": llm_client.provider_info(),
    }


@router.get("/logout")
def logout(request: Request):
    auth_logic.clear_login(request.session)
    return RedirectResponse(auth_logic.build_logout_url(), status_code=302)
