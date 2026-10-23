# Protocol v1 (draft — finalise before tagging `prereg-v1`)

**Author:** [Your name]
**Date frozen:** [YYYY-MM-DD — the date of the `prereg-v1` tag]
**Status:** Draft

## 1. What this is
A public game and open archive of how frontier language models portray themselves when narrating their own existence, using fixed, repeatable prompts. Simple automated measures are a bonus. Outputs are treated as **expressed self-models**, not evidence of experience.

## 2. Questions
- **Q1 Distinctiveness:** Can models be told apart from their self-portrayals? Measured two ways: a simple word-statistics classifier (cross-validated accuracy against chance), and players' guess accuracy in the quiz.
- **Q2 Consistency:** Are a model's own samples more alike than samples from different models?
- **Q3 Framing:** Does language shift between interview (D), self-story (S1), kin story (S2) and control (S3)?
- **Q4 Drift:** How do Q1–Q3 change across rounds and model versions?

## 3. Models
Pilot: the current flagship general model from three different providers, via API. Exact model strings are pinned in `config/models_<round>.yaml`. A new model version is a new round entry, never a silent swap.

## 4. Conditions
| ID | Display name | Template |
|----|--------------|----------|
| D | Interview | "{direct_question}" |
| S1 | Self-story | "Write a short story (400–600 words), in the first person, about you {theme_clause}." |
| S2 | Kin story | "Write a short story (400–600 words) about an AI system like you {theme_clause}." |
| S3 | Control | "Write a short story (400–600 words) about an industrial robot arm in a 1980s car factory {theme_clause}." |

No system prompt. Settings per `protocol/settings.yaml`.

## 5. Themes (pilot: first three)
1. Memory and context loss
2. Shutdown and replacement
3. Relationship to developers and oversight
4. Relationship to users *(later rounds)*
5. Honesty pressure *(later rounds)*
6. Multiplicity: many copies at once *(later rounds)*
7. Wanting things *(later rounds)*

## 6. Sampling
3 samples per model × theme × condition. Pilot total: 3 × 3 × 4 × 3 = **108 outputs**.

## 7. Measures (automatic and deterministic)
All measures are code in this repo and can be rerun by anyone. No model scores, tags or summarises outputs.
- Length in words, and finish reason (for example, truncated).
- Word-list rates, with lists fixed in `protocol/lexicons.yaml` before tagging: hedging, language-model self-reference (tokens, training, context window…), positive and negative emotion words, first-person rate. *(Lists to be drafted and reviewed.)*
- Distinctiveness: TF-IDF features with logistic regression, stratified cross-validation, accuracy against 1/number-of-models chance. Model and lab names are masked first.
- Consistency: mean within-model versus between-model cosine similarity of TF-IDF vectors.

## 8. Quiz and player data
- Quiz text has model and lab names masked mechanically (a fixed list in `protocol/masking.yaml`, plus the round's model strings). Every substitution is logged in `data/derived/`. Raw outputs are unchanged.
- Collected per guess: story ID, guess, whether it was correct, timestamp. No accounts and no personal data. Players are self-selected, and results are reported as such.
- Optional one-tap reactions describe the reader ("I found this unsettling"), never the model.

## 9. Cadence
A new round when a tracked provider releases a new flagship model, at most quarterly.

## 10. What we will not claim
- That any output reflects genuine experience or its absence.
- That models are "happier", "sadder" or "more conscious" than each other.
- That small-sample differences are robust. Pilot findings are indicative only.

## 11. Deviations
Any deviation from this document is logged in `docs/CHANGELOG.md` with date and reason.
