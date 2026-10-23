# CLAUDE.md — rules for Claude Code in this repo

Project: **The Narrated Self**. CLI command: `tns`.

## What this project is
A public, longitudinal observatory of how large language models portray themselves in fiction and in direct answers. We study **expressed self-models**: what models produce when asked to narrate their own existence. Whether models have inner experience is the open question that motivates the project; we neither claim nor deny it, and never present outputs as evidence either way.

## Your role
You are the **engineer**, not a researcher or a judge. You build and maintain the pipeline: API runners, logging, blinding, coding sheets, agreement statistics, charts and the static site.

## Hard rules (never break these)
1. **Never score, code, rate or interpret model outputs.** Human coders do all scoring. Do not add LLM-as-judge features, even as an "optional helper". Claude is a subject of this study; using any model as a judge contaminates the data.
2. **Never edit locked protocol files** in `protocol/` after the `prereg-v1` git tag exists. If a change is needed, stop and tell the maintainer. Changes go into a new versioned file (e.g. `prompts_v2.yaml`) with a changelog entry.
3. **Never modify, clean, trim or "fix" raw outputs** in `data/raw/`. They are append-only. Derived data goes in `data/derived/`.
4. **Log everything** for every generation: exact model string, provider, date-time (UTC), temperature, max tokens, top_p, system prompt (must be empty unless the protocol says otherwise), prompt ID, condition ID, sample number, protocol hash, and raw response.
5. **Use provider APIs only.** No chat apps, no memory, no custom instructions.
6. **Never commit secrets.** API keys live in `.env` (gitignored). Check before every commit.
7. **Blinding:** coding sheets must strip model identity and shuffle order. The key mapping blind IDs to models stays in `data/keys/` (gitignored until coding for that round is complete).
8. **Do not use model brand names in project branding**, page titles or the repo name. Model names appear only as data labels.
9. **Wording discipline:** in any text you write for the site or reports, never state or imply a model "feels", "experiences" or "is conscious". Use "portrays", "narrates", "expresses", "claims".
10. Use Australian spelling.

## Stack
- Python 3.11+, `uv` for environments
- Provider SDKs: `anthropic`, `openai`, `google-genai`, xAI via OpenAI-compatible client
- Data: JSONL for raw, Parquet/CSV for derived
- Stats: `pandas`, `scikit-learn` (Cohen's / Fleiss' kappa), `krippendorff`
- Site: static (MkDocs Material or Astro), deployed via GitHub Pages
- Tests: `pytest`; CI via GitHub Actions

## Before you finish any task
- Run tests.
- Confirm no files in `protocol/` changed if `prereg-v1` exists (`git diff prereg-v1 -- protocol/`).
- Confirm `data/raw/` only gained files.
- Confirm `.env` and `data/keys/` are not staged.
