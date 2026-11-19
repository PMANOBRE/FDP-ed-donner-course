"""The shapes of the UnderCover API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

Status = Literal["waiting", "in_progress", "waiting_for_sign_off", "decided"]
DecisionKind = Literal["approve", "decline", "refer"]


class ClaimSummary(BaseModel):
    """A claim as it appears in the queue."""

    claim_id: str
    customer_name: str
    claim_type: str
    summary: str
    amount_claimed: float
    submitted_on: date
    status: Status
    decision: DecisionKind | None
    payout: float | None


class Item(BaseModel):
    """One thing the customer is claiming for."""

    description: str
    category: str
    amount: float


class Document(BaseModel):
    """A supporting document, as text."""

    name: str
    type: str
    content: str


class Claim(BaseModel):
    """A claim in full."""

    claim_id: str
    status: Status
    policy_id: str
    customer_id: str
    customer_name: str
    claim_type: str
    submitted_on: date
    incident_date: date
    incident_location: str
    summary: str
    story: str
    items: list[Item]
    amount_claimed: float
    documents: list[Document]


class Trip(BaseModel):
    """The covered trip."""

    destination: str
    departs_on: date
    returns_on: date
    trip_cost: float


class Policy(BaseModel):
    """A policy record."""

    policy_id: str
    customer_id: str
    plan: str
    plan_name: str
    add_ons: list[str]
    purchased_on: date
    sold_through: str
    trip: Trip
    travelers: list[str]
    status: str


class EarlierClaim(BaseModel):
    """A claim the customer made before."""

    claim_id: str
    filed_on: date
    incident_date: date
    claim_type: str
    summary: str
    outcome: str
    amount_paid: float


class ClaimHistory(BaseModel):
    """A customer's name and earlier claims, without contact details."""

    customer_id: str
    name: str
    customer_since: date
    previous_claims: list[EarlierClaim]
