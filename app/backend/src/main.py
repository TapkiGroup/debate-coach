from fastapi import FastAPI
from .routers import debate, pitch, health
from .core.settings import settings
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="Debate-Coach Backend", version="0.1.0")

    origins = ["http://localhost:3000", "https://<your-vercel>.vercel.app"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins, 
        allow_credentials=True,
        allow_methods=["*"], 
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"]) 
    app.include_router(debate.router, prefix="/api/v1/debate", tags=["debate"]) 
    app.include_router(pitch.router, prefix="/api/v1/pitch", tags=["pitch"]) 

    return app


app = create_app()