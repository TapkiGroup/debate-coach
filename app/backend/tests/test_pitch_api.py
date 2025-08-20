from fastapi.testclient import TestClient
from src.main import create_app

def _client():
    return TestClient(create_app())

def test_pitch_actions_happy_path():
    c = _client()
    payload = {
        "session_id": "s-pit-1",
        "mode": "pitch_objection",
        "actions": ["first_impression", "objections"],
        "message": "We build an AI grant-writer for NGOs; 20% win-rate uplift."
    }
    r = c.post("/api/v1/pitch/actions", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    
    assert "chat_text" in data
    assert isinstance(data.get("updates"), list)

def test_pitch_actions_wrong_mode_400():
    c = _client()
    payload = {
        "session_id": "s-pit-2",
        "mode": "debate_coach",  
        "actions": ["evaluate_argument"],
        "message": "Test"
    }
    r = c.post("/api/v1/pitch/actions", json=payload)
    assert r.status_code == 400
