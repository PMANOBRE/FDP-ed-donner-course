"""The shapes of the UnderCover API."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

Status = Literal["waiting", "in_progress", "waiting_for_sign_off", "decided"]
DecisionKind = Literal["approve", "decline", "refer"]
StepKind = Literal["tool_call", "tool_result", "message"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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


class Decision(BaseModel):
    """The decision on a claim."""

    decision: DecisionKind
    payout: float
    section: str
    reason: str
    decided_at: datetime


class Payment(BaseModel):
    """A payment made on a claim."""

    amount: float
    paid_at: datetime


class SignOff(BaseModel):
    """A handler's sign-off on a payout over the approval limit."""

    handler_id: str
    handler_name: str
    signed_off_at: datetime


class ClaimOutcome(BaseModel):
    """Where a claim stands: its status, decision, payment and sign-off."""

    claim_id: str
    status: Status
    thread_id: str | None
    decision: Decision | None
    payment: Payment | None
    sign_off: SignOff | None


class Claim(ClaimOutcome):
    """A claim in full, with where it stands."""

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


class Step(BaseModel):
    """One step of the agent's work on a claim."""

    step_id: int
    kind: StepKind
    content: str
    created_at: datetime


class Handler(BaseModel):
    """A claims handler."""

    handler_id: str
    name: str
    role: str
    can_approve_over_limit: bool


class Instructions(BaseModel):
    """The agent's instructions followed by the policy wording, in Markdown."""

    text: str


class StartClaim(BaseModel):
    """The thread the agent works a claim in."""

    thread_id: Text


class NewStep(BaseModel):
    """A step to record."""

    kind: StepKind
    content: str


class NewDecision(BaseModel):
    """A decision to record."""

    decision: DecisionKind
    payout: float
    section: Text
    reason: Text


class NewPayment(BaseModel):
    """A payment to make."""

    amount: float


class NewSignOff(BaseModel):
    """The handler who signs off."""

    handler_id: Text
