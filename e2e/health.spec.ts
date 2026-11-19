import { expect, test } from "@playwright/test";

test("the dashboard shows the backend is up", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Backend: up")).toBeVisible();
});

test("the e2e backend has its own seeded queue", async ({ request }) => {
  const response = await request.get("/api/claims");
  expect(response.ok()).toBe(true);
  expect(await response.json()).toHaveLength(25);
});
