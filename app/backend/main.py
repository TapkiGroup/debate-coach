import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import session, chat
from core.config import settings

app = FastAPI(title="Debate Coach Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env_summary()}
