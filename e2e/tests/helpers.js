// Shared set-up for the site tests: a stand-in API, a blocked Plausible, error capture and game helpers.
import { test as base, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

export const ROUND = JSON.parse(readFileSync(new URL("../../site/data/R0.json", import.meta.url), "utf8"));
export const STATE_KEY = "tns-R0-live-v5";
export const MODEL_IDS = ROUND.models.map(m => m.id);
export const MODEL_NAMES = ROUND.models.map(m => m.name);
export const storyById = Object.fromEntries(ROUND.stories.map(s => [s.id, s]));
const API = "http://127.0.0.1:8787";

// Every test gets: api.calls (what the site tried to send), events (Plausible calls) and errors (console, page and CSP).
export const test = base.extend({
  stats: [{ round: "R0", qualifying_guesses: 0, pooled_accuracy: null }, { option: true }],
  initScripts: [[], { option: true }],
  api: [async ({ page, stats }, use) => {
    const calls = [];
    await page.route(`${API}/**`, async route => {
      const req = route.request();
      const url = new URL(req.url());
      if (req.method() === "POST") {
        calls.push({ path: url.pathname, body: JSON.parse(req.postData() || "null") });
        await route.fulfill({ status: 201, contentType: "application/json", body: '{"ok":true}' });
      } else {
        calls.push({ path: url.pathname, query: Object.fromEntries(url.searchParams) });
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(stats) });
      }
    });
    // Plausible's script is replaced by nothing, so tracked events stay in window.plausible.q for the tests to read.
    await page.route("https://plausible.io/**", route =>
      route.request().resourceType() === "script"
        ? route.fulfill({ status: 200, contentType: "text/javascript", body: "" })
        : route.fulfill({ status: 202, body: "ok" }));
    await page.route(/fonts\.(googleapis|gstatic)\.com/, route => route.abort());
    await use({ calls, guesses: () => calls.filter(c => c.path === "/guess").map(c => c.body) });
  }, { auto: true }],
  // Every test fails on a script error or a blocked resource, unless it opts out.
  allowErrors: [false, { option: true }],
  errors: [async ({ page, initScripts, allowErrors }, use) => {
    const errors = [];
    page.on("pageerror", e => errors.push(`pageerror: ${e.message}`));
    page.on("console", m => {
      // Blocked web fonts are a test artefact, not a site error.
      if (m.type() === "error" && !/fonts\.g|ERR_FAILED/.test(m.text())) errors.push(`console: ${m.text()}`);
    });
    await page.addInitScript(() => {
      window.__csp = [];
      document.addEventListener("securitypolicyviolation", e => window.__csp.push(`${e.violatedDirective} ${e.blockedURI}`));
    });
    for (const s of initScripts) await page.addInitScript(s);
    await use(errors);
    if (!allowErrors) {
      const csp = page.url().startsWith("http") ? await page.evaluate(() => window.__csp || []).catch(() => []) : [];
      expect([...errors, ...csp.map(c => `csp: ${c}`)], "script errors or blocked resources").toEqual([]);
    }
  }, { auto: true }]
});
export { expect };

// Open the game with a clean device and wait for the first story.
export async function openGame(page, path = "/#play") {
  await page.goto(path);
  await expect(page.locator("#choices .choice")).toHaveCount(5);
}

export async function savedState(page) {
  return page.evaluate(k => JSON.parse(localStorage.getItem(k)), STATE_KEY);
}

// The model that wrote the story currently shown, read from the saved game and the round data.
export async function currentAnswer(page) {
  const s = await savedState(page);
  return storyById[s.set[s.i]].model;
}

export const wrongFor = answer => MODEL_IDS.find(m => m !== answer);

// Guess the current story, right or wrong on purpose. Returns the model guessed and the true answer.
export async function guess(page, right) {
  const answer = await currentAnswer(page);
  const pick = right ? answer : wrongFor(answer);
  await page.click(`#choice-${pick}`);
  return { pick, answer };
}

// Visible-state checks that catch a story starting with the last answer still showing.
export async function expectFreshStory(page, n) {
  await expect(page.locator("#m-no")).toHaveText(`Story ${n} of 5`);
  await expect(page.locator("#reveal")).toBeHidden();
  await expect(page.locator("#stamp")).toBeHidden();
  await expect(page.locator("#tray-label")).toHaveText("Who wrote it?");
  await expect(page.locator("#choices .choice:enabled")).toHaveCount(5);
  await expect(page.locator("#choices .is-answer, #choices .picked")).toHaveCount(0);
  await expect(page.locator("#story p").first()).toBeVisible();
}

// Play a whole set. pattern: true/false per story. Returns what was guessed.
export async function playSet(page, pattern = [true, false, true, false, false]) {
  const played = [];
  for (let k = 0; k < 5; k++) {
    await expectFreshStory(page, k + 1);
    played.push(await guess(page, pattern[k]));
    await expect(page.locator("#reveal")).toBeVisible();
    await page.click("#next");
  }
  await expect(page.locator("#results")).toBeVisible();
  return played;
}

export async function cspViolations(page) {
  return page.evaluate(() => window.__csp || []);
}
