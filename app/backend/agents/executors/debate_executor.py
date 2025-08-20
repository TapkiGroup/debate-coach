import json
from pathlib import Path
from typing import Dict, Any, List
from core.schemas import Event, Column, Fallacy, Score
from agents.tools.fallacies import detect_fallacies
from agents.tools.scoring import score_claim
from core.llm.main_client import chat as main_chat

_EVAL_PROMPT = Path("prompts/evaluation.txt").read_text(encoding="utf-8")
_OBJ_PROMPT  = Path("prompts/objections.txt").read_text(encoding="utf-8")

def _json_load(s: str) -> dict | list:
    try:
        return json.loads(s)
    except Exception:
        return {}

def do_fallacy_check_if_needed(claim: str, need: bool) -> List[Fallacy]:
    return [Fallacy(**f) for f in detect_fallacies(claim)] if need else []

def execute(intent: str, claim: str, need_fallacy: bool) -> Dict[str, Any]:
    fallacies = do_fallacy_check_if_needed(claim, need_fallacy)

    events: List[Event] = []
    chat_reply = ""
    score: Score | None = None

    if intent == "give_objections":
        sys = "You produce ranked counter-arguments. JSON only."
        out = main_chat(system=sys, user=_OBJ_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        ranked = data.get("ranked", [])
        events.append(Event(column=Column.CON, payload={
            "counters_ranked": ranked,
            "fallacies": [f.model_dump() for f in fallacies] if fallacies else []
        }))
        # Score after counters
        sc = score_claim(claim, context_hint="Counter-arguments were generated.")
        score = Score(**sc["score"]) if "score" in sc else None
        chat_reply = "Here are the strongest counter-arguments. I've also updated the CON column. What's your next move?"

    elif intent == "evaluate_argument":
        sys = "You provide critique and a strength score. JSON only."
        out = main_chat(system=sys, user=_EVAL_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        bullets = data.get("bullets", [])
        score_obj = data.get("score", {"value":50,"reasons":["fallback"]})
        events.append(Event(column=Column.CON, payload={
            "critique": bullets,
            "fallacies": [f.model_dump() for f in fallacies] if fallacies else []
        }))
        score = Score(**score_obj)
        chat_reply = "I've provided a concise critique and updated the CON column with key points."

    else:
        chat_reply = "Unsupported intent for debate executor."
    return {"chat_reply": chat_reply, "events": events, "score": score, "fallacies": fallacies}
