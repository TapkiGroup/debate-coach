from typing import Dict, List
import uuid
from core.schemas import SessionState, Mode, Event, Column, Source, ColumnsSnapshot

class SessionStore:
    def __init__(self):
        self._by_id: Dict[str, SessionState] = {}

    def create(self, mode: Mode) -> str:
        sid = uuid.uuid4().hex
        self._by_id[sid] = SessionState(mode=mode)
        return sid

    def get(self, sid: str) -> SessionState:
        return self._by_id[sid]

    def append_event(self, sid: str, ev: Event):
        st = self._by_id[sid]
        if ev.column == Column.PRO:
            st.pro.append(ev)
        elif ev.column == Column.CON:
            st.con.append(ev)
        elif ev.column == Column.SOURCES:
            # We keep sources as structured list via add_sources().
            # SOURCE events (meta like added_sids) are still useful for the UI log,
            # but they are NOT appended into CON (bug fix). We simply ignore here.
            return

    def add_sources(self, sid: str, sources: List[Source]) -> List[str]:
        st = self._by_id[sid]
        st.sources.extend(sources)
        return [s.sid for s in sources]

    def export_columns(self, sid: str) -> ColumnsSnapshot:
        st = self._by_id[sid]
        return ColumnsSnapshot(PRO=st.pro, CON=st.con, SOURCES=st.sources)


session_store = SessionStore()