# Changelog

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
