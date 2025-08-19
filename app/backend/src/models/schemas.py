from __future__ import annotations
from pydantic import BaseModel, HttpUrl
from enum import Enum
from typing import Literal, Union
from datetime import datetime


class Mode(str, Enum):
    debate_coach = "debate_coach"
    pitch_objection = "pitch_objection"


class Action(str, Enum):
    # Debate actions
    evaluate_argument = "evaluate_argument"
    generate_counters = "generate_counters"
    research = "research"
    # Pitch actions
    first_impression = "first_impression"
    objections = "objections"
    reality_check = "reality_check"


class FallacyItem(BaseModel):
    name: str
    explanation: str


class ProConItem(BaseModel):
    id: str
    title: str
    body: str
    fallacies: list[FallacyItem] = []


class SourceRelation(str, Enum):
    supports = "supports"
    challenges = "challenges"
    neutral = "neutral"


class SourceItem(BaseModel):
    id: str
    title: str
    url: HttpUrl
    note: str
    relation: SourceRelation


class ColumnUpdate(BaseModel):
    column: Literal["PRO", "CON", "SOURCES"]
    items: list[Union[ProConItem, SourceItem]]
    timestamp: datetime


class ChatRequest(BaseModel):
    session_id: str
    mode: Mode
    actions: list[Action]
    message: str


class ChatResponse(BaseModel):
    chat_text: str
    updates: list[ColumnUpdate]