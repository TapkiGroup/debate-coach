from typing import List
from core.schemas import ChatIn, ChatOut, Event, Column, Intent, Mode, Source, Score
from core.state import SessionStore
from agents.supervisor.supervisor_agent import decide
from agents.executors import debate_executor, pitch_executor
from agents.tools.parsing import extract_claim_or_empty

def run_chat_turn(payload: ChatIn, store: SessionStore) -> ChatOut:
    st = store.get(payload.session_id)
    mode = st.mode
    user_text = payload.user_text

    events_to_return: List[Event] = []
    fallacies = None
    score = None

    # === 1) Extract claim/pitch FIRST and persist PRO (append-only, no strengthening)
    extracted = extract_claim_or_empty(user_text)
    if extracted and extracted.get("original_text"):
        st.last_user_claim_raw = extracted.get("original_text")
        st.has_new_claim_this_turn = True
        ev = Event(
            column=Column.PRO,
            payload={
                "summary_raw": extracted.get("original_text"),
                "normalized": extracted.get("normalized"),
            },
        )
        # persist + return
        store.append_event(payload.session_id, ev)
        events_to_return.append(ev)
    else:
        st.has_new_claim_this_turn = False

    # === 2) Supervisor decides what to do next (aware of flags)
    flags = {
        "did_fallacy_on_this_claim": st.did_fallacy_on_this_claim,
        "last_intent": st.last_intent.value if st.last_intent else None,
        "has_new_claim": st.has_new_claim_this_turn,
        "has_last_claim": bool(st.last_user_claim_raw),
    }
    cmd = decide(mode, user_text, flags)

    intent = cmd.get("intent", "none")
    if intent in Intent.__members__:
        st.last_intent = Intent(intent)

    command = cmd.get("command")

    # === 3) If supervisor says NUDGE — but we already captured PRO, still nudge for action
    if command == "NUDGE":
        if st.has_new_claim_this_turn:
            return ChatOut(
                chat_reply="Got your position. Should I evaluate it, generate objections, or gather sources?",
                events=events_to_return,
            )
        return ChatOut(
            chat_reply="Please paste your argument/pitch so I can help. One or two sentences is enough.",
            events=[],
        )

    # === 4) OFFER_ACTIONS: return menu; PRO (if any) already persisted
    if command == "OFFER_ACTIONS":
        return ChatOut(
            chat_reply="What should I do next? Options: evaluate_argument / give_objections (or objections for pitch) / research.",
            events=events_to_return,
        )

    # === 5) UPDATE_PRO_ONLY: we already persisted PRO; now offer actions
    if command == "UPDATE_PRO_ONLY" and not cmd.get("plan_steps"):
        return ChatOut(
            chat_reply="Got your position. Should I evaluate it, generate objections, or gather sources?",
            events=events_to_return,
        )

    # === 6) RUN_PIPELINE → execute one step per MVP
    if command == "RUN_PIPELINE":
        steps = cmd.get("plan_steps", [])
        need_fallacy = "FALLACY_CHECK" in steps
        claim = st.last_user_claim_raw or user_text

        # --- Unified RESEARCH handling for BOTH modes (persist SOURCES) ---
        if intent == "research":
            from agents.tools.research import gather_sources, classify_sources
            sources = gather_sources(claim, max_results=8)
            classified = classify_sources(claim, sources) if sources else []

            # Convert to Source objects and store
            new_sources: List[Source] = []
            from core.schemas import Source as SourceModel, SourceReliability, EvidenceTag
            for it in classified:
                reliability = (it.get("reliability") or "medium").lower()
                reliability = reliability if reliability in {"high", "medium", "low"} else "medium"
                tag_icon = (it.get("tag") or "")
                tag_map = {"✅": "corroborated", "❌": "refuted", "⚠️": "disputed", "🕳": "unverifiable"}
                ev_tag = tag_map.get(tag_icon)
                new_sources.append(
                    SourceModel(
                        title=it.get("title", "") or it.get("url", ""),
                        url=it.get("url", ""),
                        note=it.get("note", ""),
                        reliability=SourceReliability(reliability),
                        tag=EvidenceTag(ev_tag) if ev_tag else None,
                    )
                )

            sids = store.add_sources(payload.session_id, new_sources)
            # meta event (not persisted in state.events; sources are persisted in state.sources)
            meta_ev = Event(column=Column.SOURCES, payload={"added_sids": sids, "count": len(sids)})
            events_to_return.append(meta_ev)
            chat_reply = "I've added relevant neutral sources to the SOURCES column."
            return ChatOut(chat_reply=chat_reply, events=events_to_return)

        # --- Non-research executors ---
        if mode == Mode.debate_counter:
            result = debate_executor.execute(intent=intent, claim=claim, need_fallacy=need_fallacy)
        else:
            # pitch mode: normalize evaluator/objections names
            pin = intent
            if intent == "give_objections":
                pin = "objections"
            if intent == "evaluate_argument":
                pin = "ruthless_impression"
            result = pitch_executor.execute(intent=pin, pitch_text=claim, need_fallacy=need_fallacy)

        # Persist CON events; append to return list
        for ev in result.get("events", []):
            if ev.column == Column.CON:
                store.append_event(payload.session_id, ev)
            events_to_return.append(ev)

        fallacies = result.get("fallacies")
        score = result.get("score")
        return ChatOut(chat_reply=result.get("chat_reply", "Done."), events=events_to_return, score=score, fallacies=fallacies)

    # === 7) Fallback — never lose the PRO update we already persisted
    return ChatOut(
        chat_reply="I captured your message. Would you like me to evaluate, object, or research?",
        events=events_to_return,
    )
