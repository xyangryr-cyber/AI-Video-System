import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/e2e/playwright",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    actionTimeout: 10_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.CI
    ? undefined
    : [
        {
          command: "cd ../.. && docker compose -f docker-compose.dev.yml up -d",
          port: 3000,
          reuseExistingServer: true,
          timeout: 120_000,
        },
        {
          command: "cd ../.. && docker compose -f docker-compose.dev.yml up -d",
          port: 8000,
          reuseExistingServer: true,
          timeout: 120_000,
        },
      ],
});
