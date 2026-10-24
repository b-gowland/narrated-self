import assert from "node:assert/strict";
import { test } from "node:test";
import { aggregate, buildGuessRow, buildProfileRow, indexRound, isBot, PER_MODEL_THRESHOLD } from "../src/logic.js";

const round = indexRound({
  models: [{ id: "anthropic" }, { id: "openai" }],
  stories: [
    { id: "R0-anthropic-T1-S1-s1", model: "anthropic", theme: "T1", cond: "S1" },
    { id: "R0-openai-T1-S2-s1", model: "openai", theme: "T1", cond: "S2" },
    { id: "R0-openai-T1-S3-s1", model: "openai", theme: "T1", cond: "S3" },
  ],
});
const DEVICE = "0b5c7e1a-3f2d-4c8b-9a6e-1d2f3a4b5c6d";
const SET = "9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b";
const ctx = { receivedAt: "2026-10-25T00:00:00.000Z", userAgent: "Mozilla/5.0 (Windows NT 10.0) Firefox/140.0" };
const quiz = (over = {}) => ({
  round: "R0", mode: "quiz", device_id: DEVICE, set_id: SET, first_set: true,
  story_id: "R0-anthropic-T1-S1-s1", guess: "anthropic", position: 1, ms_to_guess: 42000, ...over,
});

test("a valid quiz guess is stored with the true model and correctness worked out server-side", () => {
  const { ok, row } = buildGuessRow(quiz(), round, ctx);
  assert.equal(ok, true);
  assert.equal(row.true_model, "anthropic");
  assert.equal(row.correct, 1);
  assert.equal(row.is_bot, 0);
  assert.equal(buildGuessRow(quiz({ guess: "openai" }), round, ctx).row.correct, 0);
});

test("the browser cannot claim a guess was correct", () => {
  const { row } = buildGuessRow(quiz({ guess: "openai", correct: true, true_model: "openai" }), round, ctx);
  assert.equal(row.true_model, "anthropic");
  assert.equal(row.correct, 0);
});

test("nothing identifying is stored", () => {
  const { row } = buildGuessRow(quiz(), round, ctx);
  for (const key of Object.keys(row)) assert.ok(!/ip|agent|ua|cookie|email|name/i.test(key), key);
});

test("bad input is rejected", () => {
  for (const [over, msg] of [
    [{ round: "R0; DROP TABLE" }, "bad round"], [{ mode: "x" }, "bad mode"], [{ device_id: "abc" }, "bad device_id or set_id"],
    [{ first_set: "yes" }, "bad first_set"], [{ position: 0 }, "bad position"], [{ ms_to_guess: -1 }, "bad ms_to_guess"],
    [{ story_id: "R0-made-up" }, "unknown story_id"], [{ guess: "skynet" }, "unknown guess"],
  ]) {
    assert.deepEqual(buildGuessRow(quiz(over), round, ctx), { ok: false, error: msg });
  }
  assert.equal(buildGuessRow(null, round, ctx).ok, false);
});

test("control picks are correct only when the robot-arm story is picked", () => {
  const pick = story_id => buildGuessRow(
    { ...quiz(), mode: "control", story_id, other_id: "R0-openai-T1-S2-s1", guess: undefined }, round, ctx).row;
  assert.equal(pick("R0-openai-T1-S3-s1").correct, 1);
  assert.equal(pick("R0-openai-T1-S2-s1").correct, 0);
  assert.equal(pick("R0-openai-T1-S3-s1").guess, "robot");
});

test("bot user agents are flagged, and the agent itself is not kept", () => {
  assert.equal(isBot("Googlebot/2.1"), true);
  assert.equal(isBot("curl/8.0"), true);
  assert.equal(isBot(""), true);
  assert.equal(isBot(ctx.userAgent), false);
  assert.equal(buildGuessRow(quiz(), round, { ...ctx, userAgent: "Googlebot" }).row.is_bot, 1);
});

test("profile answers are limited to the listed options", () => {
  assert.equal(buildProfileRow({ device_id: DEVICE, uses_most: "claude" }, ctx).ok, true);
  assert.equal(buildProfileRow({ device_id: DEVICE, uses_most: "my cousin's bot" }, ctx).ok, false);
});

test("aggregates exclude repeat sets, bots and fast guesses, and withhold per-model results below the threshold", () => {
  const base = { true_model: "anthropic", guess: "anthropic", correct: 1, first_set: 1, is_bot: 0, ms_to_guess: 30000 };
  const rows = [
    base,
    { ...base, first_set: 0 },
    { ...base, is_bot: 1 },
    { ...base, ms_to_guess: 1200 },
    { ...base, true_model: "openai", guess: "anthropic", correct: 0 },
  ];
  const a = aggregate(rows, ["anthropic", "openai"]);
  assert.equal(a.all_guesses, 5);
  assert.equal(a.qualifying_guesses, 2);
  assert.deepEqual(a.excluded, { repeat_sets: 1, bots: 1, under_5_seconds: 1 });
  assert.equal(a.pooled_accuracy, 0.5);
  assert.equal(a.per_model.anthropic.accuracy, null);
  assert.equal(a.confusion_matrix, null);
});

test("per-model accuracy and the confusion matrix appear once every model passes the threshold", () => {
  const rows = [];
  for (const m of ["anthropic", "openai"]) {
    for (let i = 0; i < PER_MODEL_THRESHOLD; i++) {
      const right = i % 4 === 0;
      rows.push({ true_model: m, guess: right ? m : (m === "anthropic" ? "openai" : "anthropic"),
        correct: right ? 1 : 0, first_set: 1, is_bot: 0, ms_to_guess: 20000 });
    }
  }
  const a = aggregate(rows, ["anthropic", "openai"]);
  assert.equal(a.per_model.anthropic.accuracy, 0.25);
  assert.equal(a.confusion_matrix.anthropic.openai, 150);
  assert.equal(a.confusion_matrix.openai.openai, 50);
});
