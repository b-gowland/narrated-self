// The Narrated Self: anonymous guess logging (docs/PREREGISTRATION.md §9).
// Stores no IP address, user agent or cookie. Story IDs are checked against the published round data,
// and whether a guess is correct is worked out here, not taken from the browser.

import { aggregate, buildGuessRow, buildProfileRow, indexRound } from "./logic.js";

const MAX_GUESSES_PER_DEVICE_PER_DAY = 1000; // flood protection only; analysis exclusions are separate
const MAX_BODY_BYTES = 4096;
const ROUND_ID = /^R\d{1,3}$/;
const roundCache = new Map(); // per isolate: round -> { index, models, at }

async function loadRound(env, round) {
  if (!ROUND_ID.test(round)) return null; // validate before building any URL from it
  const hit = roundCache.get(round);
  if (hit && Date.now() - hit.at < 10 * 60 * 1000) return hit;
  const res = await fetch(`${env.SITE_URL}/data/${round}.json`, { cf: { cacheTtl: 600 } });
  if (!res.ok) return null;
  const data = await res.json();
  const entry = { index: indexRound(data), models: data.models.map(m => m.id), at: Date.now() };
  roundCache.set(round, entry);
  return entry;
}

function cors(env, request) {
  const origin = request.headers.get("Origin") ?? "";
  const allowed = env.ALLOWED_ORIGINS.split(",").map(s => s.trim());
  return allowed.includes(origin)
    ? { "Access-Control-Allow-Origin": origin, "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" }
    : {};
}

const SECURITY_HEADERS = { "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer" };

const json = (body, status, headers = {}) =>
  new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json", ...SECURITY_HEADERS, ...headers },
  });

// Constant-time comparison, so response timing can't be used to guess the export token.
function tokenMatches(given, expected) {
  if (!expected || typeof given !== "string") return false;
  const a = new TextEncoder().encode(given);
  const b = new TextEncoder().encode(expected);
  if (a.byteLength !== b.byteLength) return false;
  return crypto.subtle.timingSafeEqual(a, b);
}

async function readBody(request) {
  const declared = Number(request.headers.get("Content-Length") ?? "0");
  if (declared > MAX_BODY_BYTES) return null; // refuse large bodies before reading them
  const text = await request.text();
  if (text.length > MAX_BODY_BYTES) return null;
  try { return JSON.parse(text); } catch { return null; }
}

