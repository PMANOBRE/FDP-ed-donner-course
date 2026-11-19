import { expect, test } from "@playwright/test";

test("the queue lists the 25 claims", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(26);
});

test("a claim opens from the queue", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL(/#\/claims\/CLM-1001$/);
  await expect(page.getByRole("heading", { name: "CLM-1001" })).toBeVisible();
  await expect(page.getByText(/My flight home from Rome/)).toBeVisible();
});

test("the header opens the instructions", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Instructions" }).click();
  await expect(page).toHaveURL(/#\/instructions$/);
  await expect(
    page.getByRole("heading", { name: "The UnderCover Agent" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "10. How we work out your payment" }),
  ).toBeVisible();
});

test("an unknown claim is not found", async ({ page }) => {
  await page.goto("/#/claims/CLM-9999");
  await expect(
    page.getByRole("heading", { name: "Claim not found" }),
  ).toBeVisible();
});
