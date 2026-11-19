import pytest


def test_list_claims(api):
    claims = api.get("/api/claims").json()
    assert len(claims) == 25
    assert [c["claim_id"] for c in claims] == sorted(c["claim_id"] for c in claims)
    assert {c["status"] for c in claims} == {"waiting"}
    assert claims[0] == {
        "claim_id": "CLM-1001",
        "customer_name": "Maya Patel",
        "claim_type": "trip_delay",
        "summary": "Flight home canceled by the airline, rebooked the next morning",
        "amount_claimed": 420.0,
        "submitted_on": "2026-06-24",
        "status": "waiting",
        "decision": None,
        "payout": None,
    }


def test_get_claim(api):
    claim = api.get("/api/claims/CLM-1001").json()
    assert claim["story"].startswith("My flight home from Rome")
    assert len(claim["items"]) == 3
    assert len(claim["documents"]) == 4
    assert claim["status"] == "waiting"
    assert claim["customer_name"] == "Maya Patel"
    assert claim["documents"][0]["name"] == "Meridian Air cancellation notice"


def test_get_policy(api):
    policy = api.get("/api/policies/POL-2001").json()
    assert policy["plan"] == "premium"
    assert policy["plan_name"] == "UnderCover Premium"
    assert policy["add_ons"] == []
    assert policy["trip"]["destination"] == "Rome, Italy"
    assert policy["trip"]["returns_on"] == "2026-06-18"
    assert policy["travelers"] == ["Maya Patel"]


def test_get_claim_history_leaves_out_contact_details(api):
    history = api.get("/api/customers/CUS-3001/claims").json()
    assert history["name"] == "Maya Patel"
    assert [c["claim_id"] for c in history["previous_claims"]] == ["CLM-0412"]
    for field in ("email", "phone", "address", "date_of_birth"):
        assert field not in history


@pytest.mark.parametrize(
    "path",
    [
        "/api/claims/CLM-9999",
        "/api/policies/POL-9999",
        "/api/customers/CUS-9999/claims",
    ],
)
def test_unknown_ids_return_404(api, path):
    response = api.get(path)
    assert response.status_code == 404
    assert "9999" in response.json()["detail"]
