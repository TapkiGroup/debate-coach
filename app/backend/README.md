# Debate-Coach Backend (MVP)

FastAPI backend for **Debate-Coach**. Two modes supported:
- **Debate Coach** (`/api/v1/debate/actions`)
- **Pitch & Objection** (`/api/v1/pitch/actions`)

This MVP avoids source *reliability scoring*. Sources are only classified as `supports | challenges | neutral` with a one-line note.

## Quickstart
```bash
# Python 3.10+
cd app/backend
python -m venv .venv && source .venv/bin/activate
pip install -e .  # or: pip install -r requirements if you add one
pip install fastapi uvicorn httpx python-dotenv pydantic pytest

# Run
uvicorn src.main:create_app --reload --port 8000

# Test
pytest -q
```

## Environment
Create `.env` next to `pyproject.toml` (or use system env):
```
OPENAI_API_KEY=
TAVILY_API_KEY=
PORT=8000
```

## Endpoints
- `POST /api/v1/debate/actions`
- `POST /api/v1/pitch/actions`
- `GET /healthz`

