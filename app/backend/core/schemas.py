from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

class Mode(str, Enum):
    debate_counter = "debate_counter"
    pitch_objections = "pitch_objections"

class Intent(str, Enum):
    evaluate_argument = "evaluate_argument"
    give_objections   = "give_objections"
    research          = "research"
    none              = "none"

class Column(str, Enum):
    PRO = "PRO"
    CON = "CON"
    SOURCES = "SOURCES"

class EvidenceTag(str, Enum):
    corroborated = "corroborated"
    refuted      = "refuted"
    disputed     = "disputed"
    unverifiable = "unverifiable"

class SourceReliability(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Source(BaseModel):
    sid: str = Field(default_factory=lambda: f"S{uuid.uuid4().hex[:8]}")
    title: str
    url: str
    note: Optional[str] = None
    reliability: SourceReliability = SourceReliability.medium
    tag: Optional[EvidenceTag] = None

class Fallacy(BaseModel):
    code: str
    label: str
    emoji: str
    why: str

class Score(BaseModel):
    value: int
    reasons: List[str]

class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    ts: datetime = Field(default_factory=datetime.utcnow)
    column: Column
    payload:  Union[Dict[str, Any], str]

class SessionState(BaseModel):
    mode: Mode
    pro: List[Event] = Field(default_factory=list)
    con: List[Event] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    fallacies_seen: List[Fallacy] = Field(default_factory=list)
    last_user_claim_raw: Optional[str] = None
    last_intent: Optional[Intent] = None
    last_plan: Optional[List[str]] = None
    did_fallacy_on_this_claim: bool = False
    has_new_claim_this_turn: bool = False

class CreateSessionOut(BaseModel):
    session_id: str

class ChatIn(BaseModel):
    session_id: str
    user_text: str

class ChatOut(BaseModel):
    chat_reply: str
    events: List[Event]
    score: Optional[Score] = None
    fallacies: Optional[List[Fallacy]] = None

class ColumnsSnapshot(BaseModel):
    PRO: List[Event]
    CON: List[Event]
    SOURCES: List[Source]
