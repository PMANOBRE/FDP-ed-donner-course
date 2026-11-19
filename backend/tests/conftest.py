import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def api(tmp_path, monkeypatch):
    """A client for the backend on a fresh database of its own."""
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        yield client
