import sqlite3

import pytest

from backend.db import db_path

SIGN_OFF_NEEDED = "A payout over $1,000.00 needs a handler's sign-off"


def start(api, claim_id, thread_id="thread-1"):
    return api.post(f"/api/claims/{claim_id}/start", json={"thread_id": thread_id})


def decide(api, claim_id, decision, payout, text=("Section 3", "It fits.")):
    section, reason = text
    return api.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": decision,
            "payout": payout,
            "section": section,
            "reason": reason,
        },
    )


def pay(api, claim_id, amount):
    return api.post(f"/api/claims/{claim_id}/payment", json={"amount": amount})


def sign_off(api, claim_id, handler_id):
    return api.post(f"/api/claims/{claim_id}/sign-off", json={"handler_id": handler_id})


def approve(api, claim_id, payout):
    start(api, claim_id)
    return decide(api, claim_id, "approve", payout)


def run_sql(sql):
    db = sqlite3.connect(db_path())
    with db:
        db.execute(sql)
    db.close()


def test_start_claim(api):
    response = start(api, "CLM-1001", "thread-a")
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["thread_id"] == "thread-a"
    assert api.get("/api/claims/CLM-1001").json()["thread_id"] == "thread-a"


def test_start_claim_again_while_in_progress(api):
    start(api, "CLM-1001", "thread-a")
    response = start(api, "CLM-1001", "thread-b")
    assert response.status_code == 200
    assert response.json()["thread_id"] == "thread-b"


def test_start_claim_after_a_decision_is_refused(api):
    start(api, "CLM-1001")
    decide(api, "CLM-1001", "decline", 0)
    response = start(api, "CLM-1001")
    assert response.status_code == 409
    assert response.json()["detail"] == "Claim CLM-1001 is decided"


def test_start_claim_needs_a_thread_id(api):
    assert start(api, "CLM-1001", " ").status_code == 422


def test_record_decision_on_a_waiting_claim_is_refused(api):
    response = decide(api, "CLM-1001", "approve", 420)
    assert response.status_code == 409
    assert "not in progress" in response.json()["detail"]


def test_record_decision_twice_is_refused(api):
    start(api, "CLM-1001")
    decide(api, "CLM-1001", "refer", 0)
    assert decide(api, "CLM-1001", "decline", 0).status_code == 409


def test_steps(api):
    first = api.post(
        "/api/claims/CLM-1001/steps",
        json={"kind": "tool_call", "content": 'get_claim {"claim_id": "CLM-1001"}'},
    )
    assert first.status_code == 200
    api.post("/api/claims/CLM-1001/steps", json={"kind": "message", "content": "Done."})
    steps = api.get("/api/claims/CLM-1001/steps").json()
    assert [(s["kind"], s["content"]) for s in steps] == [
        ("tool_call", 'get_claim {"claim_id": "CLM-1001"}'),
        ("message", "Done."),
    ]
    assert steps[0]["step_id"] < steps[1]["step_id"]
    assert all(s["created_at"] for s in steps)
    assert api.get("/api/claims/CLM-1002/steps").json() == []


def test_steps_need_a_known_kind(api):
    response = api.post(
        "/api/claims/CLM-1001/steps", json={"kind": "thought", "content": "Hmm."}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("decision", "payout", "section", "reason"),
    [
        ("approve", 0, "Section 3", "It fits."),
        ("approve", -5, "Section 3", "It fits."),
        ("decline", 50, "Section 3", "It doesn't fit."),
        ("refer", 10, "Section 11", "A document is missing."),
        ("maybe", 0, "Section 3", "Unsure."),
        ("approve", 420, "", "It fits."),
        ("approve", 420, "Section 3", "   "),
    ],
)
def test_invalid_decisions_are_refused(api, decision, payout, section, reason):
    start(api, "CLM-1001")
    response = decide(api, "CLM-1001", decision, payout, (section, reason))
    assert response.status_code == 422
    assert api.get("/api/claims/CLM-1001").json()["decision"] is None


def test_approve_and_pay_within_the_limit(api):
    response = approve(api, "CLM-1001", 420.00)
    assert response.json()["status"] == "decided"
    assert response.json()["decision"]["payout"] == 420.0
    paid = pay(api, "CLM-1001", 420.00)
    assert paid.status_code == 200
    claim = api.get("/api/claims/CLM-1001").json()
    assert claim["payment"]["amount"] == 420.0
    assert claim["decision"]["decision"] == "approve"
    assert claim["sign_off"] is None
    again = pay(api, "CLM-1001", 420.00)
    assert again.status_code == 409
    assert again.json()["detail"] == "Claim CLM-1001 is already paid"


