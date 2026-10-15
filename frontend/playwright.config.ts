import { defineConfig, devices } from "@playwright/test";

// E2E runs against its own servers (backend :8001, Next.js :3001 with a separate build
// directory), never the ones used for development. The Next.js dev rewrite mirrors the
// Netlify /api proxy. The backend needs a migrated and seeded database (see README).
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 3001;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: "retain-on-failure",
    ...devices["Pixel 7"],
  },
  webServer: [
    {
      command: process.env.E2E_BACKEND_CMD ?? `.venv/bin/uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: "../backend",
      url: `http://localhost:${BACKEND_PORT}/api/health`,
      reuseExistingServer: false,
      env: {
        ALLOWED_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
        // Several accounts are created per run; rate limiting itself is covered by pytest.
        LOGIN_RATE_LIMIT: "1000",
        // E2E never calls external services.
        FOOD_SOURCE: "none",
      },
    },
    {
      command: `npm run dev -- --port ${FRONTEND_PORT}`,
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: false,
      env: { DEV_API_URL: `http://localhost:${BACKEND_PORT}`, NEXT_DIST_DIR: ".next-e2e" },
    },
  ],
});
