import { expect, test, type APIRequestContext } from "@playwright/test";

// These tests stand in for the agent by calling the API, each on its own claim.

function post(request: APIRequestContext, path: string, data: object) {
  return request.post(`/api/claims/${path}`, { data });
}

test("the claim page shows the agent at work without a reload", async ({
  page,
  request,
}) => {
  await page.goto("/#/claims/CLM-1003");
  const status = page.locator(".title .badge");
  await expect(status).toHaveText("Waiting");
  await expect(page.getByText("Not decided yet.")).toBeVisible();

  expect(
    (await post(request, "CLM-1003/start", { thread_id: "e2e" })).ok(),
  ).toBe(true);
  await expect(status).toHaveText("In progress");
  await expect(
    page.getByText("The agent is working on this claim."),
  ).toBeVisible();

  await post(request, "CLM-1003/steps", {
    kind: "tool_call",
    content: 'get_claim {"claim_id": "CLM-1003"}',
  });
  await expect(page.getByText("Calls get_claim")).toBeVisible();

  await post(request, "CLM-1003/steps", {
    kind: "tool_result",
    content: 'get_claim {"claim_id": "CLM-1003", "status": "in_progress"}',
  });
  await expect(page.getByText("Result from get_claim")).toBeVisible();

  await post(request, "CLM-1003/steps", {
    kind: "message",
    content: "The fall is covered under section 7, less the deductible.",
  });
  await expect(
    page.getByText("The fall is covered under section 7, less the deductible."),
  ).toBeVisible();

  await post(request, "CLM-1003/decision", {
    decision: "approve",
    payout: 950,
    section: "7. Emergency Medical",
    reason: "The treatment was necessary. The deductible is taken off.",
  });
  await post(request, "CLM-1003/payment", { amount: 950 });
  await expect(status).toHaveText("Decided");
  await expect(page.getByText("Approved", { exact: true })).toBeVisible();
  await expect(page.getByText("Paid $950.00")).toBeVisible();
});

test("a handler signs off a payout over the limit", async ({
  page,
  request,
}) => {
  await post(request, "CLM-1020/start", { thread_id: "e2e" });
  await post(request, "CLM-1020/decision", {
    decision: "approve",
    payout: 1350,
    section: "5. Baggage and Personal Effects",
    reason: "The loss is covered. The payout is over the approval limit.",
  });
  const payment = await post(request, "CLM-1020/payment", { amount: 1350 });
  expect(payment.status()).toBe(403);
  expect(await payment.json()).toEqual({
    detail: "A payout over $1,000.00 needs a handler's sign-off",
  });

  await page.goto("/#/claims/CLM-1020");
  const status = page.locator(".title .badge");
  await expect(status).toHaveText("Waiting for sign-off");
  await page.getByLabel("Handler").selectOption({ label: "Dana Whitfield" });
  await page.getByRole("button", { name: "Sign off" }).click();
  await expect(status).toHaveText("Decided");
  await expect(
    page.getByText("Paid $1,350.00, signed off by Dana Whitfield"),
  ).toBeVisible();
});

const unpaid = [
  { claimId: "CLM-1004", decision: "decline", label: "Declined" },
  { claimId: "CLM-1005", decision: "refer", label: "Referred" },
];

for (const { claimId, decision, label } of unpaid) {
  test(`a claim marked ${label} shows its reason and no payment`, async ({
    page,
    request,
  }) => {
    const reason = `The claim is ${label.toLowerCase()} under the wording.`;
    await post(request, `${claimId}/start`, { thread_id: "e2e" });
    await post(request, `${claimId}/decision`, {
      decision,
      payout: 0,
      section: "11. How to claim",
      reason,
    });

    await page.goto(`/#/claims/${claimId}`);
    await expect(page.locator(".title .badge")).toHaveText("Decided");
    await expect(page.getByText(label, { exact: true })).toBeVisible();
    await expect(page.getByText(reason)).toBeVisible();
    await expect(page.getByText("No payment.")).toBeVisible();
  });
}
