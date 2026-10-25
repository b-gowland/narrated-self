// Layout under worst-case conditions: the narrowest common phone (320px) and a wide fallback font (as on Linux,
// or when the web fonts fail to load). Every story in the quiz pool is shown, before and after its reveal.
import { test, expect, ROUND, STATE_KEY } from "./helpers.js";

const WIDE_FONT = () => document.addEventListener("DOMContentLoaded", () => {
  const s = document.createElement("style");
  s.textContent = "*{font-family:Verdana,'DejaVu Sans',sans-serif !important}";
  document.head.append(s);
});
const overflow = page => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);

test.describe("narrow phone, wide font", () => {
  test.use({ viewport: { width: 320, height: 640 }, initScripts: [WIDE_FONT] });

  test("no quiz story or its reveal pushes the page sideways", async ({ page }, info) => {
    test.skip(info.project.name !== "phone", "layout sweep runs once");
    test.setTimeout(300000);
    const pool = ROUND.stories.filter(s => ROUND.quiz.conditions.includes(s.cond) && s.words >= ROUND.quiz.min_words);
    await page.goto("/#play");
    for (let k = 0; k < pool.length; k += 5) {
      const set = pool.slice(k, k + 5).map(s => s.id);
      while (set.length < 5) set.push(pool[0].id);
      for (let i = 0; i < set.length; i++) {
        await page.evaluate(([key, set, i]) => localStorage.setItem(key, JSON.stringify(
          { set, set_id: crypto.randomUUID(), first: false, n: 2, counted: false, i, results: [], guesses: [] })), [STATE_KEY, set, i]);
        await page.reload();
        await page.locator("#choices .choice").first().waitFor();
        expect(await overflow(page), `${set[i]} story`).toBeLessThanOrEqual(0);
        await page.locator("#choices .choice").last().click();
        expect(await overflow(page), `${set[i]} reveal`).toBeLessThanOrEqual(0);
      }
    }
  });

  test("no view or score page pushes the page sideways", async ({ page }) => {
    await page.goto("/#play");
    for (let k = 0; k < 5; k++) {
      await page.locator("#choices .choice").first().click();
      await page.click("#next");
    }
    await expect(page.locator("#results")).toBeVisible();
    expect(await overflow(page), "score page").toBeLessThanOrEqual(0);
    for (const v of ["compare", "control", "findings", "about"]) {
      await page.click(`nav a[data-view="${v}"]`);
      if (v === "findings") await page.click(".method summary");
      expect(await overflow(page), v).toBeLessThanOrEqual(0);
    }
  });
});
