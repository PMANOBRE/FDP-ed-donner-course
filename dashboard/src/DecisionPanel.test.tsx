import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Claim, Decision } from "./api";
import { DecisionPanel } from "./DecisionPanel";
import { claim, handlers, json, stubFetch } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const approval: Decision = {
  decision: "approve",
  payout: 420,
  section: "3. Trip Delay",
  reason: "The delay was covered. Every expense has a receipt.",
  decided_at: "2026-11-19T10:00:00Z",
};
const paid = { amount: 420, paid_at: "2026-11-19T10:00:05Z" };
const held: Claim = {
  ...claim,
  status: "waiting_for_sign_off",
  decision: { ...approval, payout: 1350 },
};

function show(current: Claim, onSignedOff = vi.fn()) {
  render(<DecisionPanel claim={current} onSignedOff={onSignedOff} />);
  return onSignedOff;
}

it("says when the claim is waiting", () => {
  show(claim);
  expect(screen.getByText("Not decided yet.")).toBeDefined();
});

it("says when the agent is working", () => {
  show({ ...claim, status: "in_progress" });
  expect(screen.getByText("The agent is working on this claim.")).toBeDefined();
});

it("shows a paid approval with its payout, section and reason", () => {
  show({ ...claim, status: "decided", decision: approval, payment: paid });
  expect(screen.getByText("Approved")).toBeDefined();
  expect(screen.getByText("$420.00")).toBeDefined();
  expect(screen.getByText("3. Trip Delay")).toBeDefined();
  expect(screen.getByText(approval.reason)).toBeDefined();
  expect(screen.getByText("Paid $420.00")).toBeDefined();
});

it("shows an approval that isn't paid yet", () => {
  show({ ...claim, status: "decided", decision: approval });
  expect(screen.getByText("Approved, not paid yet.")).toBeDefined();
});

it("shows who signed off a payment", () => {
  show({
    ...held,
    status: "decided",
    payment: { amount: 1350, paid_at: "2026-11-19T11:00:00Z" },
    sign_off: {
      handler_id: "HND-01",
      handler_name: "Dana Whitfield",
      signed_off_at: "2026-11-19T11:00:00Z",
    },
  });
  expect(
    screen.getByText("Paid $1,350.00, signed off by Dana Whitfield"),
  ).toBeDefined();
});

it.each([
  ["decline", "Declined"],
  ["refer", "Referred"],
] as const)("shows a %s with no payment", (kind, label) => {
  show({
    ...claim,
    status: "decided",
    decision: { ...approval, decision: kind, payout: 0, reason: "No cover." },
  });
  expect(screen.getByText(label)).toBeDefined();
  expect(screen.getByText("No cover.")).toBeDefined();
  expect(screen.getByText("No payment.")).toBeDefined();
});

it("signs off a held payment", async () => {
  const fetch = stubFetch({
    "/api/handlers": [
      ...handlers,
      {
        ...handlers[0],
        handler_id: "HND-09",
        name: "New Starter",
        can_approve_over_limit: false,
      },
    ],
    "POST /api/claims/CLM-1002/sign-off": { ...held, status: "decided" },
  });
  const onSignedOff = show(held);
  expect(
    screen.getByText("The payment is held until a handler signs it off."),
  ).toBeDefined();
  const button = screen.getByRole("button", { name: "Sign off" });
  expect(button).toHaveProperty("disabled", true);
  await screen.findByRole("option", { name: "Dana Whitfield" });
  expect(screen.queryByRole("option", { name: "New Starter" })).toBeNull();
  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(button);
  await vi.waitFor(() => {
    expect(onSignedOff).toHaveBeenCalledOnce();
  });
  expect(fetch).toHaveBeenCalledWith("/api/claims/CLM-1002/sign-off", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handler_id: "HND-01" }),
  });
});

it("shows the backend's error when a sign-off is refused", async () => {
  stubFetch({
    "/api/handlers": handlers,
    "POST /api/claims/CLM-1002/sign-off": () =>
      json(
        { detail: "Claim CLM-1002 is decided, not waiting for sign-off" },
        409,
      ),
  });
  const onSignedOff = show(held);
  await screen.findByRole("option", { name: "Priya Raman" });
  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-03" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign off" }));
  expect((await screen.findByRole("alert")).textContent).toBe(
    "Claim CLM-1002 is decided, not waiting for sign-off",
  );
  expect(onSignedOff).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Sign off" })).toHaveProperty(
    "disabled",
    false,
  );
});

it("falls back to the status when an error has no message", async () => {
  stubFetch({
    "/api/handlers": handlers,
    "POST /api/claims/CLM-1002/sign-off": () =>
      json({ detail: [{ msg: "Field required" }] }, 422),
  });
  show(held);
  await screen.findByRole("option", { name: "Dana Whitfield" });
  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign off" }));
  expect((await screen.findByRole("alert")).textContent).toBe(
    "The request failed with status 422",
  );
});
