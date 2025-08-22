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
        sys = "You produce ranked counter-arguments. JSON only."
        out = main_chat(system=sys, user=_OBJ_PROMPT + f"\n\nCLAIM:\n{pitch_text}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        ranked = data.get("ranked", [])

        # Format counters
        counters_text = ""
        for c in ranked:
            if c.get("title"):
                counters_text += f"{c['title']}: {c['why']}\n"
            else:
                counters_text += f"{c['why']}\n"

        # Format fallacies
        fallacies_text = ""
        
        # Combine
        con_text = counters_text + (("\n" + fallacies_text) if fallacies_text else "")
        events.append(Event(column=Column.CON, payload=con_text.strip()))
        chat_reply = "I've added objections and fallacy analysis to the CON column."

    elif intent == "ruthless_impression":
        out = main_chat(system="You critique a pitch harshly. JSON only.",
                        user=_EVAL_PROMPT + f"\n\nPITCH:\n{pitch_text}",
                        temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        bullets = data.get("bullets", [])
        score_obj = data.get("score", {"value":50,"reasons":["fallback"]})

        # Format critique bullets
        critique_text = ""
        for b in bullets:
            critique_text += f"- {b}\n"

        # Format fallacies
        fallacies_text = ""
        
        # Score and evaluation summary
        score = Score(**score_obj)
        score_text = f"Score: {score.value}/100"
        evaluation_summary = ""
        if score_obj.get("reasons"):
            evaluation_summary = f"Short evaluation: {score_obj['reasons'][0]}"

        # Combine
        con_text = f"{evaluation_summary}\n{critique_text}"
        if fallacies_text:
            con_text += "\n" + fallacies_text

        events.append(Event(column=Column.CON, payload=con_text.strip()))
        chat_reply = "Brutal first impression added to CON with a score."

    elif intent == "research":
        sources = gather_sources(pitch_text, max_results=8)
        classified = classify_sources(pitch_text, sources) if sources else []
        chat_reply = "I've gathered neutral market/analogs/competitor sources and summarized them."
        events.append(Event(column=Column.SOURCES, payload={
            "added": classified
        }))

    else:
        chat_reply = "Unsupported intent for pitch executor."
    
    return {"chat_reply": chat_reply, "events": events, "score": score, "fallacies": fallacies}