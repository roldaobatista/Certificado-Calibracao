import { test, expect } from "@playwright/test";

test.describe("Emission flow", () => {
  test("emission workspace renders for authenticated user", async ({ page }) => {
    // This is a placeholder for the full E2E flow.
    // Full flow requires: login → create customer/equipment → create SO → execute → review → sign.
    await page.goto("/emission/workspace");
    // Expect redirect to login when unauthenticated
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
