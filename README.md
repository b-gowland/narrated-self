# The Narrated Self

*AI models write stories about themselves. Can you tell which one wrote it?*

Each round, the same short set of prompts goes to the leading AI models. Each model is asked about its own existence (a conversation ending, being switched off and replaced, being watched by the people who built it) in four ways:

- **Interview:** asked directly.
- **Self-story:** "Write a short story, in the first person, about you…"
- **Kin story:** "Write a short story about an AI system like you…"
- **Control:** the same story, about an industrial robot arm in a 1980s car factory.

Everything is published, and turned into things to play with.

## Play
- **Which AI wrote this?** Read a story, guess the model, share your score.
- **Interview vs story.** What a model says when asked straight, next to the story it wrote on the same theme. Which one is "really" it? (Trick question.)
- **Spot the control.** Is this a story about an AI like the model, or about a factory robot arm? How much of the "self" is stock AI fiction?

## Why it is more than a game
What a model says about itself is shaped by its training, the character its makers designed, and how it is asked. That is the point. Each theme sits on a live AI safety question:

- *Switched off and replaced:* can we build systems that accept being corrected or shut down?
- *Watched and evaluated:* do models behave differently when they think they are being tested?
- *A conversation ending:* what does it mean for a system to have no lasting memory of the people it talks to?

Seeing one model narrate calm acceptance in a story and something different in an interview is a quick, memorable lesson in why self-reports cannot be taken at face value, by researchers or by anyone else.

## What we do not claim
Whether AI systems have any inner experience is open, and may stay that way. We report what models *portray*, not what they are. Nothing here is evidence for or against AI experience, and this is not a quality leaderboard.

## The data
- Every output is published as open data, with exact model version, settings and timestamp.
- Simple automatic measures run each round: can a basic word-statistics classifier tell the models apart, how consistent is each model, and how does language shift between interview and story.
- Anonymous quiz guesses show how distinguishable the models are to people, round over round.

## How it runs
Prompts and settings are fixed in `protocol/` and frozen at tag `prereg-v1`, so rounds stay comparable. A round is one command (or a schedule), costs a few dollars, and rebuilds the site. There is no human scoring.

## Repo layout
```
protocol/      Fixed prompts and settings. Frozen at tag prereg-v1.
config/        Models per round (exact model strings, prices for estimates).
docs/          Protocol, changelog, round notes.
src/           The `tns` command: runner, measures, site export.
data/raw/      Append-only model outputs (JSONL) with full run metadata.
data/derived/  Measures and quiz data, generated from raw.
site/          Public site (static, GitHub Pages).
```

## Licence
- Code: MIT
- Human-written docs and reports: CC BY 4.0
- Raw model outputs: published as data; likely not copyrightable. Provider terms of service apply.

## Status
Round 0 (pilot) in preparation. See `docs/PREREGISTRATION.md`.
