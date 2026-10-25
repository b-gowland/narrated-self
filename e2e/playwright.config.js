// Browser tests for the static site. Run from e2e/: npm test (first time: npm ci && npx playwright install chromium).
import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;

export default defineConfig({
  testDir: "tests",
  // LIVE=1 runs only the read-only checks of the live site; otherwise everything else, against a local copy.
  testMatch: process.env.LIVE ? "live.spec.js" : "*.spec.js",
  testIgnore: process.env.LIVE ? undefined : "live.spec.js",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    // "localhost" makes the site use its local API address, which the tests intercept.
    baseURL: process.env.LIVE ? "https://narratedself.airiskpractice.org" : `http://localhost:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects: [
    { name: "phone", use: { ...devices["Pixel 7"] } },
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } } }
  ],
  webServer: process.env.LIVE ? undefined : {
    command: "node serve.mjs",
    url: `http://localhost:${PORT}/`,
    env: { PORT: String(PORT) },
    reuseExistingServer: !process.env.CI
  }
});
