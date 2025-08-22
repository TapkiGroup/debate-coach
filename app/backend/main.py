# app/backend/main.py
import os
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import session, chat
from core.config import settings
from fastapi.routing import APIRoute

app = FastAPI(title="Debate Coach", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/api")
app.include_router(chat.router,    prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env_summary()}

@app.get("/healthz")
def healthz():
    return "ok"

@app.get("/api/health")
def api_health():
    return {"status": "ok"}

from fastapi.routing import APIRoute

@app.get("/api/_debug/routes")
def _list_routes():
    routes = []
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path.startswith("/api/"):
            routes.append({"path": r.path, "methods": list(r.methods)})
    return {"routes": routes}
