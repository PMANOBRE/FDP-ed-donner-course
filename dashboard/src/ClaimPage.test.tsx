import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ClaimPage } from "./ClaimPage";
import { claim, claimRoutes, history, policy, stubFetch } from "./testing";

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
