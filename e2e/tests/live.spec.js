// Read-only checks of the live site after each deploy. Run with LIVE=1. Never guesses, so no research data is
// written; Plausible is blocked by the shared set-up, so these visits aren't counted either.
import { test, expect } from "./helpers.js";

const API = "https://narratedself-api.airiskpractice.org";

test("the live game loads real stories with no errors", async ({ page }) => {
  await page.goto("/#play");
  await expect(page.locator("#choices .choice")).toHaveCount(5);
  await expect(page.locator(".demo-note")).toContainText("real model outputs");
  await expect(page.locator("#story p").first()).not.toBeEmpty();
  await expect(page.locator("#reveal")).toBeHidden();
  await expect(page.locator("#notice")).toBeVisible();
});

test("every view opens on the live site", async ({ page }) => {
  await page.goto("/");
  for (const v of ["compare", "control", "findings", "about"]) {
    await page.click(`nav a[data-view="${v}"]`);
    await expect(page.locator(`#view-${v}`)).toBeVisible();
  }
});

test("share preview, search files and the 404 page are in place", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute("content", "https://narratedself.airiskpractice.org/og.png");
  for (const path of ["/og.png", "/robots.txt", "/sitemap.xml", "/llms.txt", "/data/R0.json", "/analytics.js", "/app.js"]) {
    const r = await request.get(path);
    expect(r.status(), path).toBe(200);
  }
  expect((await request.get("/no-such-page")).status()).toBe(404);
});

test("the guess API answers and rejects a bad guess without storing it", async ({ request }) => {
  const stats = await request.get(`${API}/stats?round=R0`);
  expect(stats.status()).toBe(200);
  expect(await stats.json()).toMatchObject({ round: "R0" });
  const bad = await request.post(`${API}/guess`, { data: {} });
  expect(bad.status()).toBe(400);
});
