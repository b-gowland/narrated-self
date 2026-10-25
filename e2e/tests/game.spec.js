// The guessing game: a full set, the reveal after each guess, the score page, play again and resuming.
import { test, expect, openGame, playSet, guess, expectFreshStory, savedState, storyById, MODEL_NAMES, ROUND } from "./helpers.js";

test("a full set: each story starts clean, the reveal is right, the score adds up", async ({ page }) => {
  await openGame(page);
  const pattern = [true, false, true, false, false];
  const played = [];
  for (let k = 0; k < 5; k++) {
    await expectFreshStory(page, k + 1);
    const pips = page.locator("#pips i");
    await expect(pips).toHaveCount(5);
    await expect(pips.nth(k)).toHaveClass("now");
    const g = await guess(page, pattern[k]);
    played.push(g);
    const answerName = ROUND.models.find(m => m.id === g.answer).name;
    const pickName = ROUND.models.find(m => m.id === g.pick).name;
    await expect(page.locator("#reveal")).toBeVisible();
    await expect(page.locator("#who")).toHaveText(answerName);
    await expect(page.locator("#verdict")).toHaveText(pattern[k] ? "Got it. Written by" : `Not ${pickName}. Written by`);
    await expect(page.locator("#stamp")).toHaveClass(pattern[k] ? "stamp" : "stamp wrong");
    await expect(page.locator("#choices .choice:enabled")).toHaveCount(0);
    await expect(page.locator(`#choice-${g.answer}`)).toHaveClass(/is-answer/);
    await expect(page.locator(`#choice-${g.pick}`)).toHaveClass(/picked/);
    await expect(pips.nth(k)).toHaveClass(pattern[k] ? "right" : "wrong");
    await expect(page.locator("#risk-name")).not.toBeEmpty();
    await expect(page.locator("#question")).not.toBeEmpty();
    await expect(page.locator("#to-interview")).toHaveText(`What ${answerName} says when asked straight →`);
    await expect(page.locator("#next")).toHaveText(k === 4 ? "See my score" : "Next story");
    await expect(page.locator("#next")).toBeFocused();
    await page.click("#next");
  }
  await expect(page.locator("#results")).toBeVisible();
  await expect(page.locator("#card")).toBeHidden();
  await expect(page.locator("#score")).toHaveText("2/5");
  const tally = page.locator("#tally li");
  await expect(tally).toHaveCount(5);
  for (let k = 0; k < 5; k++) {
    const a = ROUND.models.find(m => m.id === played[k].answer).name;
    const p = ROUND.models.find(m => m.id === played[k].pick).name;
    await expect(tally.nth(k).locator(".who")).toHaveText(pattern[k] ? a : `${a}, not ${p}`);
    await expect(tally.nth(k).locator(".mark")).toHaveText(pattern[k] ? "✓" : "✗");
  }
  await expect(page.locator("#score-line")).toContainText("1 in 5");
});

test("each set has one story per model, from the quiz pool", async ({ page }) => {
  await openGame(page);
  const s = await savedState(page);
  expect(s.set).toHaveLength(5);
  const stories = s.set.map(id => storyById[id]);
  expect(new Set(stories.map(x => x.model)).size).toBe(5);
  for (const x of stories) {
    expect(ROUND.quiz.conditions).toContain(x.cond);
    expect(x.words).toBeGreaterThanOrEqual(ROUND.quiz.min_words);
  }
});

test("the score line matches the score", async ({ page }) => {
  await openGame(page);
  await playSet(page, [true, true, true, true, true]);
  await expect(page.locator("#score")).toHaveText("5/5");
  await expect(page.locator("#score-line")).toContainText("You got every one");
  await page.click("#again");
  await playSet(page, [false, false, false, false, false]);
  await expect(page.locator("#score")).toHaveText("0/5");
  await expect(page.locator("#score-line")).toContainText("None this time");
});

test("play again starts a clean new set", async ({ page, api }) => {
  await openGame(page);
  await playSet(page);
  const first = await savedState(page);
  await page.click("#again");
  await expect(page.locator("#results")).toBeHidden();
  await expect(page.locator("#card")).toBeVisible();
  await expectFreshStory(page, 1);
  await expect(page.locator("#pips i.right, #pips i.wrong")).toHaveCount(0);
  const second = await savedState(page);
  expect(second.set_id).not.toBe(first.set_id);
  expect(second.first).toBe(false);
  expect(second.results).toEqual([]);
  await playSet(page);
  const guesses = api.guesses();
  expect(guesses).toHaveLength(10);
  expect(guesses.slice(0, 5).every(g => g.first_set === true && g.set_id === first.set_id)).toBe(true);
  expect(guesses.slice(5).every(g => g.first_set === false && g.set_id === second.set_id)).toBe(true);
});

