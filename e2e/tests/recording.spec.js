// What the site sends: guess records, the optional question, Plausible events, and the "Don't record my guesses" switch.
import { test, expect, openGame, playSet, guess, savedState, MODEL_IDS } from "./helpers.js";

const events = page => page.evaluate(() => (window.plausible?.q || []).map(a => a[0]));

test("each guess sends exactly the pre-registered fields", async ({ page, api }) => {
  await openGame(page);
  const s = await savedState(page);
  await playSet(page);
  const g = api.guesses();
  expect(g).toHaveLength(5);
  const device = await page.evaluate(() => JSON.parse(localStorage.getItem("tns-device")));
  g.forEach((x, k) => {
    expect(Object.keys(x).sort()).toEqual(
      ["device_id", "first_set", "guess", "ms_to_guess", "mode", "position", "round", "set_id", "story_id"].sort());
    expect(x).toMatchObject({ round: "R0", mode: "quiz", device_id: device, set_id: s.set_id, first_set: true, story_id: s.set[k], position: k + 1 });
    expect(MODEL_IDS).toContain(x.guess);
    expect(Number.isInteger(x.ms_to_guess) && x.ms_to_guess >= 0).toBe(true);
  });
});

test("the device ID stays the same across reloads and sets", async ({ page, api }) => {
  await openGame(page);
  await guess(page, true);
  await page.reload();
  await page.click("#next");
  await guess(page, true);
  const ids = new Set(api.guesses().map(x => x.device_id));
  expect(ids.size).toBe(1);
});

test("the notice explains recording and links to the details", async ({ page }) => {
  await openGame(page);
  await expect(page.locator("#notice")).toBeVisible();
  await expect(page.locator("#notice-text")).toContainText("recorded anonymously");
  await expect(page.locator("#optout")).toHaveText("Don't record my guesses");
  await expect(page.locator(".demo-note")).toContainText("guesses recorded anonymously for research");
  await page.click("#notice-link");
  await expect(page.locator("#view-about")).toBeVisible();
  await expect(page.locator("#your-guesses")).toBeInViewport();
});

test("opting out stops guesses, the question and Plausible, and survives a reload", async ({ page, api }) => {
  await openGame(page);
  await page.click("#optout");
  await expect(page.locator("#optout")).toHaveText("Record them again");
  await expect(page.locator("#notice-text")).toHaveText("Your guesses aren't being recorded on this device.");
  await expect(page.locator(".demo-note")).toContainText("your guesses aren't being recorded");
  await playSet(page);
  expect(api.guesses()).toHaveLength(0);
  expect(await events(page)).toEqual([]);
  await expect(page.locator("#ask")).toBeHidden();
  await page.reload();
  await expect(page.locator("#optout")).toHaveText("Record them again");
  expect(await page.evaluate(() => typeof window.plausible)).toBe("undefined");
  await page.click("#again");
  await guess(page, true);
  expect(api.calls.filter(c => c.path !== "/stats")).toHaveLength(0);
});

test("opting back in records again", async ({ page, api }) => {
  await openGame(page);
  await page.click("#optout");
  await guess(page, true);
  await page.click("#optout");
  await expect(page.locator("#optout")).toHaveText("Don't record my guesses");
  await page.click("#next");
  await guess(page, true);
  expect(api.guesses().map(x => x.position)).toEqual([2]);
});

test("opting out on the score page hides the question", async ({ page }) => {
  await openGame(page);
  await playSet(page);
  await expect(page.locator("#ask")).toBeVisible();
  await page.click("#optout");
  await expect(page.locator("#ask")).toBeHidden();
});

test("the optional question sends one answer, then stays away", async ({ page, api }) => {
  await openGame(page);
  await playSet(page);
  await expect(page.locator("#ask")).toBeVisible();
  await expect(page.locator("#ask-options button")).toHaveCount(9);
  const device = await page.evaluate(() => JSON.parse(localStorage.getItem("tns-device")));
  await page.locator("#ask-options button", { hasText: "Claude" }).click();
  await expect(page.locator("#ask")).toHaveText("Thanks.");
  expect(api.calls.filter(c => c.path === "/profile").map(c => c.body)).toEqual([{ device_id: device, uses_most: "claude" }]);
  await page.click("#again");
  await playSet(page);
  await expect(page.locator("#ask")).toBeHidden();
});

test("skipping the question sends nothing and it stays away", async ({ page, api }) => {
  await openGame(page);
  await playSet(page);
  await page.click("#ask-skip");
  await expect(page.locator("#ask")).toBeHidden();
  await page.click("#again");
  await playSet(page);
  await expect(page.locator("#ask")).toBeHidden();
  expect(api.calls.filter(c => c.path === "/profile")).toHaveLength(0);
});

test("Plausible gets one start and one finish per set, and none twice on reload", async ({ page }) => {
  await openGame(page);
  await playSet(page);
  expect(await events(page)).toEqual(["Set started", "Set finished"]);
  await page.reload();
  await expect(page.locator("#results")).toBeVisible();
  expect(await events(page)).toEqual([]);
  await page.click("#again");
  await playSet(page);
  expect(await events(page)).toEqual(["Set started", "Set finished"]);
});

test("Plausible start is not sent again when a reload lands on story 1 after guessing", async ({ page }) => {
  await openGame(page);
  await guess(page, true);
  await page.reload();
  await expect(page.locator("#reveal")).toBeVisible();
  expect(await events(page)).toEqual([]);
});

test.describe("players line", () => {
  test.use({ stats: { round: "R0", qualifying_guesses: 1234, pooled_accuracy: 0.412 } });
  test("shows the running total once there are guesses", async ({ page, api }) => {
    await openGame(page);
    await playSet(page);
    await expect(page.locator("#players")).toHaveText("Players so far: 41% right across 1,234 first-play guesses.");
    expect(api.calls.some(c => c.path === "/stats" && c.query.round === "R0")).toBe(true);
  });
});

test("players line stays hidden with no guesses yet", async ({ page }) => {
  await openGame(page);
  await playSet(page);
  await expect(page.locator("#players")).toBeHidden();
});
