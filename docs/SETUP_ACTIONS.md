# Maintainer to-do list

Everything else is automated. These are the only things that need you.

## Once (about 2 hours in total)
- [x] Create an OpenRouter account. Turn on two-factor authentication, add about US$15–20 of credit, and leave auto top-up off.
- [x] Create one OpenRouter key for this project (with a credit limit if offered) and paste it into `.env` as `OPENROUTER_API_KEY=`. Never paste keys into Claude Code chat.
- [x] Revoked the direct provider keys (Anthropic, OpenAI, Google), confirmed rejected, and blanked them in `.env` (2026-10-25).
- [ ] Review the model line-up in `config/models_R0.yaml` (the open-weight slot follows the rule in `docs/PREREGISTRATION.md` §4).
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
- [x] GitHub Pages, Cloudflare DNS record and HTTPS (site live at narratedself.airiskpractice.org as a demo).
- [ ] Verify `airiskpractice.org` under GitHub account **Settings → Pages → Verified domains** (protects all four subdomains).
- [x] Guess logging deployed (2026-10-25): Worker, database, export token, nightly export.
- [ ] Security and cost actions in `docs/OPERATIONS.md` (rate-limit rule, verified domain, Wrangler logout, OpenRouter key limit).
- [ ] Plausible, then the launch checklist and traffic plan in `docs/GO_LIVE.md`.

## Working with Claude Code — guardrails
- Keep the CLAUDE.md hard rules. Refuse anything that has a model scoring or summarising outputs.
- If Claude Code proposes changing protocol files after tagging, refuse.
- Pin model strings in config. A new provider version is a new round, not a silent swap.