async function postGuess(request, env, headers) {
  const body = await readBody(request);
  const round = await loadRound(env, body?.round ?? "");
  if (!round) return json({ error: "unknown round" }, 400, headers);
  const built = buildGuessRow(body, round.index, {
    receivedAt: new Date().toISOString(),
    userAgent: request.headers.get("User-Agent") ?? "",
  });
  if (!built.ok) return json({ error: built.error }, 400, headers);
  const r = built.row;
  const today = r.received_at.slice(0, 10);
  const { n } = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM guesses WHERE device_id = ? AND received_at >= ?"
  ).bind(r.device_id, today).first();
  if (n >= MAX_GUESSES_PER_DEVICE_PER_DAY) return json({ error: "daily limit reached" }, 429, headers);
  // One guess per story in a set: a second one (an old page, a reload, a script) is refused, not stored.
  const dup = await env.DB.prepare(
    "SELECT 1 FROM guesses WHERE set_id = ? AND mode = ? AND position = ? LIMIT 1"
  ).bind(r.set_id, r.mode, r.position).first();
  if (dup) return json({ error: "already guessed" }, 409, headers);
  await env.DB.prepare(
    `INSERT INTO guesses (received_at, round, mode, device_id, set_id, first_set, story_id, other_id,
       true_model, theme, cond, guess, correct, position, ms_to_guess, is_bot)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(r.received_at, r.round, r.mode, r.device_id, r.set_id, r.first_set, r.story_id, r.other_id,
    r.true_model, r.theme, r.cond, r.guess, r.correct, r.position, r.ms_to_guess, r.is_bot).run();
  return json({ ok: true, correct: r.correct === 1 }, 201, headers);
}

async function postProfile(request, env, headers) {
  const built = buildProfileRow(await readBody(request), { receivedAt: new Date().toISOString() });
  if (!built.ok) return json({ error: built.error }, 400, headers);
  const r = built.row;
  await env.DB.prepare(
    "INSERT OR REPLACE INTO profiles (device_id, uses_most, received_at) VALUES (?, ?, ?)"
  ).bind(r.device_id, r.uses_most, r.received_at).run();
  return json({ ok: true }, 201, headers);
}

async function quizRows(env, round) {
  const { results } = await env.DB.prepare(
    "SELECT true_model, guess, correct, first_set, is_bot, ms_to_guess FROM guesses WHERE round = ? AND mode = 'quiz'"
  ).bind(round).all();
  return results;
}

const STATS_TTL_SECONDS = 300;

// Cached for 5 minutes at Cloudflare's edge, so database reads stay flat however many people load the page.
// Only the body is cached; CORS headers are added per request.
async function getStats(url, env, headers, ctx) {
  const roundId = url.searchParams.get("round") ?? "";
  const cacheKey = new Request(`${url.origin}/stats?round=${encodeURIComponent(roundId)}`);
  const cache = caches.default;
  let body = await cache.match(cacheKey).then(r => (r ? r.text() : null)).catch(() => null);
  if (body === null) {
    const round = await loadRound(env, roundId);
    if (!round) return json({ error: "unknown round" }, 400, headers);
    const stats = aggregate(await quizRows(env, roundId), round.models);
    body = JSON.stringify({ round: roundId, ...stats, updated_utc: new Date().toISOString() });
    const toCache = new Response(body, {
      headers: { "Content-Type": "application/json", "Cache-Control": `public, max-age=${STATS_TTL_SECONDS}` },
    });
    ctx.waitUntil(cache.put(cacheKey, toCache).catch(() => {}));
  }
  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "application/json", "Cache-Control": `public, max-age=${STATS_TTL_SECONDS}`,
      ...SECURITY_HEADERS, ...headers,
    },
  });
}

async function getExport(url, request, env) {
  const auth = request.headers.get("Authorization") ?? "";
  if (!tokenMatches(auth.startsWith("Bearer ") ? auth.slice(7) : "", env.EXPORT_TOKEN)) {
    return json({ error: "unauthorised" }, 401);
  }
  const roundId = url.searchParams.get("round") ?? "";
  const round = await loadRound(env, roundId);
  if (!round) return json({ error: "unknown round" }, 400);
  const out = { round: roundId, ...aggregate(await quizRows(env, roundId), round.models) };
  const control = await env.DB.prepare(
    "SELECT COUNT(*) AS picks, SUM(correct) AS correct FROM guesses WHERE round = ? AND mode = 'control' AND is_bot = 0"
  ).bind(roundId).first();
  out.spot_the_robot = { picks: control.picks ?? 0, correct: control.correct ?? 0 };
  const { results: profiles } = await env.DB.prepare(
    "SELECT uses_most, COUNT(*) AS devices FROM profiles GROUP BY uses_most ORDER BY uses_most"
  ).all();
  out.uses_most = Object.fromEntries(profiles.map(p => [p.uses_most, p.devices]));
  if (url.searchParams.get("rows") === "1") {
    const { results } = await env.DB.prepare("SELECT * FROM guesses WHERE round = ? ORDER BY id").bind(roundId).all();
    out.rows = results;
  }
  out.exported_utc = new Date().toISOString();
  return json(out, 200);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const headers = cors(env, request);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
    try {
      if (request.method === "POST" && url.pathname === "/guess") return await postGuess(request, env, headers);
      if (request.method === "POST" && url.pathname === "/profile") return await postProfile(request, env, headers);
      if (request.method === "GET" && url.pathname === "/stats") return await getStats(url, env, headers, ctx);
      if (request.method === "GET" && url.pathname === "/export") return await getExport(url, request, env);
      return json({ error: "not found" }, 404, headers);
    } catch (e) {
      console.error(`${request.method} ${url.pathname}: ${e && e.stack ? e.stack : e}`);
      return json({ error: "server error" }, 500, headers);
    }
  },
};
