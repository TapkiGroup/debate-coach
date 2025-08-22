import json
from pathlib import Path
from core.llm.main_client import chat

_PLANNER_PROMPT = Path("prompts/planner.txt").read_text(encoding="utf-8")

def plan_steps(mode: str, intent: str, flags: dict) -> list[str]:
    sys = "You are PLANNER. Return JSON ONLY."
    user = f"""{_PLANNER_PROMPT}

MODE: {mode}
INTENT: {intent}
FLAGS: {json.dumps(flags)}
"""
    out = chat(system=sys, user=user, temperature=0.0, max_tokens=200)
    try:
        data = json.loads(out)
        steps = data.get("plan_steps", [])
        if isinstance(steps, list) and steps:
            return steps
    except Exception:
        pass
    # Safe minimal default if planner failed (still LLM-first design elsewhere)
    return ["EXECUTOR:offer_actions"]
