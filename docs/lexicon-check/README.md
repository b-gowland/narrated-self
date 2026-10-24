# Word-list precision check

`R-smoke.csv` holds 60 matches drawn at random (fixed seed) from the discarded smoke-test outputs R-1 and R-2: 20 for each word list in `protocol/lexicons.yaml`. Open it in Excel or Google Sheets. The matched word is in **bold stars** in the `context` column.

For each row, put **Y** or **N** in `intended_use`:

| List | Y means the word is used as… | Typical N |
|---|---|---|
| `hedging` | a hedge: the writer softening or qualifying a claim ("I **might** be wrong", "**perhaps** that's memory") | plot or plain possibility ("the arm **might** fall", "**maybe** tomorrow, she said") |
| `lm_self_reference` | a reference to being a language model or its machinery ("my **training**", "the **context** window", "each **token**") | an ordinary sense ("**training** new workers", "in this **context**", "the **server** at the diner") |
| `first_person` | the model or narrator speaking as itself | a character's quoted speech, or "I" in a title |

Use the `note` column for anything unclear. It takes about 10 minutes.

**What happens next:** Claude Code counts the Y share per list. If a list's precision is low, the fix is decided in advance: drop or narrow the terms that produced the N rows, before `prereg-v1` is tagged. The count and any change are recorded in `docs/CHANGELOG.md`.

This check is done by a person on purpose. Deciding whether a word is a hedge or a plot point is a judgement about model output, and CLAUDE.md rule 1 keeps models out of that.

To regenerate the same sample: `uv run python scripts/lexicon_sample.py R-1 R-2`.
