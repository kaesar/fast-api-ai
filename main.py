"""Entrypoint FastAPI — ejercicio OAuth/OnMind-XID + LLM.

Las rutas viven en `endpoints/` y se agregan en `router.py`
(mismo esquema router + endpoints del proyecto original).
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import config
from router import router

app = FastAPI(title="AI OAuth + LLM ejercicio")
app.add_middleware(SessionMiddleware, secret_key=config.APP_SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")  # OnMind-CUI
app.include_router(router)
