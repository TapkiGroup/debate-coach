import json
from pathlib import Path
from core.llm.main_client import chat
from agents.triage.triage_agent import classify_intent
from agents.planner.planner_agent import plan_steps
from agents.tools.parsing import extract_claim_or_empty
from core.schemas import Intent, Mode
from agents.supervisor.policies import require_fallacy_first, only_one_executor

_PROMPT = Path("prompts/supervisor.txt").read_text(encoding="utf-8")

def decide(mode: Mode, last_user_text: str, session_flags: dict) -> dict:

    # TRIAGE (LLM)
    tri = classify_intent(mode.value, last_user_text)
    intent = tri.get("intent","none")
    has_new_claim = bool(tri.get("has_new_claim", False))

    # Try to extract (LLM). This is only advisory; chat_loop already does authoritative extraction.
    claim = extract_claim_or_empty(last_user_text) if has_new_claim else {}

    flags = dict(session_flags)
    flags.update({
        "triage_intent": intent,
        "has_new_claim": has_new_claim,
        "has_extracted_claim": bool(claim),
    })

    # Supervisor raw command
    sys = "You are Supervisor. Output JSON command ONLY."
    user = f"""{_PROMPT}

SESSION_FLAGS: {json.dumps(flags, ensure_ascii=False)}
"""
    raw = chat(system=sys, user=user, temperature=0.0, max_tokens=300)
    try:
        cmd = json.loads(raw)
    except Exception:
        cmd = {"command":"OFFER_ACTIONS","reason":"fallback"}

    # If a new claim was present but supervisor didn't choose a plan, force UPDATE_PRO_ONLY.
    if has_new_claim and cmd.get("command") in {None, "", "OFFER_ACTIONS", "NUDGE"}:
        cmd = {"command": "UPDATE_PRO_ONLY", "reason": "new claim captured"}

    # If RUN_PIPELINE -> ask PLANNER (LLM) for plan and enforce policies
    if cmd.get("command") == "RUN_PIPELINE":
        steps = plan_steps(mode.value, intent, flags)
        steps = require_fallacy_first(steps, Intent(intent))
        steps = only_one_executor(steps)
        cmd["plan_steps"] = steps

    # Attach triage intent & extracted claim (advisory)
    cmd["intent"] = intent
    if claim:
        cmd["extracted_claim"] = claim

    return cmd
