"""Endpoint de chat LLM (protegido, solo autenticados)."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import auth as auth_logic
from app import llm_client

router = APIRouter(tags=["chat"])


class ChatIn(BaseModel):
    prompt: str


@router.post("/chat")
async def chat(request: Request, body: ChatIn):
    if not auth_logic.is_authenticated(request.session):
        return JSONResponse({"detail": "No autenticado. Haz login en /login."}, status_code=401)
    prompt = body.prompt.strip()
    if not prompt:
        return JSONResponse({"detail": "prompt vacío"}, status_code=400)
    if len(prompt) > 4000:
        return JSONResponse({"detail": "prompt demasiado largo (máx 4000)"}, status_code=400)
    history = request.session.get("chat_history", [])
    try:
        reply = await llm_client.chat_completion(prompt, history)
    except Exception as exc:  # p.ej. Ollama caído o key inválida
        return JSONResponse({"detail": f"LLM error: {exc}"}, status_code=502)
    history = (history + [{"role": "user", "content": prompt}, {"role": "assistant", "content": reply}])[-20:]
    request.session["chat_history"] = history
    return {"reply": reply, "user": request.session.get("user"), "llm": llm_client.provider_info()}
