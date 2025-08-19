"""
Smoke tests to verify the backend skeleton boots and exposes basic routes.
Run with: pytest -q app/backend/tests/test_smoke_server.py
"""
import importlib
import types
import pytest

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore


def _import_app_factory():
    """Import src.main and return create_app callable."""
    mod = importlib.import_module("src.main")
    factory = getattr(mod, "create_app", None)
    assert isinstance(factory, types.FunctionType), "create_app() not found in src.main"
    return factory


@pytest.mark.skipif(TestClient is None, reason="fastapi[test] not installed")
def test_healthz_route_responds():
    factory = _import_app_factory()
    app = factory()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.skipif(TestClient is None, reason="fastapi[test] not installed")
def test_unknown_route_returns_404():
    factory = _import_app_factory()
    app = factory()
    client = TestClient(app)
    r = client.get("/this/route/does/not/exist")
    assert r.status_code == 404
