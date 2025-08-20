import json
import pytest
from fastapi.testclient import TestClient
import importlib

# --- Deterministic stubs for LLM and research ---

def _triage_stub(mode: str, user_text: str):
    txt = user_text.lower()
    if "evaluate_argument" in txt or "ruthless_impression" in txt:
        return {"intent": "evaluate_argument", "has_new_claim": False}
    if "give_objections" in txt or "objections" in txt:
        return {"intent": "give_objections", "has_new_claim": False}
    if "research" in txt:
        return {"intent": "research", "has_new_claim": False}
    # if a claim/pitch-like sentence arrives -> mark as new claim
    has_claim = any(k in txt for k in ["my claim:", "pitch:"])
    return {"intent": "none", "has_new_claim": has_claim}

def _planner_stub(mode: str, intent: str, flags: dict):
    # Always insert FALLACY before critique/objections
    if intent in ("evaluate_argument", "give_objections"):
        return ["FALLACY_CHECK", "EXECUTOR:" + intent, "SCORE", "SUGGEST_NEXT"]
    if intent == "research":
        return ["EXECUTOR:research", "SUGGEST_NEXT"]
    return ["EXECUTOR:offer_actions"]

def _supervisor_stub(system: str, user: str, temperature: float = 0.0, max_tokens: int = 300):
    # Read session flags from user content (we know our prompt shape)
    # Simplify: if has_new_claim -> UPDATE_PRO_ONLY; if intent present -> RUN_PIPELINE; else OFFER_ACTIONS
    # This is a crude but deterministic parser over the JSON embedded in the user message.
    try:
        flags_str = user.split("SESSION_FLAGS:")[1].strip()
        # find the first '{' to end of text
        jstart = flags_str.find("{")
        jtxt = flags_str[jstart:]
        flags = json.loads(jtxt)
    except Exception:
        flags = {}

    intent = flags.get("triage_intent", "none")
    has_new = bool(flags.get("has_new_claim"))
    if has_new and intent == "none":
        return json.dumps({"command": "UPDATE_PRO_ONLY", "reason": "new claim"})
    if intent in ("evaluate_argument", "give_objections", "research"):
        return json.dumps({"command": "RUN_PIPELINE", "reason": "do action"})
    return json.dumps({"command": "OFFER_ACTIONS", "reason": "no intent"})

def _extract_claim_stub(user_text: str):
    txt = user_text.strip()
    if txt.lower().startswith("my claim:"):
        return {"original_text": txt, "normalized": "banning cash will reduce crime"}
    if txt.lower().startswith("pitch:"):
        return {"original_text": txt, "normalized": "drone grocery delivery cuts times by 80%"}
    return {}

def _fallacies_stub(text: str):
    # Return one fallacy for visibility
    return [{"code": "appeal_to_authority", "label": "Appeal to authority", "emoji": "🎓", "why": "Cites authority without evidence."}]

def _score_stub(claim: str, context_hint: str = ""):
    return {"bullets": ["Clarity is moderate", "Evidence is limited"], "score": {"value": 67, "reasons": ["baseline stub"]}}

def _main_chat_eval_stub(system: str, user: str, temperature: float = 0.3, max_tokens: int = 900):
    # Executors expect JSON for evaluation and objections
    if "generate top objections" in system.lower() or "ranked counter-arguments" in system.lower():
        payload = {"ranked": [
            {"title": "Displacement effect", "why": "Crime shifts to digital methods"},
            {"title": "Unbanked population", "why": "Harms those without access to banking"},
        ]}
        return json.dumps(payload)
    # evaluation / ruthless impression
    payload = {"bullets": [
        "Assumes cash is main driver of crime",
        "Overlooks laundering via crypto and prepaid cards"
    ], "score": {"value": 62, "reasons": ["logic gaps", "weak evidence"]}}
    return json.dumps(payload)

def _research_gather_stub(query: str, max_results: int = 8):
    return [
        {"title": "UN report on cash and crime", "url": "https://example.org/un-cash", "snippet": "Mixed evidence"},
        {"title": "Academic study on cashless and crime", "url": "https://example.org/paper-cashless", "snippet": "Shows displacement"},
    ]

def _research_classify_stub(claim: str, sources):
    return [
        {"url":"https://example.org/un-cash", "title":"UN report on cash and crime", "supports":"neutral", "reliability":"high", "tag":"⚠️", "note":"Evidence mixed."},
        {"url":"https://example.org/paper-cashless", "title":"Academic study on cashless and crime", "supports":"undermines", "reliability":"high", "tag":"❌", "note":"Suggests displacement."}
    ]

@pytest.fixture(autouse=True)
def patch_llm_and_tools(monkeypatch):
    # TRIAGE & PLANNER
    from agents.triage import triage_agent
    from agents.planner import planner_agent
    monkeypatch.setattr(triage_agent, "classify_intent", _triage_stub)
    monkeypatch.setattr(planner_agent, "plan_steps", _planner_stub)

    # SUPERVISOR (smol client chat)
    from core.llm import smol_client
    monkeypatch.setattr(smol_client, "chat", _supervisor_stub)

    # Parsing (claim extractor)
    from agents.tools import parsing as parsing_tool
    monkeypatch.setattr(parsing_tool, "extract_claim_or_empty", _extract_claim_stub)

    # Fallacies + Scoring
    from agents.tools import fallacies as fall_tool
    from agents.tools import scoring as score_tool
    monkeypatch.setattr(fall_tool, "detect_fallacies", _fallacies_stub)
    monkeypatch.setattr(score_tool, "score_claim", _score_stub)

    # Executors main chat (evaluation/objections JSON)
    from core.llm import main_client
    monkeypatch.setattr(main_client, "chat", _main_chat_eval_stub)

    # Research
    from agents.tools import research as research_tool
    monkeypatch.setattr(research_tool, "gather_sources", _research_gather_stub)
    monkeypatch.setattr(research_tool, "classify_sources", _research_classify_stub)

    yield

@pytest.fixture
def client():
    # Import after patches so any module-level imports see the monkeypatch
    app_module = importlib.import_module("main")
    app = getattr(app_module, "app")
    return TestClient(app)
