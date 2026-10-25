// Screenshots of every view and game state for a person to look over. Only runs with SHOTS=1; saved in e2e/shots/.
import { test, openGame, guess } from "./helpers.js";

test.skip(!process.env.SHOTS, "set SHOTS=1 to take screenshots");

for (const scheme of ["light", "dark"]) {
  test(`all views, ${scheme}`, async ({ page }, info) => {
    await page.emulateMedia({ colorScheme: scheme });
    const shot = name => page.screenshot({ path: `shots/${info.project.name}-${scheme}-${name}.png`, fullPage: true });
    await openGame(page);
    await shot("1-story");
    await guess(page, false);
    await shot("2-reveal");
    for (let k = 1; k < 5; k++) {
      await page.click("#next");
      await guess(page, k % 2 === 0);
    }
    await page.click("#next");
    await page.locator("#results").waitFor();
    await shot("3-score");
    for (const v of ["compare", "control", "findings", "about"]) {
      await page.click(`nav a[data-view="${v}"]`);
      if (v === "findings") await page.click(".method summary");
      await page.waitForTimeout(300);
      await shot(`4-${v}`);
    }
  });
}
