import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueuePage } from "./QueuePage";
import { json, stubFetch, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const decided = {
  ...summary,
  claim_id: "CLM-1001",
  customer_name: "Maya Patel",
  claim_type: "trip_delay",
  summary: "Flight home canceled",
  amount_claimed: 420,
  status: "decided",
  decision: "approve",
  payout: 420,
};

it("lists the claims with where each stands", async () => {
  stubFetch({ "/api/claims": [decided, summary] });
  render(<QueuePage />);
  const rows = await screen.findAllByRole("row");
  expect(rows).toHaveLength(3);
  const first = within(rows[1]);
  expect(first.getByRole("link", { name: "CLM-1001" })).toHaveProperty(
    "hash",
    "#/claims/CLM-1001",
  );
  expect(first.getByText("Maya Patel")).toBeDefined();
  expect(first.getByText("Trip delay")).toBeDefined();
  expect(first.getByText("Decided")).toBeDefined();
  expect(first.getByText("Approved")).toBeDefined();
  expect(first.getAllByText("$420.00")).toHaveLength(2);
  const second = within(rows[2]);
  expect(second.getByText("$1,150.00")).toBeDefined();
  expect(second.getByText("Jul 20, 2026")).toBeDefined();
  expect(second.getByText("Waiting")).toBeDefined();
});

it("counts the claims in each state", async () => {
  stubFetch({
    "/api/claims": [decided, summary, { ...summary, claim_id: "CLM-1003" }],
  });
  render(<QueuePage />);
  const counts = within(await screen.findByLabelText("Claims by state"));
  const tiles = counts.getAllByText(/^\d+$/).map((tile) => tile.textContent);
  expect(tiles).toEqual(["2", "0", "0", "1"]);
  expect(counts.getByText("Waiting for sign-off")).toBeDefined();
});

it("says when the backend can't be reached", async () => {
  stubFetch({
    "/api/claims": () => json({ detail: "Database is locked" }, 500),
  });
  render(<QueuePage />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Database is locked",
  );
});
