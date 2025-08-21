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

@app.post("/api/session/start")
def _fallback_start_session():
    return {"session_id": str(uuid.uuid4())}

@app.get("/api/_debug/routes")
def _list_routes():
    return {"paths": [r.path for r in app.routes if isinstance(r, APIRoute)]}

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env_summary()}
