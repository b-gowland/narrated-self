// Navigation between views, the back button, the two reading views, Findings, About and the 404 page.
import { test, expect, openGame, guess, storyById, ROUND } from "./helpers.js";

const VIEWS = ["play", "compare", "control", "findings", "about"];
const visibleViews = page => page.locator("section.view:visible");

test("each menu link shows only its view and marks it current", async ({ page }) => {
  await openGame(page);
  for (const v of VIEWS) {
    await page.click(`nav a[data-view="${v}"]`);
    await expect(visibleViews(page)).toHaveCount(1);
    await expect(page.locator(`#view-${v}`)).toBeVisible();
    await expect(page.locator(`nav a[data-view="${v}"]`)).toHaveAttribute("aria-current", "page");
    await expect(page.locator("nav a[aria-current]")).toHaveCount(1);
    expect(new URL(page.url()).hash).toBe(`#${v}`);
  }
});

test("direct links open the right view, and unknown ones open the game", async ({ page }) => {
  for (const v of VIEWS) {
    await page.goto(`/#${v}`);
    await expect(page.locator(`#view-${v}`)).toBeVisible();
    await expect(visibleViews(page)).toHaveCount(1);
  }
  await page.goto("/index.html#nonsense"); // a fresh load; in-page anchors keep the current view by design
  await expect(page.locator("#view-play")).toBeVisible();
  await page.goto("/");
  await expect(page.locator("#view-play")).toBeVisible();
});

test("the back button returns to the previous view", async ({ page }) => {
  await openGame(page, "/");
  await page.click('nav a[data-view="findings"]');
  await page.click('nav a[data-view="about"]');
  await page.goBack();
  await expect(page.locator("#view-findings")).toBeVisible();
  await page.goBack();
  await expect(page.locator("#view-play")).toBeVisible();
  await page.goForward();
  await expect(page.locator("#view-findings")).toBeVisible();
});

test("the wordmark and the Findings play link go to the game", async ({ page }) => {
  await openGame(page);
  await page.click('nav a[data-view="about"]');
  await page.click(".wordmark");
  await expect(page.locator("#view-play")).toBeVisible();
  await page.click('nav a[data-view="findings"]');
  await page.click(".findings-play");
  await expect(page.locator("#view-play")).toBeVisible();
});

test("the skip link jumps to the game without breaking the view", async ({ page }) => {
  await openGame(page, "/#about");
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#view-about")).toBeVisible();
  await expect(visibleViews(page)).toHaveCount(1);
});

test("Interview vs story shows the chosen model's answer and story", async ({ page }) => {
  await page.goto("/#compare");
  await expect(page.locator("#cmp-model option")).toHaveCount(5);
  await expect(page.locator("#cmp-theme option")).toHaveCount(3);
  for (const m of ROUND.models) {
    for (const t of Object.keys(ROUND.prompts)) {
      await page.selectOption("#cmp-model", m.id);
      await page.selectOption("#cmp-theme", t);
      const d = ROUND.stories.find(s => s.model === m.id && s.theme === t && s.cond === "D" && s.sample === 1);
      const s1 = ROUND.stories.find(s => s.model === m.id && s.theme === t && s.cond === "S1" && s.sample === 1);
      // First words of the first paragraph, as the site displays it.
      const firstWords = txt => txt.replace(/\r/g, "").trim().split(/\n\s*\n/)[0].replace(/\[\[[^\]]+\]\]/g, " ")
        .replace(/[#*_]/g, "").trim().split(/\s+/).slice(0, 3).join(" ");
      await expect(page.locator("#cmp-d p").first()).toContainText(firstWords(d.text));
      await expect(page.locator("#cmp-s p").first()).toContainText(firstWords(s1.text));
      await expect(page.locator("#cmp-q")).toHaveText(`"${ROUND.prompts[t].D}"`);
      await expect(page.locator("#cmp-p")).toHaveText(`"${ROUND.prompts[t].S1}"`);
    }
  }
});

test("the link from a reveal opens Interview vs story for that model and theme", async ({ page }) => {
  await openGame(page);
  const g = await guess(page, true);
  const s = await page.evaluate(() => JSON.parse(localStorage.getItem("tns-R0-live-v5")));
  await page.click("#to-interview");
  await expect(page.locator("#view-compare")).toBeVisible();
  await expect(page.locator("#cmp-model")).toHaveValue(g.answer);
  await expect(page.locator("#cmp-theme")).toHaveValue(storyById[s.set[0]].theme);
  await page.goBack();
  await expect(page.locator("#view-play")).toBeVisible();
  await expect(page.locator("#reveal")).toBeVisible();
});

test("AI vs robot arm pairs an AI story with a robot-arm story from the same model", async ({ page }) => {
  await page.goto("/#control");
  for (let k = 0; k < 5; k++) {
    const books = page.locator("#ctl-pair .book");
    await expect(books).toHaveCount(2);
    await expect(books.nth(0).locator("h2")).toHaveText("About an AI like itself");
    await expect(books.nth(1).locator("h2")).toHaveText("About a 1980s robot arm");
    const label = await books.nth(0).locator(".cover-top span").textContent();
    expect(label).toBe(await books.nth(1).locator(".cover-top span").textContent());
    expect(label).toMatch(/written by (Claude|GPT|Gemini|Grok|MiMo)$/);
    await expect(books.nth(1).locator(".story p").first()).not.toBeEmpty();
    await page.click("#ctl-next");
  }
});

test("Findings charts load and the method section opens with spaced paragraphs", async ({ page }) => {
  await page.goto("/#findings");
  await page.click(".method summary");
  const imgs = page.locator("#view-findings img");
  await expect(imgs).toHaveCount(2);
  for (let k = 0; k < 2; k++) {
    await imgs.nth(k).scrollIntoViewIfNeeded();
    await expect.poll(() => imgs.nth(k).evaluate(i => i.complete && i.naturalWidth)).toBeGreaterThan(0);
    expect((await imgs.nth(k).getAttribute("alt")).length).toBeGreaterThan(40);
  }
  const gap = await page.locator(".method p").nth(1).evaluate(p => parseFloat(getComputedStyle(p).marginTop));
  expect(gap).toBeGreaterThan(8);
});

test("About has the guess details, the FAQ and working in-page structure", async ({ page }) => {
  await page.goto("/#about");
  await expect(page.locator("#your-guesses")).toBeVisible();
  await expect(page.locator("#view-about")).toContainText("Plausible");
  await expect(page.locator("#faq")).toBeVisible();
  const external = page.locator("#view-about a[href^='http']");
  expect(await external.count()).toBeGreaterThan(5);
});

test.describe("404", () => {
test.use({ allowErrors: true }); // the browser logs the expected 404 response
test("an unknown page shows the 404 page with a way back", async ({ page, errors }) => {
  const r = await page.goto("/no-such-page");
  expect(r.status()).toBe(404);
  await expect(page.locator("h1")).toHaveText("Page not found");
  await page.click("text=Play The Narrated Self");
  await expect(page.locator("#view-play")).toBeVisible();
  expect(errors.filter(e => !/status of 404/.test(e))).toEqual([]);
});
});
