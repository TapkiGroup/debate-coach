from fastapi.testclient import TestClient
from src.main import create_app

def test_healthz_ok():
    app = create_app()
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
