"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from backend.db import connect, db_path
from backend.models import (
    Claim,
    ClaimHistory,
    ClaimOutcome,
    ClaimSummary,
    Handler,
    NewDecision,
    NewPayment,
    NewSignOff,
    NewStep,
    Policy,
    StartClaim,
    Step,
)
from backend.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create and seed the database on startup if it is missing."""
    if not db_path().exists():
        seed()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)


def database() -> Iterator[sqlite3.Connection]:
    """Give each request a connection that commits on success, else rolls back."""
    db = connect()
    try:
        with db:
            yield db
    finally:
        db.close()


DB = Annotated[sqlite3.Connection, Depends(database)]


def now() -> str:
    """The time now, in UTC."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def money(amount: float) -> str:
    """Format an amount in US dollars, such as $1,250.00."""
    return f"${amount:,.2f}"


def approval_limit(db: sqlite3.Connection) -> float:
    """The payout above which a handler must sign off."""
    row = db.execute(
        "SELECT value FROM settings WHERE key = 'payout_approval_limit'"
    ).fetchone()
    return float(row["value"])


def find(db: sqlite3.Connection, sql: str, key: str, what: str) -> sqlite3.Row:
    """Fetch one row by its id, or raise a 404."""
    row = db.execute(sql, (key,)).fetchone()
    if row is None:
        raise HTTPException(404, f"No {what} with id {key}")
    return row


def outcome(db: sqlite3.Connection, claim_id: str) -> dict[str, Any]:
    """Read a claim's decision, payment and sign-off."""
    decision = db.execute(
        "SELECT decisions.*, signed_off_by AS handler_id, name AS handler_name"
        " FROM decisions LEFT JOIN handlers ON handlers.handler_id = signed_off_by"
        " WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    payment = db.execute(
        "SELECT amount, paid_at FROM payments WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    return {
        "decision": dict(decision) if decision else None,
        "payment": dict(payment) if payment else None,
        "sign_off": dict(decision) if decision and decision["signed_off_by"] else None,
    }


def load_outcome(db: sqlite3.Connection, claim_id: str) -> ClaimOutcome:
    """Read where a claim stands."""
    row = find(
        db,
        "SELECT claim_id, status, thread_id FROM claims WHERE claim_id = ?",
        claim_id,
        "claim",
    )
    return ClaimOutcome.model_validate(dict(row) | outcome(db, claim_id))


def load_claim(db: sqlite3.Connection, claim_id: str) -> Claim:
    """Read a claim in full."""
    row = find(
        db,
        "SELECT claims.*, customers.name AS customer_name"
        " FROM claims JOIN customers USING (customer_id) WHERE claim_id = ?",
        claim_id,
        "claim",
    )
    claim = dict(row) | outcome(db, claim_id)
    claim["items"] = json.loads(row["items"])
    claim["documents"] = json.loads(row["documents"])
    return Claim.model_validate(claim)


def state(status: str) -> str:
    """A status in words, such as waiting for sign-off."""
    return status.replace("_", " ").replace("sign off", "sign-off")


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims(db: DB) -> list[ClaimSummary]:
    """List the claims queue in id order, with where each claim stands."""
    rows = db.execute(
        "SELECT claim_id, customers.name AS customer_name, claim_type, summary,"
        " amount_claimed, submitted_on, status, decision, payout"
        " FROM claims JOIN customers USING (customer_id)"
        " LEFT JOIN decisions USING (claim_id) ORDER BY claim_id"
    )
    return [ClaimSummary.model_validate(dict(row)) for row in rows]


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str, db: DB) -> Claim:
    """Get a claim in full: the story, the items, the documents and the outcome."""
    return load_claim(db, claim_id)