def test_pay_a_different_amount_is_refused(api):
    approve(api, "CLM-1001", 420.00)
    response = pay(api, "CLM-1001", 400.00)
    assert response.status_code == 422
    assert "$420.00" in response.json()["detail"]
    assert api.get("/api/claims/CLM-1001").json()["payment"] is None


def test_approval_of_exactly_the_limit_is_paid_without_sign_off(api):
    assert approve(api, "CLM-1002", 1000.00).json()["status"] == "decided"
    assert pay(api, "CLM-1002", 1000.00).status_code == 200


def test_approval_over_the_limit_waits_for_sign_off(api):
    assert approve(api, "CLM-1010", 1350.00).json()["status"] == "waiting_for_sign_off"
    response = pay(api, "CLM-1010", 1350.00)
    assert response.status_code == 403
    assert response.json()["detail"] == SIGN_OFF_NEEDED
    assert api.get("/api/claims/CLM-1010").json()["payment"] is None


def test_the_limit_comes_from_the_settings(api):
    run_sql("UPDATE settings SET value = '2000' WHERE key = 'payout_approval_limit'")
    assert approve(api, "CLM-1010", 1350.00).json()["status"] == "decided"
    assert pay(api, "CLM-1010", 1350.00).status_code == 200


def test_sign_off_pays_the_held_payout(api):
    approve(api, "CLM-1010", 1350.00)
    response = sign_off(api, "CLM-1010", "HND-01")
    assert response.status_code == 200
    claim = response.json()
    assert claim["status"] == "decided"
    assert claim["payment"]["amount"] == 1350.0
    assert claim["sign_off"]["handler_id"] == "HND-01"
    assert claim["sign_off"]["handler_name"] == "Dana Whitfield"
    assert claim["sign_off"]["signed_off_at"] == claim["payment"]["paid_at"]
    assert pay(api, "CLM-1010", 1350.00).status_code == 409


def test_sign_off_by_an_unknown_handler(api):
    approve(api, "CLM-1010", 1350.00)
    response = sign_off(api, "CLM-1010", "HND-99")
    assert response.status_code == 404
    assert api.get("/api/claims/CLM-1010").json()["status"] == "waiting_for_sign_off"


def test_sign_off_by_a_handler_who_cannot_approve_over_the_limit(api):
    run_sql(
        "UPDATE handlers SET can_approve_over_limit = 0 WHERE handler_id = 'HND-03'"
    )
    approve(api, "CLM-1010", 1350.00)
    response = sign_off(api, "CLM-1010", "HND-03")
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Priya Raman can't sign off payouts over $1,000.00"
    )
    claim = api.get("/api/claims/CLM-1010").json()
    assert claim["payment"] is None
    assert claim["sign_off"] is None


def test_sign_off_on_a_claim_not_waiting_for_sign_off(api):
    approve(api, "CLM-1001", 420.00)
    response = sign_off(api, "CLM-1001", "HND-01")
    assert response.status_code == 409
    assert "not waiting for sign-off" in response.json()["detail"]
    assert sign_off(api, "CLM-1002", "HND-01").status_code == 409


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_declined_and_referred_claims_are_decided_and_unpaid(api, decision):
    start(api, "CLM-1001")
    assert decide(api, "CLM-1001", decision, 0).json()["status"] == "decided"
    response = pay(api, "CLM-1001", 0)
    assert response.status_code == 409
    assert response.json()["detail"] == "Claim CLM-1001 has no approval to pay"


def test_pay_a_claim_with_no_decision_is_refused(api):
    assert pay(api, "CLM-1001", 420.00).status_code == 409


def test_queue_shows_decisions_and_payouts(api):
    approve(api, "CLM-1001", 420.00)
    first = api.get("/api/claims").json()[0]
    assert (first["status"], first["decision"], first["payout"]) == (
        "decided",
        "approve",
        420.0,
    )


def test_list_handlers(api):
    handlers = api.get("/api/handlers").json()
    assert [h["name"] for h in handlers] == [
        "Dana Whitfield",
        "Marcus Oyelaran",
        "Priya Raman",
    ]
    assert all(h["can_approve_over_limit"] for h in handlers)


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/api/claims/CLM-9999/start", {"thread_id": "t"}),
        ("/api/claims/CLM-9999/steps", {"kind": "message", "content": "Hi."}),
        (
            "/api/claims/CLM-9999/decision",
            {"decision": "refer", "payout": 0, "section": "S", "reason": "R"},
        ),
        ("/api/claims/CLM-9999/payment", {"amount": 10}),
        ("/api/claims/CLM-9999/sign-off", {"handler_id": "HND-01"}),
    ],
)
def test_writes_to_unknown_claims_return_404(api, path, body):
    assert api.post(path, json=body).status_code == 404


def test_list_steps_of_an_unknown_claim_returns_404(api):
    assert api.get("/api/claims/CLM-9999/steps").status_code == 404
