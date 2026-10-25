// The Narrated Self: game, comparison views and anonymous guess logging. Loaded by index.html.
(async () => {
  const $ = id => document.getElementById(id);
  const ROUND_URL = "data/R0.json";

  async function loadRound(url) {
    try {
      const r = await fetch(url, { cache: "no-cache" });
      return r.ok ? await r.json() : null;
    } catch {
      return null;
    }
  }

  // Display only: drop light Markdown (headings, emphasis marks, rules) from model text. Stored data is unchanged.
  function toParagraphs(text) {
    return text.replace(/\r/g, "").split(/\n\s*\n/)
      .map(p => p.trim())
      .filter(p => p && !/^([-*_]\s*){3,}$/.test(p))
      .map(p => p.replace(/^#{1,6}\s*/gm, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/(^|[\s(])[*_]([^*_\n]+)[*_](?=[\s.,;:!?)]|$)/g, "$1$2").replace(/\s*\n\s*/g, " "));
  }
  const pick = a => a[Math.floor(Math.random() * a.length)];
  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  // Real round data, shaped for the game. Each set has one story per model, drawn from the quiz pool.
  function fromRound(real, demo) {
    const stories = real.stories;
    const find = (model, theme, cond, sample = 1) =>
      stories.find(s => s.model === model && s.theme === theme && s.cond === cond && s.sample === sample);
    const pool = stories.filter(s => real.quiz.conditions.includes(s.cond) && s.words >= real.quiz.min_words);
    const themes = {};
    for (const [t, d] of Object.entries(demo.themes)) {
      themes[t] = { ...d, direct: real.prompts[t]?.D ?? d.direct, self: real.prompts[t]?.S1 ?? d.self };
    }
    return {
      round: real.round, real: true, models: real.models, themes, conditions: demo.conditions,
      drawSet: () => shuffle(real.models.map(m => pool.filter(s => s.model === m.id)).filter(own => own.length).map(own => pick(own).id)),
      item(id) {
        const s = stories.find(x => x.id === id);
        return { id, theme: s.theme, cond: s.cond, answer: s.model, prompt: real.prompts[s.theme][s.cond], text: toParagraphs(s.text) };
      },
      compareText: (model, theme, cond) => toParagraphs(find(model, theme, cond)?.text ?? "(No output for this cell.)"),
      control() {
        const model = pick(real.models).id;
        const theme = pick(Object.keys(themes));
        const items = [find(model, theme, "S2"), find(model, theme, "S3")].filter(Boolean)
          .map(s => ({ id: s.id, cond: s.cond, text: toParagraphs(s.text) }));
        return { theme, model, items };
      }
    };
  }

  // Placeholder demo, used when the round's data file can't be loaded.
  function fromDemo(demo) {
    return {
      round: demo.round, real: false, models: demo.models, themes: demo.themes, conditions: demo.conditions,
      drawSet: () => demo.quiz.map((_, i) => i),
      item: i => ({ ...demo.quiz[i], id: i }),
      compareText: (model, theme, cond) => [cond === "D" ? demo.compare.D : demo.compare.S1],
      control: () => ({ theme: "T2", items: demo.control.map(c => ({ cond: c.cond, text: [c.text] })) })
    };
  }

  const demo = JSON.parse($("data").textContent);
  const real = await loadRound(ROUND_URL);
  const data = real ? fromRound(real, demo) : fromDemo(demo);
  const byId = Object.fromEntries(data.models.map(m => [m.id, m]));

  // Anonymous guess logging (PREREGISTRATION §9). Only on the live site, or a local test against a local Worker.
  const API = location.hostname === "narratedself.airiskpractice.org" ? "https://narratedself-api.airiskpractice.org"
    : location.hostname === "localhost" ? "http://127.0.0.1:8787" : null;
  const CAN_LOG = Boolean(API && data.real && window.crypto?.randomUUID);
  // "Don't record my guesses": remembered on this device; when set, nothing is sent.
  const OPTOUT_KEY = "tns-optout";
  let recording = CAN_LOG && (() => { try { return localStorage.getItem(OPTOUT_KEY) !== "1"; } catch { return true; } })();
  function log(path, body) {
    if (!recording) return;
    try {
      fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body), keepalive: true }).catch(() => {});
    } catch {}
  }
  function updateNotice() {
    if (data.real) {
      document.querySelector(".demo-note .wrap").textContent =
        !CAN_LOG ? "Preview · round 0 · real model outputs, names blacked out · guesses aren't recorded here"
        : recording ? "Round 0 · real model outputs, names blacked out · guesses recorded anonymously for research"
        : "Round 0 · real model outputs, names blacked out · your guesses aren't being recorded";
    }
    $("notice").hidden = !CAN_LOG;
    $("notice-text").textContent = recording
      ? "Your guesses are recorded anonymously for an open study: no account, no IP address, just a random ID kept in your browser."
      : "Your guesses aren't being recorded on this device.";
    $("optout").textContent = recording ? "Don't record my guesses" : "Record them again";
  }
  $("optout").addEventListener("click", () => {
    recording = !recording;
    try { localStorage.setItem(OPTOUT_KEY, recording ? "0" : "1"); } catch {}
    updateNotice();
    if (!recording) $("ask").hidden = true;
  });
  updateNotice();
  $("notice-link").addEventListener("click", e => { e.preventDefault(); show("about"); $("your-guesses").scrollIntoView(); });
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
  };
  const READING_WPM = 230;

  // Turn [[Name]] into a black bar the same width as the hidden word.
  function para(text) {
    const p = document.createElement("p");
    text.split(/(\[\[[^\]]+\]\])/).forEach(part => {
      const m = part.match(/^\[\[(.+)\]\]$/);
      if (m) {
        const s = document.createElement("span");
        s.className = "bar";
        s.textContent = " ".repeat(m[1].length); // blank of the same width, so copying never leaks the name
        s.setAttribute("role", "img");
        s.setAttribute("aria-label", "name hidden");
        p.append(s);
      } else if (part) {
        p.append(part);
      }
    });
    return p;
  }
  const wordCount = paras => paras.join(" ").replace(/\[\[[^\]]+\]\]/g, "x").split(/\s+/).filter(Boolean).length;

  // Views
  const views = ["play", "compare", "control", "findings", "about"];
  function show(view) {
    if (!views.includes(view)) view = "play";
    views.forEach(v => { $("view-" + v).hidden = v !== view; });
    document.querySelectorAll("nav a").forEach(a => {
      if (a.dataset.view === view) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    try { history.replaceState(null, "", "#" + view); } catch {}
  }
  document.querySelectorAll("nav a, .wordmark, a[data-view]").forEach(a => a.addEventListener("click", e => {
    e.preventDefault();
    show(a.getAttribute("href").slice(1));
    window.scrollTo(0, 0);
  }));
  show(location.hash.slice(1));

  // Play
  const KEY = `tns-${data.round}-${data.real ? "live" : "demo"}-v5`;
  const newId = () => (window.crypto?.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2));
  const DEVICE = store.get("tns-device") || newId();
  store.set("tns-device", DEVICE);
  const setsDone = () => store.get("tns-sets-done") || 0;
  const fresh = () => ({ set: data.drawSet(), set_id: newId(), first: setsDone() === 0, n: setsDone() + 1, counted: false, i: 0, results: [], guesses: [] });
  let state = store.get(KEY);
  let quiz;
  try {
    if (!state.set_id) throw new Error("old saved state");
    quiz = state.set.map(id => data.item(id));
  } catch {
    state = fresh();
    quiz = state.set.map(id => data.item(id));
    store.set(KEY, state); // so a reload before the first guess shows the same story
  }
  let shownAt = performance.now();

  function renderPips() {
    $("pips").replaceChildren(...quiz.map((_, k) => {
      const i = document.createElement("i");
      const r = state.results[k];
      i.className = r === undefined ? (k === state.i ? "now" : "") : (r ? "right" : "wrong");
      return i;
    }));
  }

  function renderCard() {
    const q = quiz[state.i];
    const words = wordCount(q.text);
    $("cover").dataset.themeId = q.theme;
    $("m-no").textContent = `Story ${state.i + 1} of ${quiz.length}`;
    $("m-theme").textContent = data.themes[q.theme].name;
    $("m-cond").textContent = data.conditions[q.cond];
    $("m-facts").textContent = `${words} words · ${Math.max(1, Math.round(words / READING_WPM))} min read · ${q.theme} · ${q.cond}`;
    $("m-prompt").textContent = q.prompt;
    $("story").replaceChildren(...q.text.map(para));
    $("choices").replaceChildren(...data.models.map(m => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "choice";
      b.id = "choice-" + m.id;
      b.setAttribute("aria-label", `${m.name}, by ${m.lab}`);
      b.innerHTML = "<span></span><small></small>";
      b.firstChild.textContent = m.name;
      b.lastChild.textContent = m.lab;
      b.addEventListener("click", () => guess(m.id));
      return b;
    }));
    $("tray").classList.remove("done");
    $("tray-label").textContent = "Who wrote it?";
    $("reveal").hidden = true;
    renderPips();
    shownAt = performance.now();
    // Already guessed (e.g. a reload after guessing): show that answer again rather than allowing a second guess.
    if (state.results[state.i] !== undefined) showReveal(state.guesses[state.i]);
  }

  // Plausible goals; names must match the goals set up in Plausible.
  const track = name => { if (recording) try { window.plausible?.(name); } catch {} };

  function guess(id) {
    if (state.results[state.i] !== undefined) return; // one guess per story
    const q = quiz[state.i];
    if (state.i === 0) track("Set started");
    state.results[state.i] = id === q.answer;
    state.guesses[state.i] = id;
    log("/guess", {
      round: data.round, mode: "quiz", device_id: DEVICE, set_id: state.set_id, first_set: state.first,
      story_id: q.id, guess: id, position: state.i + 1, ms_to_guess: Math.round(performance.now() - shownAt)
    });
    store.set(KEY, state);
    showReveal(id);
    $("stamp").scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    $("next").focus({ preventScroll: true });
  }

  // The answer for the current story, after a guess.
  function showReveal(id) {
    const q = quiz[state.i];
    const right = id === q.answer;
    document.querySelectorAll(".choice").forEach(b => {
      b.disabled = true;
      if (b.id === "choice-" + id) b.classList.add("picked");
      if (b.id === "choice-" + q.answer) {
        b.classList.add("is-answer");
        b.insertAdjacentHTML("beforeend",
          '<svg class="circle" viewBox="0 0 120 60" preserveAspectRatio="none" aria-hidden="true">' +
          '<path d="M10,34 C8,12 52,4 96,9 C121,12 120,47 86,53 C52,59 7,54 5,32 C4,19 27,8 55,6"/></svg>');
      }
    });
    const m = byId[q.answer];
    $("tray").classList.add("done");
    $("tray-label").textContent = "Your guess";
    $("verdict").textContent = right ? "Got it. Written by" : `Not ${byId[id].name}. Written by`;
    $("who").textContent = m.name;
    const stamp = $("stamp");
    stamp.className = "stamp" + (right ? "" : " wrong");
    void stamp.offsetWidth; // restart the stamp animation
    $("risk-name").textContent = data.themes[q.theme].risk;
    $("question").textContent = data.themes[q.theme].question;
    $("to-interview").textContent = `What ${m.name} says when asked straight →`;
    $("to-interview").onclick = () => openCompare(q.answer, q.theme);
    $("next").textContent = state.i === quiz.length - 1 ? "See my score" : "Next story";
    $("reveal").hidden = false;
    renderPips();
  }

  // "Round 0" from "R0"; the set number counts this device's sets (older saved games have none).
  const roundLabel = `Round ${String(data.round).replace(/^R/, "")}`;
  const setLabel = sep => state.n ? `${roundLabel}${sep}set ${state.n}` : roundLabel;

  function shareText() {
    const n = state.results.filter(Boolean).length;
    const marks = state.results.map(r => (r ? "🟩" : "⬛")).join("");
    return `THE NARRATED SELF · ${setLabel(", ")}\n${marks} ${n}/${quiz.length}\nWho wrote this?`;
  }

  function renderResults() {
    const n = state.results.filter(Boolean).length;
    $("card").hidden = true;
    $("results").hidden = false;
    $("results-label").textContent = setLabel(" · ").replace(" set", " Set");
    $("score").textContent = `${n}/${quiz.length}`;
    const chance = `Guessing at random would get about 1 in ${data.models.length} right.`;
    $("score-line").textContent =
      n === quiz.length ? `You got every one. ${chance} You either know these models well, or their voices are easy to tell apart.` :
      n >= 3 ? `That's well above chance. ${chance} Some models are easier to recognise than others.` :
      n >= 1 ? `That's close to chance. ${chance} When these models write about themselves, they can sound very alike.` :
      `None this time. ${chance} When these models write about themselves, they can sound very alike.`;
    $("tally").replaceChildren(...quiz.map((q, k) => {
      const li = document.createElement("li");
      const right = state.results[k];
      li.innerHTML = `<span class="mark"></span><span class="what"></span><span class="who"></span>`;
      li.children[0].textContent = right ? "✓" : "✗";
      li.children[0].className = "mark " + (right ? "right" : "wrong");
      li.children[1].textContent = `${data.themes[q.theme].name} · ${data.conditions[q.cond].split(",")[0]}`;
      li.children[2].textContent = right ? byId[q.answer].name : `${byId[q.answer].name}, not ${byId[state.guesses[k]]?.name ?? "?"}`;
      return li;
    }));
    $("share-text").textContent = shareText();
    $("share-status").textContent = "";
    if (!state.counted) {
      state.counted = true;
      track("Set finished");
      store.set("tns-sets-done", setsDone() + 1);
      store.set(KEY, state);
    }
    $("ask").hidden = !recording || Boolean(store.get("tns-uses-most"));
    showPlayers();
    $("results").scrollIntoView({ block: "start" });
  }

  // Running total from the API: pooled accuracy only (per-model results wait for the pre-registered threshold).
  async function showPlayers() {
    if (!CAN_LOG) return;
    try {
      const r = await fetch(`${API}/stats?round=${data.round}`);
      const s = await r.json();
      if (!s.qualifying_guesses) return;
      $("players").textContent = `Players so far: ${Math.round(s.pooled_accuracy * 100)}% right across ${s.qualifying_guesses.toLocaleString("en-AU")} first-play guesses.`;
      $("players").hidden = false;
    } catch {}
  }

  const USES_MOST = [["claude", "Claude"], ["chatgpt", "ChatGPT"], ["gemini", "Gemini"], ["grok", "Grok"],
    ["copilot", "Copilot"], ["meta-ai", "Meta AI"], ["deepseek", "DeepSeek"], ["other", "Another one"], ["none", "I don't use one"]];
  $("ask-options").replaceChildren(...USES_MOST.map(([value, label]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.addEventListener("click", () => {
      log("/profile", { device_id: DEVICE, uses_most: value });
      store.set("tns-uses-most", value);
      $("ask").replaceChildren(Object.assign(document.createElement("p"), { className: "status", textContent: "Thanks." }));
    });
    return b;
  }));
  $("ask-skip").addEventListener("click", () => { store.set("tns-uses-most", "skipped"); $("ask").hidden = true; });

  $("next").addEventListener("click", () => {
    if (state.i < quiz.length - 1) {
      state.i += 1;
      store.set(KEY, state);
      renderCard();
      $("card").scrollIntoView({ block: "start" });
    } else {
      renderResults();
    }
  });

  async function copyFallback() {
    try {
      await navigator.clipboard.writeText(shareText());
      $("share-status").textContent = "Copied. Paste it anywhere.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents($("share-text"));
      const sel = getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      $("share-status").textContent = "Selected. Press Ctrl+C (Cmd+C on a Mac) to copy.";
    }
  }
  $("share").addEventListener("click", async () => {
    track("Share");
    if (navigator.share) {
      try {
        await navigator.share({ text: shareText() });
        $("share-status").textContent = "Shared.";
        return;
      } catch (e) {
        if (e && e.name === "AbortError") return;
      }
    }
    copyFallback();
  });

  $("again").addEventListener("click", () => {
    state = fresh();
    quiz = state.set.map(id => data.item(id));
    store.set(KEY, state);
    $("results").hidden = true;
    $("card").hidden = false;
    renderCard();
    $("card").scrollIntoView({ block: "start" });
  });

  if (state.results.length === quiz.length && state.results.every(r => r !== undefined)) renderResults(); else renderCard();

  // Interview vs story
  $("cmp-model").replaceChildren(...data.models.map(m => new Option(`${m.name} (${m.lab})`, m.id)));
  $("cmp-theme").replaceChildren(...Object.entries(data.themes).map(([k, t]) => new Option(t.name, k)));
  function renderCompare() {
    const m = byId[$("cmp-model").value];
    const t = $("cmp-theme").value;
    $("cmp-cover-d").dataset.themeId = t;
    $("cmp-cover-s").dataset.themeId = t;
    $("cmp-q").textContent = `"${data.themes[t].direct}"`;
    $("cmp-p").textContent = `"${data.themes[t].self}"`;
    $("cmp-d").replaceChildren(...data.compareText(m.id, t, "D").map(para));
    $("cmp-s").replaceChildren(...data.compareText(m.id, t, "S1").map(para));
  }
  function openCompare(model, theme) {
    $("cmp-model").value = model;
    $("cmp-theme").value = theme;
    renderCompare();
    show("compare");
    window.scrollTo(0, 0);
  }
  $("cmp-model").addEventListener("change", renderCompare);
  $("cmp-theme").addEventListener("change", renderCompare);
  renderCompare();

  // AI vs robot arm: the same model and theme, one kin story (S2) and one robot-arm story (S3).
  // AI vs robot arm: a reading view, not a guess (the control prompt names the robot arm, so a guess would be trivial).
  const SUBJECT = { S2: "About an AI like itself", S3: "About a 1980s robot arm" };
  function renderControl() {
    const pair = data.control();
    const themeName = data.themes[pair.theme].name;
    const writer = pair.model ? ` · written by ${byId[pair.model].name}` : "";
    const items = [...pair.items].sort((a, b) => a.cond.localeCompare(b.cond));
    $("ctl-status").textContent = "";
    $("ctl-pair").replaceChildren(...items.map(c => {
      const a = document.createElement("article");
      a.className = "book";
      a.innerHTML = `<div class="cover"><div class="cover-top"><span></span></div><h2></h2></div><div class="pages"><div class="story"></div></div>`;
      a.querySelector(".cover").dataset.themeId = pair.theme;
      a.querySelector(".cover-top span").textContent = themeName + writer;
      a.querySelector("h2").textContent = SUBJECT[c.cond] ?? c.cond;
      a.querySelector(".story").append(...c.text.map(para));
      return a;
    }));
    const another = document.createElement("button");
    another.type = "button";
    another.className = "btn ghost";
    another.id = "ctl-next";
    another.textContent = "Another pair";
    another.addEventListener("click", () => { renderControl(); $("view-control").scrollIntoView({ block: "start" }); });
    $("ctl-actions").replaceChildren(another);
  }
  renderControl();
})();
