import json
from core.llm.cheap_client import chat as cheap_chat
from pathlib import Path

_PROMPT = Path("prompts/extract_claims.txt").read_text(encoding="utf-8")

def extract_claim_or_empty(user_text: str) -> dict:
    sys = "Extract the claim/pitch from user's text. Reply JSON only."
    out = cheap_chat(system=sys, user=_PROMPT + "\n\nUSER:\n" + user_text, temperature=0.0, max_tokens=300)
    try:
        data = json.loads(out)
        if isinstance(data, dict) and data.get("original_text"):
            return data
    except Exception:
        pass
    return {}
