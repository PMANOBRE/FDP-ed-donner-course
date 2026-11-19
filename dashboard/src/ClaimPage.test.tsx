import { act, cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Claim, Step } from "./api";
import { ClaimPage } from "./ClaimPage";
import { REFRESH_MS } from "./useData";
import {
  claim,
  claimRoutes,
  history,
  json,
  policy,
  stubFetch,
} from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the claim in full", async () => {
  stubFetch(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1002" />);
  expect(
    await screen.findByRole("heading", { name: "CLM-1002" }),
  ).toBeDefined();
  expect(
    screen.getByText("My suitcase never arrived in Prague."),
  ).toBeDefined();
  expect(screen.getByText("Waiting")).toBeDefined();
  expect(screen.getByText("Jun 21, 2026, Frankfurt, Germany")).toBeDefined();
});

it("shows the items with their total", async () => {
  stubFetch(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1002" />);
  const items = await screen.findByRole("table");
  expect(within(items).getAllByRole("row")).toHaveLength(4);
  expect(
    within(items).getByRole("row", { name: "Total $1,150.00" }),
  ).toBeDefined();
});

it("shows the documents with their text", async () => {
  stubFetch(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1002" />);
  expect(
    await screen.findByText("Northwind Airlines lost baggage report"),
  ).toBeDefined();
  expect(screen.getByText("Carrier report")).toBeDefined();
  expect(
    screen.getByText("One checked bag, tag NW 771204, not delivered."),
  ).toBeDefined();
});

it("shows the policy", async () => {
  stubFetch(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1002" />);
  expect(await screen.findByText("UnderCover Premium")).toBeDefined();
  expect(screen.getByText("Electronics plus")).toBeDefined();
  expect(screen.getByText("May 2, 2026")).toBeDefined();
  expect(
    screen.getByText("Prague, Czech Republic, Jun 20, 2026 to Jul 1, 2026"),
  ).toBeDefined();
  expect(screen.getByText("$2,400.00")).toBeDefined();
  expect(screen.getByText("Tom Becker, Ana Becker")).toBeDefined();
});

it("shows a policy with no add-ons", async () => {
  stubFetch({
    ...claimRoutes(claim),
    "/api/policies/POL-2002": { ...policy, add_ons: [] },
  });
  render(<ClaimPage claimId="CLM-1002" />);
  expect(await screen.findByText("None")).toBeDefined();
});

it("shows the customer's earlier claims", async () => {
  stubFetch(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1002" />);
  expect(await screen.findByText("CLM-0377")).toBeDefined();
  expect(screen.getByText(/Snowstorm delay in Denver/)).toBeDefined();
  expect(screen.getByText("$180.00")).toBeDefined();
});

it("says when the customer has no earlier claims", async () => {
  stubFetch({
    ...claimRoutes(claim),
    "/api/customers/CUS-3002/claims": { ...history, previous_claims: [] },
  });
  render(<ClaimPage claimId="CLM-1002" />);
  expect(await screen.findByText("No earlier claims.")).toBeDefined();
});

it("says when the claim doesn't exist", async () => {
  stubFetch({});
  render(<ClaimPage claimId="CLM-9999" />);
  expect(
    await screen.findByRole("heading", { name: "Claim not found" }),
  ).toBeDefined();
});

describe("refreshing", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the agent's work as it happens, without a reload", async () => {
    let current: Claim = { ...claim, status: "in_progress", thread_id: "t-1" };
    let currentSteps: Step[] = [];
    stubFetch({
      ...claimRoutes(claim),
      "/api/claims/CLM-1002": () => json(current),
      "/api/claims/CLM-1002/steps": () => json(currentSteps),
    });
    render(<ClaimPage claimId="CLM-1002" />);
    expect(await screen.findByText("In progress")).toBeDefined();
    expect(screen.getByText("Starting work…")).toBeDefined();

    currentSteps = [
      {
        step_id: 1,
        kind: "tool_call",
        content: 'get_claim {"claim_id": "CLM-1002"}',
        created_at: "2026-11-19T10:00:00Z",
      },
    ];
    await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));
    expect(screen.getByText("get_claim")).toBeDefined();

    current = {
      ...current,
      status: "decided",
      decision: {
        decision: "approve",
        payout: 750,
        section: "5. Baggage and Personal Effects",
        reason: "Covered after the carrier's payment.",
        decided_at: "2026-11-19T10:00:10Z",
      },
      payment: { amount: 750, paid_at: "2026-11-19T10:00:11Z" },
    };
    await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));
    expect(screen.getByText("Decided", { selector: ".badge" })).toBeDefined();
    expect(screen.getByText("Approved")).toBeDefined();
    expect(screen.getByText("Paid $750.00")).toBeDefined();
  });

  it("stops refreshing a claim that doesn't exist", async () => {
    const fetch = stubFetch({});
    render(<ClaimPage claimId="CLM-9999" />);
    await screen.findByRole("heading", { name: "Claim not found" });
    const calls = fetch.mock.calls.length;
    await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS * 3));
    expect(fetch.mock.calls).toHaveLength(calls);
  });

  it("keeps trying after an error", async () => {
    let fail = true;
    stubFetch({
      ...claimRoutes(claim),
      "/api/claims/CLM-1002": () =>
        fail ? json({ detail: "Database is locked" }, 500) : json(claim),
    });
    render(<ClaimPage claimId="CLM-1002" />);
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Database is locked",
    );
    fail = false;
    await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));
    expect(screen.getByRole("heading", { name: "CLM-1002" })).toBeDefined();
  });
});
