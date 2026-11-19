import sqlite3

import pytest
from langchain_core.messages import AIMessage

from agent import __main__ as cli
from agent import main
from agent.tests.test_agent import StubModel, decision
from backend.db import db_path

REAL_RUN = main.run


def script(claim_id, kind, payout):
    """A stub model that reads the claim, decides it, pays an approval and replies."""
    calls = [("get_claim", {"claim_id": claim_id}), decision(claim_id, kind, payout)]
    if kind == "approve":
        calls.append(("pay_claim", {"claim_id": claim_id, "amount": payout}))
    replies = [
        AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": str(i)}])
        for i, (name, args) in enumerate(calls)
    ]
    return StubModel(messages=iter([*replies, AIMessage(content="Done.")]))


def leave_two_waiting():
    """Leave CLM-1001 and CLM-1003 waiting: one claim in progress, the rest decided."""
    db = sqlite3.connect(db_path())
    with db:
        db.execute("UPDATE claims SET status = 'decided' WHERE claim_id > 'CLM-1003'")
        db.execute(
            "UPDATE claims SET status = 'in_progress' WHERE claim_id = 'CLM-1002'"
        )
    db.close()


@pytest.mark.usefixtures("api")
def test_queue_works_each_waiting_claim_once(monkeypatch, capsys):
    leave_two_waiting()
    plans = {"CLM-1001": ("approve", 420.0), "CLM-1003": ("refer", 0)}
    worked = []

    def run(claim_id, thread_id):
        worked.append(claim_id)
        return REAL_RUN(claim_id, thread_id, script(claim_id, *plans[claim_id]))

    monkeypatch.setattr(main, "run", run)
    cli.main([])
    assert worked == ["CLM-1001", "CLM-1003"]
    assert capsys.readouterr().out == (
        "CLM-1001  approve  $420.00\n"
        "CLM-1003  refer    $0.00\n"
        "approve 1, decline 0, refer 1\n"
    )


def test_queue_carries_on_after_a_claim_fails(api, monkeypatch, capsys):
    leave_two_waiting()

    def run(claim_id, thread_id):
        if claim_id == "CLM-1001":
            raise RuntimeError("The model is unavailable")
        return REAL_RUN(claim_id, thread_id, script(claim_id, "decline", 0))

    monkeypatch.setattr(main, "run", run)
    counts = main.work_queue()
    assert capsys.readouterr().out == (
        "CLM-1001  error    The model is unavailable\n"
        "CLM-1003  decline  $0.00\n"
        "approve 0, decline 1, refer 0, error 1\n"
    )
    assert counts == {"error": 1, "decline": 1}
    assert api.get("/api/claims/CLM-1003").json()["status"] == "decided"


@pytest.mark.usefixtures("api")
def test_queue_reports_a_claim_left_undecided(monkeypatch, capsys):
    leave_two_waiting()
    monkeypatch.setattr(main, "run", lambda claim_id, thread_id: "I am not sure.")
    main.work_queue()
    assert capsys.readouterr().out == (
        "CLM-1001  undecided\n"
        "CLM-1003  undecided\n"
        "approve 0, decline 0, refer 0, undecided 2\n"
    )


@pytest.mark.usefixtures("api")
def test_queue_shortens_a_long_error(monkeypatch, capsys):
    leave_two_waiting()

    def run(claim_id, thread_id):
        raise RuntimeError("Error code: 429 - " + "rate limited " * 40)

    monkeypatch.setattr(main, "run", run)
    main.work_queue()
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith("CLM-1001  error    Error code: 429 - rate limited")
    assert first.endswith("[...]")
    assert len(first) < 140
