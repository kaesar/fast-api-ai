"""Agregador de routers (mismo esquema original: router.py agrega endpoints)."""
from fastapi import APIRouter

from endpoints import auth, chat, views

router = APIRouter()
router.include_router(views.router)
router.include_router(auth.router)
router.include_router(chat.router)
