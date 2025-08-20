import json

def _post(client, url, payload=None):
    if payload is None:
        r = client.post(url)
    else:
        r = client.post(url, json=payload)
    assert r.status_code == 200, r.text
    return r.json()

def _get(client, url):
    r = client.get(url)
    assert r.status_code == 200, r.text
    return r.json()

def test_debate_full_cycle(client):
    # 1) session
    sess = _post(client, "/api/session?mode=debate_counter")
    sid = sess["session_id"]

    # 2) first turn: claim -> should append PRO event
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "My claim: banning cash will reduce crime."})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["PRO"]) == 1, cols
    assert cols["CON"] == [], cols["CON"]
    assert cols["SOURCES"] == [], cols["SOURCES"]

    # 3) evaluate -> CON + score
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "evaluate_argument"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["CON"]) >= 1, cols
    # payload contains either 'critique' or 'counters_ranked'
    last_con = cols["CON"][-1]["payload"]
    assert ("critique" in last_con) or ("counters_ranked" in last_con)
    # score present in chat response (stubbed)
    assert "chat_reply" in out

    # 4) objections -> another CON
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "give_objections"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["CON"]) >= 2, cols
    assert "counters_ranked" in cols["CON"][-1]["payload"]

    # 5) research -> SOURCES >= 1
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "research"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["SOURCES"]) >= 1, cols["SOURCES"]

def test_pitch_full_cycle(client):
    # 1) session
    sess = _post(client, "/api/session?mode=pitch_objections")
    sid = sess["session_id"]

    # 2) first turn: pitch -> PRO
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "Pitch: We will deliver groceries by autonomous drones in dense urban areas to cut delivery times by 80%."})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["PRO"]) == 1

    # 3) ruthless impression -> CON
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "ruthless_impression"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["CON"]) >= 1
    last_con = cols["CON"][-1]["payload"]
    assert ("critique" in last_con) or ("objections_ranked" in last_con)

    # 4) objections -> another CON
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "objections"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["CON"]) >= 2
    assert ("objections_ranked" in cols["CON"][-1]["payload"]) or ("counters_ranked" in cols["CON"][-1]["payload"])

    # 5) research -> SOURCES
    out = _post(client, "/api/chat", {"session_id": sid, "user_text": "research"})
    cols = _get(client, f"/api/columns?session_id={sid}")
    assert len(cols["SOURCES"]) >= 1
