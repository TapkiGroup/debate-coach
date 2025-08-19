import importlib
import types
import pytest

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore


@pytest.mark.skipif(TestClient is None, reason="fastapi[test] not installed")
@pytest.mark.parametrize("endpoint,payload", [
    ("/api/v1/debate/actions", {
        "session_id": "s1",
        "mode": "debate_coach",
        "actions": ["evaluate_argument"],
        "message": "Universal basic income reduces productivity"
    }),
    ("/api/v1/pitch/actions", {
        "session_id": "s2",
        "mode": "pitch_objection",
        "actions": ["first_impression"],
        "message": "AI tool that writes grant proposals for NGOs"
    }),
])
def test_action_endpoints_basic_200(endpoint, payload):
    mod = importlib.import_module("src.main")
    factory = getattr(mod, "create_app", None)
    assert isinstance(factory, types.FunctionType), "create_app() not found in src.main"
    app = factory()
    client = TestClient(app)
    r = client.post(endpoint, json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "chat_text" in data
    assert isinstance(data.get("updates", []), list)