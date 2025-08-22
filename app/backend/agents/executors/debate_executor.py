from pathlib import Path
from typing import Dict, Any, List
from core.schemas import Event, Column, Fallacy, Score
from agents.tools.fallacies import detect_fallacies
from agents.tools.scoring import score_claim
from core.llm.main_client import chat as main_chat
from agents.tools.research import gather_sources, classify_sources
import json

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

    if intent == "research":
        sources = gather_sources(claim, max_results=8)
        classified = classify_sources(claim, sources) if sources else []
        chat_reply = "I've gathered relevant sources and summarized them."
        events.append(Event(column=Column.SOURCES, payload={
            "added": classified
        }))

    elif intent == "evaluate_argument":
        sys = "You provide critique and a strength score. JSON only."
        out = main_chat(system=sys, user=_EVAL_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        bullets = data.get("bullets", [])
        score_obj = data.get("score", {"value":0,"reasons":["fallback"]})

        # Format critique bullets
        critique_text = ""
        for b in bullets:
            critique_text += f"- {b}\n"

        # Format fallacies
        fallacies_text = ""
        if fallacies:
            fallacies_text = "DETECTED FALLACIES:\n"
            for f in fallacies:
                fallacies_text += f"{f['emoji']} {f['label']}: {f['why']}\n"

        # Score and evaluation summary
        score = Score(**score_obj)
        score_text = f"Score: {score.value}/100"
        evaluation_summary = ""
        if score_obj.get("reasons"):
            evaluation_summary = f"Short evaluation: {score_obj['reasons'][0]}"

        # Combine
        con_text = f"{score_text}\n{evaluation_summary}\n{critique_text}"
        if fallacies_text:
            con_text += "\n" + fallacies_text

        events.append(Event(column=Column.CON, payload=con_text.strip()))
        chat_reply = "I've provided a concise critique, score, and summary in the CON column."

    else:
        sys = "You produce ranked counter-arguments. JSON only."
        out = main_chat(system=sys, user=_OBJ_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        ranked = data.get("ranked", [])
        fallacies = [f.model_dump() for f in fallacies] if fallacies else []

        # Format counters
        counters_text = ""
        for c in ranked:
            if c.get("title"):
                counters_text += f"{c['title']}: {c['why']}\n"
            else:
                counters_text += f"{c['why']}\n"

        # Format fallacies
        fallacies_text = ""
        if fallacies:
            fallacies_text = "DETECTED FALLACIES:\n"
            for f in fallacies:
                fallacies_text += f"{f['emoji']} {f['label']}: {f['why']}\n"

        # Combine
        con_text = counters_text + (("\n" + fallacies_text) if fallacies_text else "")
        events.append(Event(column=Column.CON, payload=con_text.strip()))
        chat_reply = "I've added counter-arguments and fallacy analysis to the CON column."

    return {"chat_reply": chat_reply, "events": events, "score": score, "fallacies": fallacies}