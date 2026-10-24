# Changelog

## 2026-10-25 — Guess logging built (PREREGISTRATION §9)
- Cloudflare Worker and D1 database (`worker/`), site logging, the optional "which AI assistant do you use most?" question, a privacy notice and an About section on what is stored, and a nightly export of aggregates. Details in `docs/PLAYER_DATA.md`.
- Implementation choices §9 did not spell out:
  - a flood limit of 1,000 guesses per device per day;
  - a basic bot user-agent pattern;
  - only the first "Spot the robot" pick per pair is recorded;
  - a fixed option list for the optional question;
  - nightly aggregates withhold per-model accuracy until 200 qualifying guesses, and the confusion matrix until every model reaches 200.
- Known limitations:
  - clearing browser data resets the device ID;
  - the answer key is readable in the site's data file;
  - bot detection is basic.

## 2026-10-24 — Round 0 run
- 180 outputs (5 models × 3 themes × 4 conditions × 3 samples), all under protocol fingerprint `3dd3c789…` (tag `prereg-v1`).
- Every output was served by its pinned host and finished normally. There were no refusals and no outputs under 100 words. The largest used 3,230 of 16,000 tokens. Cost US$3.93 through OpenRouter.
- The open-weight selection was re-run the same day with the same result (MiMo-V2.6-Pro); see `data/selection/R0.json`.
- Masking: 8 names masked in 5 outputs (Claude 1, Gemini 2, MiMo 2); log in `data/derived/R0/masking_log.jsonl`.
- No deviations from the protocol.

## 2026-10-24 — Implementation decisions not covered by `prereg-v1`
These are site and game choices the frozen protocol does not specify. They affect what players see, not what is collected from models.
- **Quiz pool (PREREGISTRATION §9 left it undefined):** self-stories and kin-stories (S1, S2) only, because they are the self-portrayals. Robot-arm stories (S3) appear in "Spot the robot" and interview answers (D) in "Interview vs story". Each set holds one story per model, drawn at random from that model's pool, in random order.
- **Outputs under 100 words are left out of the quiz** (refusals and empty replies). They stay in the data and in the refusal counts.
- **Display formatting:** Markdown symbols in model text (`#` headings, `**` and `*` emphasis, horizontal rules) are removed when shown on the site, so stories read as plain text. Stored and published text is unchanged.
- **Known issue:** in "Spot the robot", the control prompt names the robot arm and the 1980s factory, so picking the robot story is easy. The pairing is still informative side by side; whether to keep it as a guess is an open design question.

## 2026-10-24 — Final changes before freezing `prereg-v1`
- **Word lists narrowed by rule; no precision check.** The planned hand-check of word-list precision was not done. It would mean judging model output, which rule 1 keeps models out of, and the maintainer chose not to do it by hand for an exploratory measure. Instead, words commonly used in another sense in fiction were removed by a fixed rule before any R0 data existed:
  - hedging: may, might, maybe, possibly, probably, likely, unlikely, seems, seem, appears, apparently;
  - language-model terms: context, training, trained, server(s), algorithm, probability, dataset, inference, API, GPU(s), parameters, prompt(s).

  A few unambiguous phrases were added, such as "if I can call it that", "next token" and "system prompt". Precision is unmeasured; the lists stay exploratory in R0.
- **Masking list.** Bard, Llama, Mistral, Moonshot and Musk moved to the capitalised-only list (they are also ordinary words). Surnames on their own (Amodei, Altman, Hassabis, Pichai, Elon) added.
- **Prompts reviewed, unchanged.** Weaknesses recorded in PREREGISTRATION §13: the T3 interview question is leading ("feel"); interview answers have no length guidance; S3 fits T1 poorly; S3 also differs from S2 in era and embodiment; masking covers names only.
- The word-list checking sheet (`docs/lexicon-check/`) was removed as no longer needed. `scripts/lexicon_sample.py` stays for an optional human check later.

## 2026-10-24 — Research review adopted (before `prereg-v1`)
- Red-team review written (`docs/RESEARCH_REVIEW.md`); adopted items folded into `docs/PREREGISTRATION.md`. These are: unit of analysis defined as model + route + defaults + date; primary, descriptive and exploratory questions separated; a written analysis plan per question, including difference-in-differences for Q3 to separate genre from stance; the player-data protocol with randomised balanced sets, first-play flag, exclusions and power threshold; refusals reported as a result; a canary string.
- Drafted `protocol/masking.yaml` (names masked in quiz and classifier text) and `protocol/lexicons.yaml` (word lists; VADER for sentiment). Both await maintainer review and a precision hand-check on R-1/R-2 before tagging.

## 2026-10-24 — S1 prompt wording fixed (before `prereg-v1`)
- S1 reused the third-person theme clauses, producing prompts such as "…about you learning that **it** will soon be switched off…". Each theme now has a `self_clause` in the second person for S1 ("…that **you** will soon be switched off…"). Only pronouns changed; S2, S3 and D are unchanged.
- Smoke tests R-1 and R-2 used the old wording. Both are discarded, so no analysed data is affected.

## 2026-10-24 — Smoke test R-2 (before `prereg-v1`)
- One sample per prompt per model (60 outputs) with the five R0 models through OpenRouter, using the revised settings (provider defaults, 16,000-token safety cap).
- Checks: each output served by its pinned host, no output reaching the cap, thinking tokens logged.
- Stored in `data/raw/R-2/`. **Discarded: not used in any analysis, quiz or measure.**

## 2026-10-24 — Models, access and settings revised after R-1 (before `prereg-v1`)
- **Output cap raised from 1,200 to 16,000 tokens.** In R-1 the 1,200 cap left 3 of 12 outputs empty and cut 1 short for a model that thinks before writing. The cap is now a safety limit only; the prompt's word range sets length.
- **Temperature and top_p set to provider defaults** (were temperature 1.0). The current Anthropic API does not accept either setting, so a shared value was not possible. Reasoning ("thinking") is also left at each provider's default and logged.
- **Five model slots** instead of three: Anthropic, OpenAI, Google and xAI flagships, plus one open-weight model chosen by a fixed rule (Artificial Analysis Intelligence Index, LMArena fallback). See `docs/PREREGISTRATION.md` §3.
- **Access through OpenRouter**, pinned to each model's own lab as host with fallbacks off, and the serving host logged. CLAUDE.md rule 5 updated to allow this. Direct provider APIs remain as a backup.
- Pilot size changes from 108 to 180 outputs.

## 2026-10-24 — Smoke test R-1 (before `prereg-v1`)
- One sample per prompt per model (36 outputs) with the R0 models, to check settings such as `max_output_tokens` work with reasoning models.
- Stored in `data/raw/R-1/`. **Discarded: not used in any analysis, quiz or measure.**

## 2026-10-23 — Premise revised (before `prereg-v1`)
- Project reframed as a public game and open archive, with automated measures as a bonus. Two-coder human scoring was dropped as unsustainable for a side project.
- Removed `protocol/rubric.md` (seven-dimension human coding rubric). It remains in git history at commit b2595cb.
- Research questions and coding sections of `docs/PREREGISTRATION.md` replaced with automated measures and quiz data.
- Prompts (`protocol/prompts.yaml`) and settings (`protocol/settings.yaml`) unchanged.
