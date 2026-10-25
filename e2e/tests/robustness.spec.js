// Keyboard play, screen-reader announcements, layout on a phone, and the site under bad conditions.
import { test, expect, openGame, playSet, guess } from "./helpers.js";

test("a whole set can be played with the keyboard alone", async ({ page }) => {
  await openGame(page);
  for (let k = 0; k < 5; k++) {
    await page.locator("#choices .choice").first().focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#reveal")).toBeVisible();
    await expect(page.locator("#next")).toBeFocused();
    await page.keyboard.press("Enter");
    if (k < 4) {
      await expect(page.locator("#m-no")).toHaveText(`Story ${k + 2} of 5`);
      await expect(page.locator("#m-theme")).toBeFocused();
    }
  }
  await expect(page.locator("#results")).toBeVisible();
  await expect(page.locator("#results-title")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});

test("each guess is announced to screen readers, and cleared for the next story", async ({ page }) => {
  await openGame(page);
  await expect(page.locator("#announce")).toHaveAttribute("role", "status");
  const g = await guess(page, false);
  await expect(page.locator("#announce")).toHaveText(/^Not \w+\. Written by \w+\.$/);
  await page.click("#next");
  await expect(page.locator("#announce")).toHaveText("");
  expect(g.pick).not.toBe(g.answer);
});

test("choice buttons are named by what they show, and progress is announced", async ({ page }) => {
  await openGame(page);
  // Phones hide the lab line to save space, so the name is the model alone there.
  await expect(page.getByRole("button", { name: /^Claude( Anthropic)?$/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /^MiMo( Xiaomi)?$/ })).toBeVisible();
  await expect(page.locator("#pips")).toHaveAttribute("aria-label", "Story 1 of 5: 0 right, 0 wrong");
  await guess(page, false);
  await expect(page.locator("#pips")).toHaveAttribute("aria-label", "Story 1 of 5: 0 right, 1 wrong");
});

test("no view scrolls sideways", async ({ page }) => {
  await openGame(page);
  await guess(page, true);
  for (const v of ["play", "compare", "control", "findings", "about"]) {
    await page.click(`nav a[data-view="${v}"]`);
    if (v === "findings") await page.click(".method summary");
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(over, `${v} overflows by ${over}px`).toBeLessThanOrEqual(0);
  }
});

test("tap targets for the choices are big enough on a phone", async ({ page }, info) => {
  test.skip(info.project.name !== "phone");
  await openGame(page);
  const boxes = await page.locator("#choices .choice").evaluateAll(bs => bs.map(b => b.getBoundingClientRect().height));
  for (const h of boxes) expect(h).toBeGreaterThanOrEqual(44);
});

test.describe("with reduced motion", () => {
  test.use({ reducedMotion: "reduce" });
  test("the game still plays through", async ({ page }) => {
    await openGame(page);
    await playSet(page);
    await expect(page.locator("#score")).toBeVisible();
  });
});

test.describe("with browser storage blocked (some private modes)", () => {
  test.use({
    initScripts: [() => {
      const deny = () => { throw new DOMException("blocked", "SecurityError"); };
      Object.defineProperty(window, "localStorage", { get: deny, configurable: true });
    }]
  });
  test("a set can still be played and shared", async ({ page, api }) => {
    await page.goto("/#play");
    for (let k = 0; k < 5; k++) {
      await expect(page.locator("#m-no")).toHaveText(`Story ${k + 1} of 5`);
      await expect(page.locator("#reveal")).toBeHidden();
      await page.locator("#choices .choice").first().click();
      await expect(page.locator("#reveal")).toBeVisible();
      await page.click("#next");
    }
    await expect(page.locator("#results")).toBeVisible();
    await expect(page.locator("#share-text")).toContainText("/5");
    expect(api.guesses()).toHaveLength(5);
  });
});

test.describe("when the guess API is down", () => {
  test.use({ allowErrors: true });
  test("the game carries on without showing an error", async ({ page, errors }) => {
    await page.route("http://127.0.0.1:8787/**", r => r.abort());
    await openGame(page);
    await playSet(page);
    await expect(page.locator("#score")).toBeVisible();
    await expect(page.locator("#players")).toBeHidden();
    expect(errors.filter(e => e.startsWith("pageerror"))).toEqual([]);
  });
});

test.describe("when the round data can't load", () => {
  test.use({ allowErrors: true });
  test("the placeholder demo still works and records nothing", async ({ page, api, errors }) => {
    await page.route("**/data/R0.json", r => r.fulfill({ status: 500, body: "" }));
    await page.goto("/#play");
    await expect(page.locator(".demo-note")).toContainText("Demo");
    await expect(page.locator("#notice")).toBeHidden();
    for (let k = 0; k < 5; k++) {
      await page.locator("#choices .choice").first().click();
      await page.click("#next");
    }
    await expect(page.locator("#results")).toBeVisible();
    expect(api.guesses()).toHaveLength(0);
    expect(errors.filter(e => e.startsWith("pageerror"))).toEqual([]);
  });
});

test("dark mode keeps the story readable", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await openGame(page);
  const [fg, bg] = await page.locator("#story p").first().evaluate(p => {
    const c = getComputedStyle(p).color;
    let el = p, b = "rgba(0, 0, 0, 0)";
    while (el && (b === "rgba(0, 0, 0, 0)" || b === "transparent")) { b = getComputedStyle(el).backgroundColor; el = el.parentElement; }
    return [c, b];
  });
  const lum = s => { const [r, g, b] = s.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
  expect((a + 0.05) / (b + 0.05)).toBeGreaterThan(7);
});
