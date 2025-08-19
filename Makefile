SHELL := /bin/bash

# Paths
BACKEND_DIR := app/backend
FRONTEND_DIR := app/frontend

.PHONY: help
help:
\t@echo "Targets:"
\t@echo "  make install-backend   - create venv and install backend deps"
\t@echo "  make run-backend       - run FastAPI on :8000"
\t@echo "  make test-backend      - run pytest"
\t@echo "  make dev-frontend      - run Next.js dev on :3000"
\t@echo "  make docker-up         - docker compose up --build"
\t@echo "  make docker-down       - docker compose down"

.PHONY: install-backend
install-backend:
\tcd $(BACKEND_DIR) && python -m venv .venv && source .venv/bin/activate && \\\n\tpip install -r requirements.txt || pip install fastapi uvicorn[standard] httpx python-dotenv pydantic pytest

.PHONY: run-backend
run-backend:
\tcd $(BACKEND_DIR) && source .venv/bin/activate && uvicorn src.main:create_app --reload --port 8000

.PHONY: test-backend
test-backend:
\tcd $(BACKEND_DIR) && source .venv/bin/activate && pytest -q

.PHONY: dev-frontend
dev-frontend:
\tcd $(FRONTEND_DIR) && npm i && NEXT_PUBLIC_API_BASE=$${NEXT_PUBLIC_API_BASE:-http://localhost:8000} npm run dev

.PHONY: docker-up
docker-up:
\tdocker compose up --build

.PHONY: docker-down
docker-down:
\tdocker compose down
