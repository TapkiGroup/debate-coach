import json
from pathlib import Path
from core.llm.cheap_client import chat as cheap_chat

_TRIAGE_PROMPT = Path("prompts/triage.txt").read_text(encoding="utf-8")

def classify_intent(mode: str, user_text: str) -> dict:
    sys = "You are TRIAGE. Reply JSON ONLY."
    user = f"""{_TRIAGE_PROMPT}

MODE: {mode}
USER:
{user_text}
"""
    out = cheap_chat(system=sys, user=user, temperature=0.0, max_tokens=300)
    try:
        data = json.loads(out)
        if isinstance(data, dict) and "intent" in data and "has_new_claim" in data:
            return data
    except Exception:
        pass
    return {"intent":"none","has_new_claim":False}