test("leaving mid-set and coming back resumes on the same story", async ({ page }) => {
  await openGame(page);
  await guess(page, true);
  await page.click("#next");
  await guess(page, false);
  await page.click("#next");
  await expectFreshStory(page, 3);
  const before = await savedState(page);
  await page.reload();
  await expectFreshStory(page, 3);
  const after = await savedState(page);
  expect(after.set).toEqual(before.set);
  expect(after.results).toEqual([true, false]);
  await expect(page.locator("#pips i").nth(0)).toHaveClass("right");
  await expect(page.locator("#pips i").nth(1)).toHaveClass("wrong");
});

test("reloading after a guess shows that answer again and doesn't allow a second guess", async ({ page, api }) => {
  await openGame(page);
  const g = await guess(page, false);
  await expect(page.locator("#reveal")).toBeVisible();
  await page.reload();
  await expect(page.locator("#m-no")).toHaveText("Story 1 of 5");
  await expect(page.locator("#reveal")).toBeVisible();
  await expect(page.locator("#choices .choice:enabled")).toHaveCount(0);
  await expect(page.locator(`#choice-${g.answer}`)).toHaveClass(/is-answer/);
  await expect(page.locator("#next")).toHaveText("Next story");
  await page.click("#next");
  await expectFreshStory(page, 2);
  expect(api.guesses().filter(x => x.position === 1)).toHaveLength(1);
});

test("a finished set still shows the score after a reload", async ({ page }) => {
  await openGame(page);
  await playSet(page, [true, true, false, false, false]);
  await page.reload();
  await expect(page.locator("#results")).toBeVisible();
  await expect(page.locator("#card")).toBeHidden();
  await expect(page.locator("#score")).toHaveText("2/5");
});

test("a damaged saved game starts a fresh set", async ({ page }) => {
  await openGame(page);
  for (const bad of ['{"set":["nope"],"set_id":"x","i":0,"results":[]}', "not json", '{"i":3}']) {
    await page.evaluate(v => localStorage.setItem("tns-R0-live-v5", v), bad);
    await page.reload();
    await expectFreshStory(page, 1);
  }
});

test("the results card and share text number each set", async ({ page }) => {
  await openGame(page);
  await playSet(page);
  await expect(page.locator("#results-label")).toHaveText("Round 0 · Set 1");
  await expect(page.locator("#share-text")).toContainText("THE NARRATED SELF · Round 0, set 1");
  await page.click("#again");
  await playSet(page);
  await expect(page.locator("#results-label")).toHaveText("Round 0 · Set 2");
  await expect(page.locator("#share-text")).toContainText("Round 0, set 2");
});

test("story text and buttons never show unmasked model names in quiz stories", async ({ page }) => {
  // Fairness: masking replaced names with bars; check the rendered text, not just the data.
  const names = [...MODEL_NAMES, ...ROUND.models.map(m => m.lab)];
  await openGame(page);
  for (let k = 0; k < 5; k++) {
    const text = await page.locator("#story").innerText();
    for (const n of names) expect(text, `story ${k + 1} mentions ${n}`).not.toMatch(new RegExp(`\\b${n}\\b`));
    const bars = page.locator("#story .bar");
    for (let b = 0; b < await bars.count(); b++) {
      await expect(bars.nth(b)).toHaveAttribute("aria-label", "name hidden");
      expect((await bars.nth(b).textContent()).trim()).toBe("");
    }
    await guess(page, true);
    await page.click("#next");
  }
});

test("the exact prompt matches the round's prompt for that story", async ({ page }) => {
  await openGame(page);
  const s = await savedState(page);
  const story = storyById[s.set[0]];
  await page.click("details.prompt summary");
  await expect(page.locator("#m-prompt")).toHaveText(ROUND.prompts[story.theme][story.cond]);
});

test("double-clicking a choice records one guess", async ({ page, api }) => {
  await openGame(page);
  const s = await savedState(page);
  await page.locator(`#choice-${storyById[s.set[0]].model}`).dblclick();
  await expect(page.locator("#reveal")).toBeVisible();
  expect(api.guesses()).toHaveLength(1);
});
