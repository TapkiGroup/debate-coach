from typing import List
from core.schemas import ChatIn, ChatOut, Event, Column, Intent, Mode, Source, Score
from core.state import SessionStore
from agents.supervisor.supervisor_agent import decide
from agents.executors import debate_executor, pitch_executor
from agents.tools.parsing import extract_claim_or_empty

def _reply(chat_reply: str, events: List[Event], score, fallacies) -> ChatOut:
    return ChatOut(chat_reply=chat_reply, events=events, score=score, fallacies=fallacies or [])

def _persist_pro_if_any(user_text: str, st, store: SessionStore, session_id: str) -> List[Event]:
    events: List[Event] = []
    extracted = extract_claim_or_empty(user_text)
    if extracted:
        normalized = (extracted.get("normalized") or "").strip()
        original = (extracted.get("original_text") or "").strip()
    else:
        normalized = original = ""

    # Only update PRO when we truly got a claim, not a command like "evaluate it"
    if normalized and original:
        st.last_user_claim_raw = original
        st.has_new_claim_this_turn = True
        ev = Event(column=Column.PRO, payload=f"You current statement: {normalized}")
        store.append_event(session_id, ev)
        events.append(ev)
    else:
        st.has_new_claim_this_turn = False  # keep previous last_user_claim_raw
    return events

def _intent_override(user_text: str) -> str | None:
    t = user_text.lower()
    # be generous with synonyms
    if any(w in t for w in ["evaluate_argument", "evaluate it", "evaluate", "critique", "score it", "review"]):
        return "evaluate_argument"
    if any(w in t for w in ["give_objections", "objections", "counter", "refute", "rebut"]):
        return "give_objections"
    if "research" in t:
        return "research"
    return None

def run_chat_turn(payload: ChatIn, store: SessionStore) -> ChatOut:
    st = store.get(payload.session_id)
    mode = st.mode
    user_text = payload.user_text

    events_to_return: List[Event] = []
    fallacies = []
    score = None

    # 1) Extract & persist PRO
    events_to_return.extend(_persist_pro_if_any(user_text, st, store, payload.session_id))

    # 2) Supervisor + local override
    flags = {
        "did_fallacy_on_this_claim": st.did_fallacy_on_this_claim,
        "last_intent": st.last_intent.value if st.last_intent else None,
        "has_new_claim": st.has_new_claim_this_turn,
        "has_last_claim": bool(st.last_user_claim_raw),
    }
    cmd = decide(mode, user_text, flags)
    intent = cmd.get("intent", "none")

    # Hard override: if user explicitly asked, trust the user
    override = _intent_override(user_text)
    if override:
        intent = override
        cmd["command"] = "RUN_PIPELINE"
        cmd["plan_steps"] = ["FALLACY_CHECK"]  # keep fallacies when requested later

    # Record last_intent
    if intent in Intent.__members__:
        st.last_intent = Intent(intent)

    command = cmd.get("command")

    # If a new PRO just arrived, do NOT run pipeline automatically: always nudge
    if st.has_new_claim_this_turn and command == "RUN_PIPELINE" and intent != "research" and not override:
        return _reply(
            "Got your position. Should I evaluate it, generate objections, or gather sources?",
            events_to_return, score, fallacies
        )

    # 3) NUDGE
    if command == "NUDGE":
        if st.has_new_claim_this_turn:
            return _reply(
                "Got your position. Should I evaluate it, generate objections, or gather sources?",
                events_to_return, score, fallacies
            )
        return _reply(
            "Please paste your argument/pitch so I can help. One or two sentences is enough.",
            [], score, fallacies
        )

    # 4) OFFER_ACTIONS
    if command == "OFFER_ACTIONS":
        return _reply(
            "What should I do next? Options: evaluate_argument / give_objections (or objections for pitch) / research.",
            events_to_return, score, fallacies
        )

    # 5) UPDATE_PRO_ONLY
    if command == "UPDATE_PRO_ONLY" and not cmd.get("plan_steps"):
        return _reply(
            "Got your position. Should I evaluate it, generate objections, or gather sources?",
            events_to_return, score, fallacies
        )

    # 6) RUN_PIPELINE
    if command == "RUN_PIPELINE":
        steps = cmd.get("plan_steps", [])
        need_fallacy = "FALLACY_CHECK" in steps
        claim = st.last_user_claim_raw or user_text

        if intent == "research":
            return _reply("I can't do research yet, sorry!.", events_to_return, score, fallacies)

        if mode == Mode.debate_counter:
            result = debate_executor.execute(intent=intent, claim=claim, need_fallacy=need_fallacy)
        else:
            pin = intent
            if intent == "give_objections":
                pin = "objections"
            if intent == "evaluate_argument":
                pin = "ruthless_impression"
            result = pitch_executor.execute(intent=pin, pitch_text=claim, need_fallacy=False)

        # Persist CON events; append to return list
        for ev in result.get("events", []):
            if ev.column == Column.CON:
                store.append_event(payload.session_id, ev)
            events_to_return.append(ev)

        fallacies = result.get("fallacies") or []
        score = result.get("score")

        # Optional: cache score in session (if field exists)
        try:
            if score is not None:
                st.last_score = score
        except Exception:
            pass

        return _reply(result.get("chat_reply", "Done."), events_to_return, score, fallacies)

    # 7) Fallback
    return _reply(
        "I captured your message. Would you like me to evaluate, object, or research?",
        events_to_return, score, fallacies
    )
