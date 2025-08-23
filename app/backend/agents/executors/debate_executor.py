from pathlib import Path
from typing import Dict, Any, List
from core.schemas import Event, Column, Fallacy, Score
from agents.tools.fallacies import detect_fallacies
from agents.tools.scoring import score_claim   # <-- use as backup scorer
from core.llm.main_client import chat as main_chat
from agents.tools.research import gather_sources, classify_sources
from core.utils.utils import format_bullets, format_ranked, format_fallacies, json_load_safe as _json_load

_EVAL_PROMPT = Path("prompts/evaluation.txt").read_text(encoding="utf-8")
_OBJ_PROMPT  = Path("prompts/objections.txt").read_text(encoding="utf-8")

def do_fallacy_check_if_needed(claim: str, need: bool) -> List[Fallacy]:
    return [Fallacy(**f) for f in detect_fallacies(claim)] if need else []

def _coerce_eval_data(raw_out: str, claim: str) -> tuple[list, dict]:
    """Parse model JSON; on failure retry outside; here just best-effort coerce."""
    data = _json_load(raw_out) or {}
    bullets = data.get("bullets") if isinstance(data, dict) else None
    score_obj = data.get("score") if isinstance(data, dict) else None

    if not isinstance(bullets, list):
        # heuristic: extract dashed lines
        bullets = [ln.strip()[1:].strip()
                   for ln in (raw_out or "").splitlines()
                   if ln.strip().startswith("- ")]
        if not bullets:
            bullets = ["No structured critique returned; using fallback."]
    if not (isinstance(score_obj, dict) and "value" in score_obj):
        # robust backup
        try:
            s = score_claim(claim)  # expected to return {"value": int, "reasons": [str,...]}
            score_obj = s if isinstance(s, dict) else {"value": 0, "reasons": ["backup"]}
        except Exception:
            score_obj = {"value": 0, "reasons": ["backup"]}
    # ensure reasons list
    if not isinstance(score_obj.get("reasons"), list):
        score_obj["reasons"] = [str(score_obj.get("reasons", "backup"))]
    return bullets, score_obj

def execute(intent: str, claim: str, need_fallacy: bool) -> Dict[str, Any]:
    fallacies_models = do_fallacy_check_if_needed(claim, need_fallacy)

    events: List[Event] = []
    chat_reply = ""
    score: Score | None = None

    if intent == "research":
        sources = gather_sources(claim, max_results=8)
        classified = classify_sources(claim, sources) if sources else []
        chat_reply = "I've gathered relevant sources and summarized them."
        events.append(Event(column=Column.SOURCES, payload={"added": classified}))

    elif intent == "evaluate_argument":
        sys = "You provide critique and a strength score. JSON only. Respond as JSON: {\"bullets\": [\"...\"], \"score\": {\"value\": 0-100, \"reasons\": [\"...\"]}}"
        out = main_chat(system=sys, user=_EVAL_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.2, max_tokens=900)
        data = _json_load(out)

        # retry once if bad JSON
        if not (isinstance(data, dict) and "score" in data and "bullets" in data):
            out_retry = main_chat(system=sys, user=_EVAL_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.0, max_tokens=900)
            bullets, score_obj = _coerce_eval_data(out_retry or out, claim)
        else:
            bullets = data.get("bullets") or []
            score_obj = data.get("score") or {"value": 0, "reasons": ["backup"]}

        critique_text  = format_bullets(bullets)
        fallacies_text = format_fallacies(fallacies_models)

        score  = Score(**score_obj)
        reason = (score.reasons[0] if getattr(score, "reasons", None) else "").strip()
        score_line = f"{score.value}/100" + (f". {reason}" if reason else "")

        parts = [score_line]
        if critique_text:
            parts.append(critique_text.strip())
        if fallacies_text:
            parts.append(fallacies_text.strip())

        con_text = "\n".join(parts).strip()
        events.append(Event(column=Column.CON, payload=con_text))
        chat_reply = "I've provided a concise critique in the CON column."

    else:  # give_objections
        sys = "You produce ranked counter-arguments. JSON only. Respond as JSON: {\"ranked\": [{\"title\": \"...\", \"why\": \"...\"}, ...]}"
        out = main_chat(system=sys, user=_OBJ_PROMPT + f"\n\nCLAIM:\n{claim}", temperature=0.3, max_tokens=900)
        data = _json_load(out) or {}
        ranked = data.get("ranked", []) or []

        counters_text  = format_ranked(ranked).strip()
        fallacies_text = format_fallacies(fallacies_models)

        con_text = counters_text or "- No counter-arguments were generated."
        if fallacies_text:
            con_text += ("\n" if con_text else "") + fallacies_text

        events.append(Event(column=Column.CON, payload=con_text))
        chat_reply = "I've added counter-arguments and fallacy analysis to the CON column."

    return {
        "chat_reply": chat_reply,
        "events": events,
        "score": score,
        "fallacies": [f.model_dump() for f in fallacies_models] if fallacies_models else []
    }
