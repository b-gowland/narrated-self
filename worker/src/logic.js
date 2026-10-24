// Pure logic for guess logging: validation and aggregation. No I/O, so it is unit-tested directly.

export const PER_MODEL_THRESHOLD = 200; // PREREGISTRATION §9: per-model results only after 200 qualifying guesses
export const MIN_MS = 5000; // PREREGISTRATION §9: guesses under 5 seconds are excluded from analysis
export const USES_MOST = ["claude", "chatgpt", "gemini", "grok", "copilot", "meta-ai", "deepseek", "other", "none"];

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ROUND = /^R\d{1,3}$/;
const BOT_UA = /bot|crawl|spider|slurp|headless|lighthouse|preview|curl|wget|python-requests|httpclient/i;

export const isBot = userAgent => !userAgent || BOT_UA.test(userAgent);

/** Index a published round file (site/data/<round>.json) by story ID. */
export function indexRound(roundData) {
  const stories = new Map(roundData.stories.map(s => [s.id, { model: s.model, theme: s.theme, cond: s.cond }]));
  return { stories, models: new Set(roundData.models.map(m => m.id)) };
}

const int = (v, lo, hi) => Number.isInteger(v) && v >= lo && v <= hi;

/**
 * Check a guess from the browser and build the row to store. "true_model" and "correct" are worked out here,
 * from the published round data, never taken from the browser.
 */
export function buildGuessRow(body, index, { receivedAt, userAgent }) {
  const fail = error => ({ ok: false, error });
  if (!body || typeof body !== "object") return fail("body must be a JSON object");
  const { round, mode, device_id, set_id, first_set, story_id, other_id, guess, position, ms_to_guess } = body;
  if (!ROUND.test(round ?? "")) return fail("bad round");
  if (mode !== "quiz" && mode !== "control") return fail("bad mode");
  if (!UUID.test(device_id ?? "") || !UUID.test(set_id ?? "")) return fail("bad device_id or set_id");
  if (typeof first_set !== "boolean") return fail("bad first_set");
  if (!int(position, 1, 10)) return fail("bad position");
  if (!int(ms_to_guess, 0, 3_600_000)) return fail("bad ms_to_guess");
  const story = index.stories.get(story_id);
  if (!story) return fail("unknown story_id");

  let correct, guessValue, other = null;
  if (mode === "quiz") {
    if (!index.models.has(guess)) return fail("unknown guess");
    guessValue = guess;
    correct = guess === story.model;
  } else {
    const otherStory = index.stories.get(other_id);
    if (!otherStory) return fail("unknown other_id");
    guessValue = "robot";
    other = other_id;
    correct = story.cond === "S3";
  }
  return {
    ok: true,
    row: {
      received_at: receivedAt, round, mode, device_id, set_id, first_set: first_set ? 1 : 0,
      story_id, other_id: other, true_model: story.model, theme: story.theme, cond: story.cond,
      guess: guessValue, correct: correct ? 1 : 0, position, ms_to_guess, is_bot: isBot(userAgent) ? 1 : 0,
    },
  };
}

export function buildProfileRow(body, { receivedAt }) {
  if (!body || !UUID.test(body.device_id ?? "")) return { ok: false, error: "bad device_id" };
  if (!USES_MOST.includes(body.uses_most)) return { ok: false, error: "bad uses_most" };
  return { ok: true, row: { device_id: body.device_id, uses_most: body.uses_most, received_at: receivedAt } };
}

/**
 * Aggregate quiz guesses. `rows` are quiz rows for one round. Qualifying guesses are first sets, not bots,
 * and at least MIN_MS to guess. Per-model figures and the confusion matrix are withheld until the threshold.
 */
export function aggregate(rows, models) {
  const qualifying = rows.filter(r => r.first_set === 1 && r.is_bot === 0 && r.ms_to_guess >= MIN_MS);
  const correct = qualifying.filter(r => r.correct === 1).length;
  const perModel = {};
  for (const m of models) {
    const own = qualifying.filter(r => r.true_model === m);
    const met = own.length >= PER_MODEL_THRESHOLD;
    perModel[m] = { qualifying: own.length, accuracy: met ? own.filter(r => r.correct === 1).length / own.length : null };
  }
  const allMet = models.every(m => perModel[m].qualifying >= PER_MODEL_THRESHOLD);
  let confusion = null;
  if (allMet) {
    confusion = Object.fromEntries(models.map(t => [t, Object.fromEntries(models.map(g => [g, 0]))]));
    for (const r of qualifying) if (confusion[r.true_model] && r.guess in confusion[r.true_model]) confusion[r.true_model][r.guess] += 1;
  }
  return {
    all_guesses: rows.length,
    qualifying_guesses: qualifying.length,
    excluded: {
      repeat_sets: rows.filter(r => r.first_set === 0).length,
      bots: rows.filter(r => r.is_bot === 1).length,
      under_5_seconds: rows.filter(r => r.ms_to_guess < MIN_MS).length,
    },
    pooled_accuracy: qualifying.length ? correct / qualifying.length : null,
    chance: models.length ? 1 / models.length : null,
    per_model_threshold: PER_MODEL_THRESHOLD,
    per_model: perModel,
    confusion_matrix: confusion,
  };
}
