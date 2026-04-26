import { test, expect } from "@playwright/test";

test.describe("Auth flow", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("body")).toContainText(/entrar|login/i);
  });

  test("unauthenticated user is redirected from protected route", async ({ page }) => {
    await page.goto("/emission/workspace");
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
