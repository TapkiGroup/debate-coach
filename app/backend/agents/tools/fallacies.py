import json
from pathlib import Path
from core.llm.cheap_client import chat as cheap_chat

_PROMPT = Path("prompts/fallacies.txt").read_text(encoding="utf-8")

def detect_fallacies(text: str) -> list[dict]:
    sys = "You detect fallacies. Reply JSON ONLY as a list."
    out = cheap_chat(system=sys, user=_PROMPT + "\n\nTEXT:\n" + text, temperature=0.0, max_tokens=400)
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
