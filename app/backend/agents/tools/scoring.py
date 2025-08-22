import json
from pathlib import Path
from core.llm.main_client import chat as main_chat

_EVAL_PROMPT = Path("prompts/evaluation.txt").read_text(encoding="utf-8")

def score_claim(claim: str, context_hint: str = "") -> dict:
    sys = "Evaluate strength concisely. Return JSON with bullets + score."
    user = f"{_EVAL_PROMPT}\n\nCLAIM:\n{claim}\n\nCONTEXT:\n{context_hint}"
    out = main_chat(system=sys, user=user, temperature=0.2, max_tokens=800)
    try:
        data = json.loads(out)
        sc = data.get("score") or {}
        bullets = data.get("bullets") or []
        # Validate score value
        value = sc.get("value", 50)
        if not isinstance(value, int) or not (0 <= value <= 100):
            value = 50
        reasons = sc.get("reasons", ["fallback"])
        return {"bullets": bullets, "score": {"value": value, "reasons": reasons}}
    except Exception:
        return {"bullets": [], "score": {"value": 50, "reasons": ["fallback"]}}
