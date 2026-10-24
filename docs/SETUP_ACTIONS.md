# Your to-do list (the human bits)

Everything else is automated. These are the only things that need you.

## Once (about 2 hours in total)
- [x] Create an OpenRouter account. Turn on two-factor authentication, add about US$15–20 of credit, and leave auto top-up off.
- [x] Create one OpenRouter key for this project (with a credit limit if offered) and paste it into `.env` as `OPENROUTER_API_KEY=`. Never paste keys into Claude Code chat.
- [ ] Revoke the direct provider keys (Anthropic, OpenAI, Google) in each console, then clear them from `.env`. OpenRouter passed smoke test R-2, so they are no longer needed.
- [ ] Review the model line-up in `config/models_R0.yaml` (the open-weight slot follows the rule in `docs/PREREGISTRATION.md` §3).
- [x] Dry run: `uv run tns run --round R0 --dry-run`.
- [ ] Read the prompts aloud once. Fix anything that sounds leading. Review the word lists once they are drafted.
- [ ] Fill in your name and the date in `docs/PREREGISTRATION.md`, commit, then tag and push: `git tag prereg-v1` and `git push origin prereg-v1`. From then on `protocol/` is frozen.

## Each round (about 15 minutes)
- [ ] Make a new `config/models_<round>.yaml`: the current lab flagships, plus the open-weight model picked by the rule (save the leaderboard page to `data/selection/`).
- [ ] Run the round (or let the schedule run it), then skim the site.
- [ ] Optional: write a short note in `docs/rounds/`.
- [ ] Before pushing anything public: `uv run python scripts/qa.py` (or ask Claude Code to run the `qa` skill).

## Going live and sharing
- [ ] Follow `docs/GO_LIVE.md`: GitHub Pages, the Cloudflare DNS record, Plausible, then the launch checklist and traffic plan.

## Working with Claude Code — guardrails
- Keep the CLAUDE.md hard rules. Refuse anything that has a model scoring or summarising outputs.
- If Claude Code proposes changing protocol files after tagging, refuse.
- Pin model strings in config. A new provider version is a new round, not a silent swap.