@app.get("/api/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str, db: DB) -> Policy:
    """Get a policy: the plan, the add-ons, the trip and the travelers."""
    row = find(db, "SELECT * FROM policies WHERE policy_id = ?", policy_id, "policy")
    policy = dict(row)
    for field in ("add_ons", "trip", "travelers"):
        policy[field] = json.loads(row[field])
    return Policy.model_validate(policy)


@app.get("/api/customers/{customer_id}/claims", operation_id="get_claim_history")
def get_claim_history(customer_id: str, db: DB) -> ClaimHistory:
    """Get a customer's name and earlier claims, without their contact details."""
    row = find(
        db,
        "SELECT customer_id, name, customer_since, previous_claims"
        " FROM customers WHERE customer_id = ?",
        customer_id,
        "customer",
    )
    return ClaimHistory(
        customer_id=row["customer_id"],
        name=row["name"],
        customer_since=row["customer_since"],
        previous_claims=json.loads(row["previous_claims"]),
    )


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers(db: DB) -> list[Handler]:
    """List the claims handlers."""
    rows = db.execute("SELECT * FROM handlers ORDER BY handler_id")
    return [Handler.model_validate(dict(row)) for row in rows]


@app.post("/api/claims/{claim_id}/start", operation_id="start_claim")
def start_claim(claim_id: str, body: StartClaim, db: DB) -> ClaimOutcome:
    """Start work on a waiting claim, or restart one left in progress."""
    claim = load_outcome(db, claim_id)
    if claim.status not in ("waiting", "in_progress"):
        raise HTTPException(409, f"Claim {claim_id} is {state(claim.status)}")
    db.execute(
        "UPDATE claims SET status = 'in_progress', thread_id = ? WHERE claim_id = ?",
        (body.thread_id, claim_id),
    )
    return load_outcome(db, claim_id)


@app.post("/api/claims/{claim_id}/steps", operation_id="record_step")
def record_step(claim_id: str, body: NewStep, db: DB) -> Step:
    """Record one step of the agent's work on a claim."""
    find(db, "SELECT claim_id FROM claims WHERE claim_id = ?", claim_id, "claim")
    row = db.execute(
        "INSERT INTO steps (claim_id, kind, content, created_at)"
        " VALUES (?, ?, ?, ?) RETURNING *",
        (claim_id, body.kind, body.content, now()),
    ).fetchone()
    return Step.model_validate(dict(row))


@app.get("/api/claims/{claim_id}/steps", operation_id="list_steps")
def list_steps(claim_id: str, db: DB) -> list[Step]:
    """List the steps of the agent's work on a claim, in order."""
    find(db, "SELECT claim_id FROM claims WHERE claim_id = ?", claim_id, "claim")
    rows = db.execute(
        "SELECT * FROM steps WHERE claim_id = ? ORDER BY step_id", (claim_id,)
    )
    return [Step.model_validate(dict(row)) for row in rows]


@app.post("/api/claims/{claim_id}/decision", operation_id="record_decision")
def record_decision(claim_id: str, body: NewDecision, db: DB) -> ClaimOutcome:
    """Record the decision on a claim in progress, with payout, section and reason."""
    claim = load_outcome(db, claim_id)
    if claim.status != "in_progress":
        raise HTTPException(
            409, f"Claim {claim_id} is {state(claim.status)}, not in progress"
        )
    approved = body.decision == "approve"
    if approved and body.payout <= 0:
        raise HTTPException(422, "An approval needs a payout above zero")
    if not approved and body.payout != 0:
        raise HTTPException(422, "A decline or a referral has a payout of zero")
    held = approved and body.payout > approval_limit(db)
    db.execute(
        "INSERT INTO decisions"
        " (claim_id, decision, payout, section, reason, decided_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            claim_id,
            body.decision,
            round(body.payout, 2),
            body.section,
            body.reason,
            now(),
        ),
    )
    db.execute(
        "UPDATE claims SET status = ? WHERE claim_id = ?",
        ("waiting_for_sign_off" if held else "decided", claim_id),
    )
    return load_outcome(db, claim_id)


@app.post("/api/claims/{claim_id}/payment", operation_id="pay_claim")
def pay_claim(claim_id: str, body: NewPayment, db: DB) -> ClaimOutcome:
    """Pay an approved claim exactly its approved payout."""
    claim = load_outcome(db, claim_id)
    if claim.decision is None or claim.decision.decision != "approve":
        raise HTTPException(409, f"Claim {claim_id} has no approval to pay")
    if claim.payment is not None:
        raise HTTPException(409, f"Claim {claim_id} is already paid")
    payout = claim.decision.payout
    if round(body.amount, 2) != payout:
        raise HTTPException(
            422, f"The amount must be the approved payout of {money(payout)}"
        )
    limit = approval_limit(db)
    if payout > limit and claim.sign_off is None:
        raise HTTPException(
            403, f"A payout over {money(limit)} needs a handler's sign-off"
        )
    db.execute("INSERT INTO payments VALUES (?, ?, ?)", (claim_id, payout, now()))
    return load_outcome(db, claim_id)


@app.post("/api/claims/{claim_id}/sign-off", operation_id="sign_off_claim")
def sign_off_claim(claim_id: str, body: NewSignOff, db: DB) -> ClaimOutcome:
    """Sign off a payout held for a handler, which pays it."""
    claim = load_outcome(db, claim_id)
    if claim.status != "waiting_for_sign_off":
        raise HTTPException(
            409, f"Claim {claim_id} is {state(claim.status)}, not waiting for sign-off"
        )
    handler = find(
        db, "SELECT * FROM handlers WHERE handler_id = ?", body.handler_id, "handler"
    )
    if not handler["can_approve_over_limit"]:
        limit = money(approval_limit(db))
        raise HTTPException(
            403, f"{handler['name']} can't sign off payouts over {limit}"
        )
    signed_off_at = now()
    db.execute(
        "UPDATE decisions SET signed_off_by = ?, signed_off_at = ? WHERE claim_id = ?",
        (body.handler_id, signed_off_at, claim_id),
    )
    db.execute(
        "INSERT INTO payments SELECT claim_id, payout, ? FROM decisions"
        " WHERE claim_id = ?",
        (signed_off_at, claim_id),
    )
    db.execute("UPDATE claims SET status = 'decided' WHERE claim_id = ?", (claim_id,))
    return load_outcome(db, claim_id)
