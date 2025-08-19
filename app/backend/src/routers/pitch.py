from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse, ColumnUpdate, ProConItem
from ..services.procon_mapper import strengthen_and_map
from ..services.research.research_pipeline import run_research
from datetime import datetime

router = APIRouter()

@router.post("/actions", response_model=ChatResponse)
async def pitch_actions(payload: ChatRequest):
    if payload.mode.name != "pitch_objection":
        raise HTTPException(status_code=400, detail="Wrong mode for this endpoint")

    chat_parts: list[str] = []
    updates: list[ColumnUpdate] = []

    # Reuse strengthen for concise PRO baseline (value props); naive for MVP
    title, pro_items, con_items = strengthen_and_map(payload.message)

    action_names = [a.value for a in payload.actions]

    if "first_impression" in action_names:
        chat_parts.append(
            "Brutal first impression: your message needs sharper differentiation, clearer target segment, and risk mitigation."
        )
        updates.append(ColumnUpdate(column="CON", items=con_items, timestamp=datetime.utcnow()))

    if "objections" in action_names:
        chat_parts.append("Listed top objections with draft rebuttal directions.")
        updates.append(ColumnUpdate(column="CON", items=con_items, timestamp=datetime.utcnow()))
        # Optionally add a refined PRO item suggesting a rebuttal outline
        rebuttal = ProConItem(id="PRO_rebuttal", title="Rebuttal outline", body="Segment focus, ROI calc, data/privacy plan.")
        updates.append(ColumnUpdate(column="PRO", items=[rebuttal], timestamp=datetime.utcnow()))

    if "reality_check" in action_names:
        sources = await run_research(payload.message)
        chat_parts.append("Added quick sources for a reality check (supports/challenges/neutral).")
        updates.append(ColumnUpdate(column="SOURCES", items=sources, timestamp=datetime.utcnow()))
        updates.append(ColumnUpdate(column="PRO", items=pro_items, timestamp=datetime.utcnow()))

    if not updates:
        chat_parts.append("No actions selected; nothing to update.")

    return ChatResponse(chat_text="\n".join(chat_parts), updates=updates)