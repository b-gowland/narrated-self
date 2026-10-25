// Sharing a result: the phone share sheet, copying, and the select-text fallback.
import { test, expect, openGame, playSet, MODEL_NAMES } from "./helpers.js";

const events = page => page.evaluate(() => (window.plausible?.q || []).map(a => a[0]));

// Replace the browser's share and clipboard with recorders, or make them fail.
const mock = (share, clipboard) => [
  `(() => {
    window.__shared = []; window.__copied = [];
    const share = ${JSON.stringify(share)}, clip = ${JSON.stringify(clipboard)};
    if (share === "none") { try { delete Navigator.prototype.share; } catch {} Object.defineProperty(navigator, "share", { value: undefined, configurable: true }); }
    else Object.defineProperty(navigator, "share", { configurable: true, value: async d => {
      if (share === "abort") throw new DOMException("cancelled", "AbortError");
      if (share === "fail") throw new DOMException("no", "NotAllowedError");
      window.__shared.push(d.text);
    } });
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async t => {
      if (clip === "deny") throw new DOMException("denied", "NotAllowedError");
      window.__copied.push(t);
    } } });
  })();`
];

async function finish(page) {
  await openGame(page);
  await playSet(page, [true, false, true, true, false]);
  return page.locator("#share-text").textContent();
}

test.describe("with a share sheet", () => {
  test.use({ initScripts: mock("ok", "ok") });
  test("shares the result text", async ({ page }) => {
    const text = await finish(page);
    await page.click("#share");
    await expect(page.locator("#share-status")).toHaveText("Shared.");
    expect(await page.evaluate(() => window.__shared)).toEqual([text]);
    expect(await events(page)).toContain("Share");
  });
});

test.describe("when the share sheet is cancelled", () => {
  test.use({ initScripts: mock("abort", "ok") });
  test("does nothing else", async ({ page }) => {
    await finish(page);
    await page.click("#share");
    await expect(page.locator("#share-status")).toHaveText("");
    expect(await page.evaluate(() => window.__copied)).toEqual([]);
  });
});

test.describe("when the share sheet fails", () => {
  test.use({ initScripts: mock("fail", "ok") });
  test("falls back to copying", async ({ page }) => {
    const text = await finish(page);
    await page.click("#share");
    await expect(page.locator("#share-status")).toHaveText("Copied. Paste it anywhere.");
    expect(await page.evaluate(() => window.__copied)).toEqual([text]);
  });
});

test.describe("without a share sheet", () => {
  test.use({ initScripts: mock("none", "ok") });
  test("copies the result", async ({ page }) => {
    const text = await finish(page);
    await page.click("#share");
    await expect(page.locator("#share-status")).toHaveText("Copied. Paste it anywhere.");
    expect(await page.evaluate(() => window.__copied)).toEqual([text]);
  });
});

test.describe("with no share sheet and copying blocked", () => {
  test.use({ initScripts: mock("none", "deny") });
  test("selects the text so it can be copied by hand", async ({ page }) => {
    const text = await finish(page);
    await page.click("#share");
    await expect(page.locator("#share-status")).toContainText("Selected.");
    expect((await page.evaluate(() => getSelection().toString())).trim()).toBe(text.trim());
  });
});

test("the share text shows the score and gives nothing away", async ({ page }) => {
  const text = await finish(page);
  expect(text).toBe("THE NARRATED SELF · Round 0, set 1\n🟩⬛🟩🟩⬛ 3/5\nWho wrote this?");
  for (const n of MODEL_NAMES) expect(text).not.toContain(n);
});
