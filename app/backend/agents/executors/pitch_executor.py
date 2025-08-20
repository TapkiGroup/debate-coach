import json
from pathlib import Path
from typing import Dict, Any, List
from core.schemas import Event, Column, Fallacy, Score
from agents.tools.fallacies import detect_fallacies
from agents.tools.scoring import score_claim
from agents.tools.research import gather_sources, classify_sources
from core.llm.main_client import chat as main_chat

_EVAL_PROMPT = Path("prompts/evaluation.txt").read_text(encoding="utf-8")
_OBJ_PROMPT  = Path("prompts/objections.txt").read_text(encoding="utf-8")

def _json_load(s: str) -> dict | list:
    try:
        return json.loads(s)
    except Exception:
        return {}

def do_fallacy_check_if_needed(text: str, need: bool) -> List[Fallacy]:
    return [Fallacy(**f) for f in detect_fallacies(text)] if need else []

def execute(intent: str, pitch_text: str, need_fallacy: bool, do_research: bool = False) -> Dict[str, Any]:
    fallacies = do_fallacy_check_if_needed(pitch_text, need_fallacy)

    events: List[Event] = []
    chat_reply = ""
    score: Score | None = None

    if intent == "objections":
        sys = "You generate top objections (ranked). JSON only."
        out = main_chat(system=sys, user=_OBJ_PROMPT + f"\n\nPITCH:\n{pitch_text}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        ranked = data.get("ranked", [])
        events.append(Event(column=Column.CON, payload={
            "objections_ranked": ranked,
            "fallacies": [f.model_dump() for f in fallacies] if fallacies else []
        }))
        sc = score_claim(pitch_text, context_hint="Objections were generated.")
        score = Score(**sc["score"]) if "score" in sc else None
        chat_reply = "Here are top objections. I've updated the CON column."

    elif intent == "ruthless_impression":
        out = main_chat(system="You critique a pitch harshly. JSON only.",
                        user=_EVAL_PROMPT + f"\n\nPITCH:\n{pitch_text}",
                        temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        bullets = data.get("bullets", [])
        score_obj = data.get("score", {"value":50,"reasons":["fallback"]})
        events.append(Event(column=Column.CON, payload={
            "critique": bullets,
            "fallacies": [f.model_dump() for f in fallacies] if fallacies else []
        }))
        score = Score(**score_obj)
        chat_reply = "Brutal first impression added to CON with a score."

    elif intent == "research":
        sources = gather_sources(pitch_text, max_results=8)
        classified = classify_sources(pitch_text, sources) if sources else []
        # In SOURCES column we add events referencing new sids at API layer (state handles storage)
        chat_reply = "I've gathered neutral market/analogs/competitor sources and summarized them."
        events.append(Event(column=Column.SOURCES, payload={
            "added": classified
        }))

    else:
        chat_reply = "Unsupported intent for pitch executor."
    return {"chat_reply": chat_reply, "events": events, "score": score, "fallacies": fallacies}
