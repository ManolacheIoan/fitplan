import { defineConfig, devices } from "@playwright/test";

// Starts the FastAPI backend and the Next.js dev server (whose /api rewrite mirrors the
// Netlify proxy). The backend needs a migrated and seeded database (see README).
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    ...devices["Pixel 7"],
  },
  webServer: [
    {
      command: process.env.E2E_BACKEND_CMD ?? ".venv/bin/uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/api/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev -- --port 3000",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
