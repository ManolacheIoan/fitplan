import { expect, test } from "@playwright/test";

// Simulates a sleeping free-tier backend: the proxy answers 503 until the instance is up.
test("shows a wake-up banner and retries while the backend starts", async ({ page }) => {
  let healthCalls = 0;
  await page.route("**/api/health", async (route) => {
    healthCalls += 1;
    if (healthCalls <= 2) await route.fulfill({ status: 503, body: "starting" });
    else await route.continue();
  });

  await page.goto("/azi");
  await expect(page.getByText(/Serverul pornește/)).toBeVisible();
  // Once healthy, the request goes through: unauthenticated users land on the login page.
  await expect(page).toHaveURL(/\/autentificare/, { timeout: 15_000 });
  await expect(page.getByText(/Serverul pornește/)).toBeHidden();
  expect(healthCalls).toBe(3);
});
