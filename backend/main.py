"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from backend.db import connect, db_path
from backend.models import Claim, ClaimHistory, ClaimSummary, Policy
from backend.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create and seed the database on startup if it is missing."""
    if not db_path().exists():
        seed()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)


def database() -> Iterator[sqlite3.Connection]:
    """Give each request a connection that commits on success."""
    db = connect()
    try:
        with db:
            yield db
    finally:
        db.close()


DB = Annotated[sqlite3.Connection, Depends(database)]


def find(db: sqlite3.Connection, sql: str, key: str, what: str) -> sqlite3.Row:
    """Fetch one row by its id, or raise a 404."""
    row = db.execute(sql, (key,)).fetchone()
    if row is None:
        raise HTTPException(404, f"No {what} with id {key}")
    return row


def load_claim(db: sqlite3.Connection, claim_id: str) -> Claim:
    """Read a claim in full."""
    row = find(
        db,
        "SELECT claims.*, customers.name AS customer_name"
        " FROM claims JOIN customers USING (customer_id) WHERE claim_id = ?",
        claim_id,
        "claim",
    )
    claim = dict(row)
    claim["items"] = json.loads(row["items"])
    claim["documents"] = json.loads(row["documents"])
    return Claim.model_validate(claim)


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
    """Get a claim in full: the story, the items claimed and the documents."""
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
