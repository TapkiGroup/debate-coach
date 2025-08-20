from fastapi import APIRouter, HTTPException, Depends, Query
from core.schemas import Mode, ColumnsSnapshot, CreateSessionOut
from core.state import SessionStore, session_store

router = APIRouter(tags=["session"])

@router.post("/session", response_model=CreateSessionOut)
def create_session(mode: Mode, store: SessionStore = Depends(lambda: session_store)):
    sid = store.create(mode=mode)
    return {"session_id": sid}

@router.get("/columns", response_model=ColumnsSnapshot)
def get_columns(session_id: str = Query(...), store: SessionStore = Depends(lambda: session_store)):
    try:
        st = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    return store.export_columns(session_id)
