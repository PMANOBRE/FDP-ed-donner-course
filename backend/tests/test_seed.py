import json
import sqlite3

from backend.db import ROOT, db_path
from backend.seed import main, seed


def test_seed_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    assert seed() == "Seeded 25 claims, 50 policies, 49 customers and 3 handlers"


def test_seed_marks_every_claim_waiting_and_reads_the_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    seed()
    db = sqlite3.connect(db_path())
    assert db.execute("SELECT DISTINCT status FROM claims").fetchall() == [("waiting",)]
    company = json.loads((ROOT / "data" / "company.json").read_text())
    (limit,) = db.execute(
        "SELECT value FROM settings WHERE key = 'payout_approval_limit'"
    ).fetchone()
    assert float(limit) == company["payout_approval_limit"]
    db.close()


def test_seed_rebuilds_from_scratch(tmp_path, monkeypatch):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    seed()
    db = sqlite3.connect(db_path())
    with db:
        db.execute("UPDATE claims SET status = 'decided'")
    db.close()
    seed()
    db = sqlite3.connect(db_path())
    assert db.execute("SELECT DISTINCT status FROM claims").fetchall() == [("waiting",)]
    db.close()


def test_seed_command(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("UNDERCOVER_DB", str(tmp_path / "test.db"))
    main()
    assert capsys.readouterr().out == (
        "Seeded 25 claims, 50 policies, 49 customers and 3 handlers"
        f" into {tmp_path / 'test.db'}\n"
    )


def test_backend_seeds_a_missing_database(api):
    assert db_path().exists()
    assert len(api.get("/api/claims").json()) == 25
