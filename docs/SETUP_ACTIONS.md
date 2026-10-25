# Maintainer to-do list

Everything else is automated. These are the only things that need you.

## Once (about 2 hours in total)
- [x] Create an OpenRouter account. Turn on two-factor authentication, add about US$15–20 of credit, and leave auto top-up off.
- [x] Create one OpenRouter key for this project (with a credit limit if offered) and paste it into `.env` as `OPENROUTER_API_KEY=`. Never paste keys into Claude Code chat.
- [x] Revoked the direct provider keys (Anthropic, OpenAI, Google), confirmed rejected, and blanked them in `.env` (2026-10-25).
- [x] Model line-up for R0 set and re-checked on the run day (`config/models_R0.yaml`, `data/selection/R0.json`).
- [x] Dry run: `uv run tns run --round R0 --dry-run`.

## Before freezing the protocol
- [x] Decisions in `docs/RESEARCH_REVIEW.md` §7 (made 2026-10-24).
- [x] Prompts and masking list reviewed (by Claude Code, at the maintainer's request); weaknesses recorded in PREREGISTRATION §13.
- [x] Word lists narrowed by rule instead of a hand-check (see CHANGELOG).
- [x] Protocol frozen: tag `prereg-v1` and GitHub release.

## Each round (about 15 minutes)
- [ ] Make a new `config/models_<round>.yaml`: the current lab flagships, plus the open-weight model picked by the rule (save the leaderboard page to `data/selection/`).
- [ ] Run the round (or let the schedule run it), then skim the site.
- [ ] Optional: write a short note in `docs/rounds/`.
- [ ] Before pushing anything public: `uv run python scripts/qa.py` (or ask Claude Code to run the `qa` skill).

## Going live and sharing
- [x] GitHub Pages, Cloudflare DNS record and HTTPS (site live at narratedself.airiskpractice.org; open to search engines from 2026-10-25).
- [x] Verified `airiskpractice.org` under GitHub account **Settings → Pages → Verified domains** (2026-10-26; protects all four subdomains).
- [x] Guess logging deployed (2026-10-25): Worker, database, export token, nightly export.
- [x] Security and cost actions in `docs/OPERATIONS.md` (rate-limit rule 2026-10-25; Wrangler logged out, domain verified and OpenRouter key limit set to US$25 on 2026-10-26).
- [x] Plausible (2026-10-25), then the launch checklist in `docs/GO_LIVE.md`.

## Working with Claude Code — guardrails
- Keep the CLAUDE.md hard rules. Refuse anything that has a model scoring or summarising outputs.
- If Claude Code proposes changing protocol files after tagging, refuse.
- Pin model strings in config. A new provider version is a new round, not a silent swap.
