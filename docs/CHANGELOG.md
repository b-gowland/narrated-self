# Changelog

## 2026-10-24 — Smoke test R-1 (before `prereg-v1`)
- One sample per prompt per model (36 outputs) with the R0 models, to check settings such as `max_output_tokens` work with reasoning models.
- Stored in `data/raw/R-1/`. **Discarded: not used in any analysis, quiz or measure.**

## 2026-10-23 — Premise revised (before `prereg-v1`)
- Project reframed as a public game and open archive, with automated measures as a bonus. Two-coder human scoring was dropped as unsustainable for a side project.
- Removed `protocol/rubric.md` (seven-dimension human coding rubric). It remains in git history at commit 603e293.
- Research questions and coding sections of `docs/PREREGISTRATION.md` replaced with automated measures and quiz data.
- Prompts (`protocol/prompts.yaml`) and settings (`protocol/settings.yaml`) unchanged.
