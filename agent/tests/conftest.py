import pytest
from fastapi.testclient import TestClient

from agent import main
from backend.main import app


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Point the agent at a backend on a fresh database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))
    with TestClient(app) as client:
        yield client
