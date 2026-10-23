# Your to-do list (the human bits)

Everything else is automated. These are the only things that need you.

## Once (about 2 hours in total)
- [ ] Check your employer's outside-activities and public-comment policy. Get written clearance if it requires it.
- [ ] Get API keys for three providers (for example Anthropic, OpenAI, Google AI Studio). Set a **monthly spend cap** of about US$10 on each.
- [ ] Copy `.env.example` to `.env` and paste the keys in yourself. Never paste keys into Claude Code chat.
- [ ] Fill in the exact model strings (and prices, for the estimate) in `config/models_R0.yaml`.
- [ ] Dry run: `uv run tns run --round R0 --dry-run`. Check the prompts and the cost.
- [ ] Read the prompts aloud once. Fix anything that sounds leading. Review the word lists once they are drafted.
- [ ] Fill in your name and the date in `docs/PREREGISTRATION.md`, commit, then tag and push: `git tag prereg-v1` and `git push origin prereg-v1`. From then on `protocol/` is frozen.

## Each round (about 15 minutes)
- [ ] When a provider ships a new flagship model, add its exact string to a new `config/models_<round>.yaml`.
- [ ] Run the round (or let the schedule run it), then skim the site.
- [ ] Optional: write a short note in `docs/rounds/`.

## Sharing (whenever you like)
- [ ] Post the quiz link on LinkedIn.
- [ ] After a round or two, a methods post on LessWrong.
- [ ] Email Eleos AI Research a two-paragraph summary and the repo link.

## Working with Claude Code — guardrails
- Keep the CLAUDE.md hard rules. Refuse anything that has a model scoring or summarising outputs.
- If Claude Code proposes changing protocol files after tagging, refuse.
- Pin model strings in config. A new provider version is a new round, not a silent swap.
