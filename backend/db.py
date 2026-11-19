"""The UnderCover database: SQLite at UNDERCOVER_DB, relative to the repo root."""

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCHEMA = """
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE handlers (
    handler_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    can_approve_over_limit INTEGER NOT NULL
);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    address TEXT NOT NULL,
    customer_since TEXT NOT NULL,
    previous_claims TEXT NOT NULL
);

CREATE TABLE policies (
    policy_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers,
    plan TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    add_ons TEXT NOT NULL,
    purchased_on TEXT NOT NULL,
    sold_through TEXT NOT NULL,
    trip TEXT NOT NULL,
    travelers TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL REFERENCES policies,
    customer_id TEXT NOT NULL REFERENCES customers,
    claim_type TEXT NOT NULL,
    submitted_on TEXT NOT NULL,
    incident_date TEXT NOT NULL,
    incident_location TEXT NOT NULL,
    summary TEXT NOT NULL,
    story TEXT NOT NULL,
    items TEXT NOT NULL,
    amount_claimed REAL NOT NULL,
    documents TEXT NOT NULL,
    status TEXT NOT NULL,
    thread_id TEXT
);

CREATE TABLE decisions (
    claim_id TEXT PRIMARY KEY REFERENCES claims,
    decision TEXT NOT NULL,
    payout REAL NOT NULL,
    section TEXT NOT NULL,
    reason TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    signed_off_by TEXT REFERENCES handlers,
    signed_off_at TEXT
);

CREATE TABLE payments (
    claim_id TEXT PRIMARY KEY REFERENCES claims,
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL
);

CREATE TABLE steps (
    step_id INTEGER PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def db_name() -> str:
    """Return the database file as configured, relative to the repo root."""
    return os.getenv("UNDERCOVER_DB", "undercover.db")


def db_path() -> Path:
    """Return the full path of the database file."""
    return ROOT / db_name()


def connect() -> sqlite3.Connection:
    """Open the database, with rows that read like dicts."""
    db = sqlite3.connect(db_path(), check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db
