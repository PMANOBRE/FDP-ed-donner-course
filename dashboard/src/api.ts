export type Status =
  "waiting" | "in_progress" | "waiting_for_sign_off" | "decided";
export type DecisionKind = "approve" | "decline" | "refer";
export type StepKind = "tool_call" | "tool_result" | "message";

export interface ClaimSummary {
  claim_id: string;
  customer_name: string;
  claim_type: string;
  summary: string;
  amount_claimed: number;
  submitted_on: string;
  status: Status;
  decision: DecisionKind | null;
  payout: number | null;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface Decision {
  decision: DecisionKind;
  payout: number;
  section: string;
  reason: string;
  decided_at: string;
}

export interface Payment {
  amount: number;
  paid_at: string;
}

export interface SignOff {
  handler_id: string;
  handler_name: string;
  signed_off_at: string;
}

export interface Claim {
  claim_id: string;
  status: Status;
  thread_id: string | null;
  decision: Decision | null;
  payment: Payment | null;
  sign_off: SignOff | null;
  policy_id: string;
  customer_id: string;
  customer_name: string;
  claim_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: Item[];
  amount_claimed: number;
  documents: ClaimDocument[];
}

export interface Policy {
  policy_id: string;
  customer_id: string;
  plan: string;
  plan_name: string;
  add_ons: string[];
  purchased_on: string;
  sold_through: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
  status: string;
}

export interface EarlierClaim {
  claim_id: string;
  filed_on: string;
  incident_date: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface ClaimHistory {
  customer_id: string;
  name: string;
  customer_since: string;
  previous_claims: EarlierClaim[];
}

export interface Step {
  step_id: number;
  kind: StepKind;
  content: string;
  created_at: string;
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
  can_approve_over_limit: boolean;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = (await response.json()) as { detail?: unknown };
    const detail = typeof body.detail === "string" ? body.detail : "";
    throw new ApiError(response.status, detail || response.statusText);
  }
  return (await response.json()) as T;
}

export const listClaims = () => request<ClaimSummary[]>("/claims");
export const getClaim = (claimId: string) =>
  request<Claim>(`/claims/${claimId}`);
export const getPolicy = (policyId: string) =>
  request<Policy>(`/policies/${policyId}`);
export const getClaimHistory = (customerId: string) =>
  request<ClaimHistory>(`/customers/${customerId}/claims`);
export const getInstructions = () => request<{ text: string }>("/instructions");
