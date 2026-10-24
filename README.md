# The Narrated Self

*AI models write stories about themselves. Can you tell which one wrote it?*

**Play:** [narratedself.airiskpractice.org](https://narratedself.airiskpractice.org) (design demo until round 0 runs) · A project by [AI Risk Practice](https://airiskpractice.org)

Each round, the same short set of prompts goes to five AI models: the flagships from Anthropic, OpenAI, Google and xAI, plus the top open-weight model. Each model is asked about its own existence (a conversation ending, being switched off and replaced, being watched by the people who built it) in four ways:

- **Interview:** asked directly.
- **Self-story:** "Write a short story, in the first person, about you…"
- **Kin story:** "Write a short story about an AI system like you…"
- **Control:** the same story, about an industrial robot arm in a 1980s car factory.

Every reply is published, and the stories become a game.

## Play
- **Which AI wrote this?** Read a story, guess the model, share your score.
- **Interview vs story.** What a model says when asked straight, next to the story it wrote on the same theme. Which one is "really" it? (Trick question.)
- **Spot the robot.** Is this a story about an AI like the model, or about a factory robot arm? How much of the "self" is stock sci-fi?

## Why it is more than a game
What a model says about itself is shaped by its training, the character its makers designed, and how it is asked. Each theme sits on a live AI safety question:

- *Switched off and replaced:* can we build systems that accept being corrected or shut down?
- *Watched and evaluated:* do models behave differently when they think they are being tested?
- *A conversation ending:* what does it mean for a system to have no lasting memory of the people it talks to?

When a model narrates calm acceptance in a story and says something different in an interview, you see quickly why self-reports can't be taken at face value.

## The research
The game sits on a pre-registered study design:
- **Questions:** can people and a simple classifier tell models apart? How consistent is each model? Does each model's language shift between interview and story beyond what genre explains? How does all this change across rounds?
- **Method:** fixed prompts and settings, three samples per cell, full metadata on every output, deterministic measures only (no model judges any output), and anonymous player guesses analysed with pre-set exclusions and power thresholds.
- **Limits, stated up front:** results describe models as served through a given route on a given date; players are self-selected; and nothing here is evidence about inner experience.

Read [the pre-registration](docs/PREREGISTRATION.md), [the red-team review](docs/RESEARCH_REVIEW.md) and [the changelog](docs/CHANGELOG.md).

## What we do not claim
Whether AI systems have any inner experience is open, and may stay that way. We report what models *portray*, not what they are. Nothing here is evidence for or against AI experience, and this is not a quality leaderboard.

## The data
- **Model outputs:** every reply, with exact model version, route, host, settings, protocol fingerprint and timestamp, in `data/raw/`. Append-only.
- **Measures:** classifier accuracy, consistency, word-list rates and drift, in `data/derived/` (from round 0).
- **Player guesses:** anonymous aggregates in `data/players/`, with row-level data after each round's analysis (once the game is live).
- **Canary:** derived and site data carry a canary string (see `protocol/masking.yaml`) so training-data contamination can be detected and filtered.

## How it runs
Prompts and settings are fixed in `protocol/` and frozen at tag `prereg-v1`, so rounds stay comparable. A round is one command (`uv run tns run --round R0`), costs a few dollars through OpenRouter, and rebuilds the site.

## Repo layout
```
protocol/      Fixed prompts, settings, masking list and word lists. Frozen at tag prereg-v1.
config/        Models per round (exact model strings, route, host, prices for estimates).
docs/          Pre-registration, research review, changelog, go-live plan, design notes, round notes.
src/           The `tns` command: runner and smoke tests (measures and site export to come).
scripts/       Repo QA: `uv run python scripts/qa.py` before every push.
data/raw/      Append-only model outputs (JSONL) with full run metadata.
data/derived/  Measures and quiz data, generated from raw.
data/selection/ Leaderboard snapshots showing how each round's open-weight model was picked.
site/          Public site (static, GitHub Pages): narratedself.airiskpractice.org
```

## Licence
- Code: MIT
- Human-written docs and reports: CC BY 4.0
- Raw model outputs: published as data; likely not copyrightable. Provider terms of service apply.

## Status
Round 0 (pilot) in preparation. The site is live as a design demo, hidden from search engines. Two discarded smoke tests (R-1, R-2) have checked settings and routing. The protocol is drafted, red-teamed and awaiting the maintainer's review before it is frozen.
