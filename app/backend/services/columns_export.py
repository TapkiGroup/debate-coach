from core.state import SessionStore
from core.schemas import ColumnsSnapshot

def export_snapshot(store: SessionStore, session_id: str) -> ColumnsSnapshot:
    return store.export_columns(session_id)
