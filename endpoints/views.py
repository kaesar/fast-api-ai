"""Endpoints de vistas + salud (sin autenticación)."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import llm_client

router = APIRouter(tags=["views"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "chat.html")


@router.get("/health")
def health():
    return {"ok": True, **llm_client.provider_info()}
