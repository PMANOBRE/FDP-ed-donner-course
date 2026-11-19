"""Build the UnderCover database from the business data in data/."""

import json
from contextlib import closing
from typing import Any

from backend.db import ROOT, SCHEMA, connect, db_name, db_path

DATA = ROOT / "data"


def load(name: str) -> Any:
    """Read one JSON file from data/."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed() -> str:
    """Rebuild the database from scratch and say what went in."""
    company = load("company.json")
    plan_names = {plan["plan"]: plan["name"] for plan in load("plans.json")["plans"]}
    policies = load("policies.json")
    customers = load("customers.json")
    handlers = load("handlers.json")
    claims = load("claims.json")
    wording = (DATA / "policy_wording.md").read_text(encoding="utf-8")

    db_path().unlink(missing_ok=True)
    with closing(connect()) as db, db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT INTO settings VALUES (?, ?)",
            [
                ("payout_approval_limit", str(company["payout_approval_limit"])),
                ("policy_wording", wording),
            ],
        )
        db.executemany(
            "INSERT INTO handlers VALUES (?, ?, ?, ?)",
            [
                (h["handler_id"], h["name"], h["role"], h["can_approve_over_limit"])
                for h in handlers
            ],
        )
        db.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    c["customer_id"],
                    c["name"],
                    c["email"],
                    c["phone"],
                    c["date_of_birth"],
                    json.dumps(c["address"]),
                    c["customer_since"],
                    json.dumps(c["previous_claims"]),
                )
                for c in customers
            ],
        )
        db.executemany(
            "INSERT INTO policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    p["policy_id"],
                    p["customer_id"],
                    p["plan"],
                    plan_names[p["plan"]],
                    json.dumps(p["add_ons"]),
                    p["purchased_on"],
                    p["sold_through"],
                    json.dumps(p["trip"]),
                    json.dumps(p["travelers"]),
                    p["status"],
                )
                for p in policies
            ],
        )
        db.executemany(
            "INSERT INTO claims VALUES"
            " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting', NULL)",
            [
                (
                    c["claim_id"],
                    c["policy_id"],
                    c["customer_id"],
                    c["claim_type"],
                    c["submitted_on"],
                    c["incident_date"],
                    c["incident_location"],
                    c["summary"],
                    c["story"],
                    json.dumps(c["items"]),
                    c["amount_claimed"],
                    json.dumps(c["documents"]),
                )
                for c in claims
            ],
        )
    return (
        f"Seeded {len(claims)} claims, {len(policies)} policies,"
        f" {len(customers)} customers and {len(handlers)} handlers"
    )


def main() -> None:
    """Rebuild the database and print what went in."""
    print(f"{seed()} into {db_name()}")


if __name__ == "__main__":
    main()
