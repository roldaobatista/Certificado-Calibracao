import { test, expect } from "@playwright/test";

test.describe("Public certificate verification", () => {
  test("public verification page renders", async ({ page }) => {
    await page.goto("/verify");
    await expect(page.locator("body")).toBeVisible();
  });

  test("invalid token shows not-found state", async ({ page }) => {
    await page.goto("/verify/invalid-token-123");
    await expect(page.locator("body")).toContainText(/não encontrado|not found|inválido/i);
  });
});
