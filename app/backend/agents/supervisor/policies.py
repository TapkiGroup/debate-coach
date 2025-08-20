from core.schemas import Intent

# Hard policies applied around LLM outputs (not replacing LLM triage/planner, only guardrails)

def require_fallacy_first(plan_steps: list[str], intent: Intent) -> list[str]:
    if intent in {Intent.evaluate_argument, Intent.give_objections}:
        if not plan_steps or "FALLACY_CHECK" not in plan_steps[:2]:
            plan_steps = ["FALLACY_CHECK"] + [s for s in plan_steps if s != "FALLACY_CHECK"]
    return plan_steps

def only_one_executor(plan_steps: list[str]) -> list[str]:
    seen = False
    cleaned = []
    for s in plan_steps:
        if s.startswith("EXECUTOR:"):
            if seen:
                continue
            seen = True
        cleaned.append(s)
    return cleaned
