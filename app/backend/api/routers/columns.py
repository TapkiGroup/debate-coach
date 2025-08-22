from fastapi import APIRouter, Query, HTTPException, Depends
from core.state import SessionStore, session_store
from core.schemas import Event, Column

router = APIRouter(tags=["columns"])

@router.get("/columns")
def get_columns(session_id: str = Query(...), store: SessionStore = Depends(lambda: session_store)):
    st = store.get(session_id)
    if not st:
        raise HTTPException(status_code=404, detail="Session not found")
    columns = {"PRO": [], "CON": [], "SOURCES": []}
    for ev in st.events:
        if ev.column in columns:
            columns[ev.column].append(ev)
    
    return columns 