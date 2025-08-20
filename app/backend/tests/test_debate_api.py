from fastapi.testclient import TestClient
from src.main import create_app

def _client():
    return TestClient(create_app())

def test_debate_actions_happy_path():
    c = _client()
    payload = {
        "session_id": "s-deb-1",
        "mode": "debate_coach",
        "actions": ["evaluate_argument", "generate_counters"],
        "message": "Universal Basic Income reduces productivity."
    }
    r = c.post("/api/v1/debate/actions", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "chat_text" in data
    assert isinstance(data.get("updates"), list)
    # если есть обновления — проверим структуру
    if data["updates"]:
        u0 = data["updates"][0]
        assert "column" in u0 and "items" in u0

def test_debate_actions_wrong_mode_400():
    c = _client()
    payload = {
        "session_id": "s-deb-2",
        "mode": "pitch_objection",  # wrong for this endpoint
        "actions": ["first_impression"],
        "message": "Test"
    }
    r = c.post("/api/v1/debate/actions", json=payload)
    assert r.status_code == 400
