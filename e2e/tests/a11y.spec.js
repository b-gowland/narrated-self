// Automated accessibility scan (axe) of every view and each game state, against WCAG 2.2 A and AA.
import AxeBuilder from "@axe-core/playwright";
import { test, expect, openGame, guess, playSet } from "./helpers.js";

async function scan(page, label) {
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
  const found = r.violations.map(v => `${label}: ${v.id} (${v.impact}) ${v.help} → ${v.nodes.slice(0, 3).map(n => n.target.join(" ")).join(" | ")}`);
  expect(found, found.join("\n")).toEqual([]);
}

for (const scheme of ["light", "dark"]) {
  test.describe(`${scheme} mode`, () => {
    // axe fetches the font stylesheet to inspect it, which the site's CSP rightly blocks; page errors still fail.
    test.use({ colorScheme: scheme, allowErrors: true });
    test.afterEach(async ({ errors }) => expect(errors.filter(e => e.startsWith("pageerror"))).toEqual([]));

    test("game: story, reveal and score page", async ({ page }) => {
      await openGame(page);
      await scan(page, "story");
      await guess(page, false);
      await scan(page, "reveal (wrong)");
      await page.click("#next");
      await guess(page, true);
      await scan(page, "reveal (right)");
    });

    test("score page", async ({ page }) => {
      await openGame(page);
      await playSet(page);
      await scan(page, "score");
    });

    for (const v of ["compare", "control", "findings", "about"]) {
      test(`${v} view`, async ({ page }) => {
        await page.goto(`/#${v}`);
        await expect(page.locator(`#view-${v}`)).toBeVisible();
        if (v === "findings") await page.click(".method summary");
        await scan(page, v);
      });
    }
  });
}
