"""Entrypoint FastAPI — ejercicio OAuth/XID + LLM.

Las rutas viven en `endpoints/` y se agregan en `router.py`
(mismo esquema router + endpoints del proyecto original).
"""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app import config
from router import router

app = FastAPI(title="AI OAuth + LLM ejercicio")
app.add_middleware(SessionMiddleware, secret_key=config.APP_SECRET_KEY)
app.include_router(router)
