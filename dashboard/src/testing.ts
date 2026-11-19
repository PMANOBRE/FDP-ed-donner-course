import { vi } from "vitest";
import type {
  Claim,
  ClaimHistory,
  ClaimSummary,
  Handler,
  Policy,
  Step,
} from "./api";

export function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * Stub fetch with replies keyed by "METHOD /api/path", or by path for GET.
 * A function reply is called each time; anything else is sent as JSON.
 * Paths with no reply get a 404.
 */
export function stubFetch(routes: Record<string, unknown>) {
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    const route = routes[`${method} ${url}`] ?? routes[url];
    if (route === undefined) {
      return Promise.resolve(json({ detail: `No ${method} ${url}` }, 404));
    }
    return Promise.resolve(
      typeof route === "function" ? (route as () => Response)() : json(route),
    );
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

export const summary: ClaimSummary = {
  claim_id: "CLM-1002",
  customer_name: "Tom Becker",
  claim_type: "baggage",
  summary: "Suitcase lost on a connecting flight",
  amount_claimed: 1150,
  submitted_on: "2026-07-20",
  status: "waiting",
  decision: null,
  payout: null,
};

export const claim: Claim = {
  claim_id: "CLM-1002",
  status: "waiting",
  thread_id: null,
  decision: null,
  payment: null,
  sign_off: null,
  policy_id: "POL-2002",
  customer_id: "CUS-3002",
  customer_name: "Tom Becker",
  claim_type: "baggage",
  submitted_on: "2026-07-20",
  incident_date: "2026-06-21",
  incident_location: "Frankfurt, Germany",
  summary: "Suitcase lost on a connecting flight",
  story: "My suitcase never arrived in Prague.",
  items: [
    { description: "Hard-shell suitcase", category: "luggage", amount: 280 },
    { description: "Wool suit", category: "clothing", amount: 870 },
  ],
  amount_claimed: 1150,
  documents: [
    {
      name: "Northwind Airlines lost baggage report",
      type: "carrier_report",
      content: "One checked bag, tag NW 771204, not delivered.",
    },
  ],
};

export const policy: Policy = {
  policy_id: "POL-2002",
  customer_id: "CUS-3002",
  plan: "premium",
  plan_name: "UnderCover Premium",
  add_ons: ["electronics_plus"],
  purchased_on: "2026-05-02",
  sold_through: "Northwind Airlines checkout",
  trip: {
    destination: "Prague, Czech Republic",
    departs_on: "2026-06-20",
    returns_on: "2026-07-01",
    trip_cost: 2400,
  },
  travelers: ["Tom Becker", "Ana Becker"],
  status: "active",
};

export const history: ClaimHistory = {
  customer_id: "CUS-3002",
  name: "Tom Becker",
  customer_since: "2022-01-15",
  previous_claims: [
    {
      claim_id: "CLM-0377",
      filed_on: "2025-03-02",
      incident_date: "2025-02-20",
      claim_type: "trip_delay",
      summary: "Snowstorm delay in Denver",
      outcome: "approved",
      amount_paid: 180,
    },
  ],
};

export const handlers: Handler[] = [
  {
    handler_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Claims Handler",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-03",
    name: "Priya Raman",
    role: "Claims Handler",
    can_approve_over_limit: true,
  },
];

export const steps: Step[] = [];

/** The routes the claim page reads, for the claim given. */
export function claimRoutes(current: Claim) {
  return {
    [`/api/claims/${current.claim_id}`]: current,
    [`/api/claims/${current.claim_id}/steps`]: steps,
    [`/api/policies/${current.policy_id}`]: policy,
    [`/api/customers/${current.customer_id}/claims`]: history,
    "/api/handlers": handlers,
  };
}
