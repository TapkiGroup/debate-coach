from fastapi import APIRouter, HTTPException, Depends
from core.schemas import ChatIn, ChatOut
from services.chat_loop import run_chat_turn
from core.state import SessionStore, session_store

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn, store: SessionStore = Depends(lambda: session_store)):
    try:
        out = run_chat_turn(payload, store)
        return out
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        # For hackathon we return safe error; logs contain stacktrace
        return ChatOut(chat_reply=f"""Something went wrong: {type(e).__name__}: {e}""", events=[])
