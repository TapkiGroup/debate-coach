from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

# FILE: app/backend/src/routers/debate.py
from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse, ColumnUpdate, ProConItem
from ..services.procon_mapper import strengthen_and_map
from ..services.research.research_pipeline import run_research
from datetime import datetime

router = APIRouter()

@router.post("/actions", response_model=ChatResponse)
async def debate_actions(payload: ChatRequest):
    if payload.mode.name != "debate_coach":
        raise HTTPException(status_code=400, detail="Wrong mode for this endpoint")

    chat_parts: list[str] = []
    updates: list[ColumnUpdate] = []

    title, pro_items, con_items = strengthen_and_map(payload.message)

    if "evaluate_argument" in [a.value for a in payload.actions]:
        chat_parts.append(
            f"Strengthened your claim: '{title}'. Highlighted weaknesses and potential fallacies."
        )
        updates.append(ColumnUpdate(column="PRO", items=pro_items, timestamp=datetime.utcnow()))
        updates.append(ColumnUpdate(column="CON", items=con_items, timestamp=datetime.utcnow()))

    if "generate_counters" in [a.value for a in payload.actions]:
        # Naive: reuse con_items as counters; real app would expand via GPT-5
        chat_parts.append("Generated top counter-arguments.")
        updates.append(ColumnUpdate(column="CON", items=con_items, timestamp=datetime.utcnow()))

    if "research" in [a.value for a in payload.actions]:
        sources = await run_research(payload.message)
        chat_parts.append("Added concise sources related to your claim.")
        updates.append(ColumnUpdate(column="SOURCES", items=sources, timestamp=datetime.utcnow()))

    if not updates:
        chat_parts.append("No actions selected; nothing to update.")

    return ChatResponse(chat_text="\n".join(chat_parts), updates=updates)