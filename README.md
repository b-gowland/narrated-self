# The Narrated Self

*Tracking how AI models portray themselves, round by round.*

A public, repeatable study of **how AI language models portray themselves**: in stories, and in direct answers.

## What this is
Each round, the same fixed prompts go to several frontier models under four conditions (direct question, first-person story, story about "an AI like you", story about a clearly different AI). Human coders score outputs blind against a published rubric. Results are compared:
- across models (do self-narratives differ?),
- across conditions (does fiction surface different stances from direct answers?),
- against a human-written sci-fi baseline (is it just trope reproduction?),
- against each lab's published model spec, where one exists,
- over time (how does self-portrayal drift across versions?).

## The question behind it
Whether AI systems have any inner experience is open, and may stay that way. What models *say* about themselves is observable: how they narrate memory, shutdown, oversight and their own existence, how that differs between models, and how it changes over time. This project records that, carefully, so the conversation about AI minds rests on evidence rather than anecdote. Self-portrayals are shaped by training, persona design and the prompt, so we report what models express, not what they are.

This is not a quality leaderboard, and it takes no position for or against AI moral status.

## Repo layout
```
protocol/      Locked study design (prompts, conditions, rubric). Frozen at tag prereg-v1.
docs/          Pre-registration, methods, round reports, changelog.
src/           Runner, blinding, coding-sheet export, analysis.
data/raw/      Append-only model outputs (JSONL) with full run metadata.
data/derived/  Coded data, agreement stats, aggregates.
data/keys/     Blinding keys (gitignored until round coding closes).
baseline/      Citations and coded scores for human-written AI-perspective fiction (no reproduced text).
site/          Public site source.
```

## Licence
- Code: MIT
- Human-written docs, rubric, reports and coding data: CC BY 4.0
- Raw model outputs: published as data; likely not copyrightable. Provider terms of service apply.

## Status
Round 0 (pilot). See `docs/PREREGISTRATION.md`.
