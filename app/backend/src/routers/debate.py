from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse

from app.agents.supervisor_agent import SupervisorAgent, SupervisorConfig
from ..services.llm_provider import LLMProvider
from ..services.research_provider import ResearchProvider

router = APIRouter()

_llm = LLMProvider()
_research = ResearchProvider()
_sup = SupervisorAgent(_llm, _research, SupervisorConfig())

@router.post("/actions", response_model=ChatResponse)
async def debate_actions(payload: ChatRequest):
    if payload.mode.name != "debate_coach":
        raise HTTPException(status_code=400, detail="Wrong mode for this endpoint")
    out = _sup.process_turn(
        session_id=payload.session_id,
        mode=payload.mode.value,
        message=payload.message,
        explicit_actions=[a.value for a in payload.actions],
    )
    return ChatResponse(chat_text=out.chat_text, updates=out.updates)

