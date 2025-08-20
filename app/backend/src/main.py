from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, debate, pitch

def create_app() -> FastAPI:
    app = FastAPI(title="Debate Coach API", version="0.1.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://<your-vercel>.vercel.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(debate.router, prefix="/api/v1/debate", tags=["debate"])
    app.include_router(pitch.router,  prefix="/api/v1/pitch",  tags=["pitch"])

    @app.get("/", include_in_schema=False)
    def root():
        return {"ok": True}

    return app
