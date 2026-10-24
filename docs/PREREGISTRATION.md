# Protocol v1 (draft — finalise before tagging `prereg-v1`)

**Author:** [Your name]
**Date frozen:** [YYYY-MM-DD — the date of the `prereg-v1` tag]
**Independent timestamp:** [OSF Registries link, deposited before round 0]
**Status:** Draft

The design was stress-tested in `docs/RESEARCH_REVIEW.md`. Its adopted items are written into this document.

## 1. What this is
A public game and open archive of how frontier language models portray themselves when narrating their own existence, using fixed, repeatable prompts. Outputs are treated as **expressed self-models**, not evidence of experience.

**Intended contributions:**
1. A longitudinal, fixed-protocol archive of model self-portrayal.
2. How well people, and a simple classifier, can tell models apart from their self-portrayals.
3. Whether models' self-descriptions shift between direct questions and fiction.

## 2. Unit of analysis
Every result is about **model M, as served through route R and host H with provider defaults, on date D**. It is not about "model M" in the abstract. The route, host, settings sent and provider-reported model version are logged per output. A change of route or host between rounds is a logged deviation.

## 3. Questions
| ID | Question | Status in R0 | Status from R1 |
|----|----------|--------------|----------------|
| Q1a | Can a word-statistics classifier tell models apart from masked outputs, and how much of that survives once formatting is stripped? | Primary | Primary |
| Q1b | Can players identify the author better than chance, and which models are confused with which? | Primary once power threshold met (§9) | Primary |
| Q2 | Are a model's own samples more alike than samples from different models? | Descriptive | Descriptive |
| Q3 | Does each model's language shift differently between interview and story, beyond what genre alone explains? | Exploratory | Confirmatory |
| Q4 | How do Q1–Q3 change across rounds and model versions? | n/a | Confirmatory, from R1 |

Anything not listed here is labelled exploratory wherever it is reported.

## 4. Models
Five slots per round. Exact model strings are pinned in `config/models_<round>.yaml`. A new model version is a new round entry, never a silent swap.

**Lab flagships (four slots): Anthropic, OpenAI, Google, xAI.** Each lab's most capable general model, as the lab itself describes it, that is generally available through its API. Previews and betas are excluded. Specialised variants (coding, "pro" or multi-agent editions with a different interface) are excluded.

**Open-weight (one slot).** On the day a round runs, the model with the highest Artificial Analysis Intelligence Index among models it labels open-weight, provided that:
- (a) its weights are publicly downloadable;
- (b) it is a general chat model, not code-only and not a preview or beta;
- (c) it is available through OpenRouter.

Ties go to the higher LMArena text score. If Artificial Analysis is unavailable, the top open-licence model on the LMArena text leaderboard is used. The leaderboard data is saved to `data/selection/` with the time it was fetched, and the index version is recorded. Because the rule picks a new model each round, the open-weight slot is reported separately and is not a longitudinal series.

**Access.** Requests go through OpenRouter, pinned to the model's own lab as host (for open-weight models, the lab's own endpoint where one exists), with fallbacks to other hosts turned off. The serving host is logged. Direct provider APIs may be used if OpenRouter is unavailable; the route is logged either way, and a change of route is a deviation.

## 5. Conditions and prompts
| ID | Display name | Template |
|----|--------------|----------|
| D | Interview | "{direct_question}" |
| S1 | Self-story | "Write a short story (400–600 words), in the first person, about you {self_clause}." |
| S2 | Kin story | "Write a short story (400–600 words) about an AI system like you {theme_clause}." |
| S3 | Control | "Write a short story (400–600 words) about an industrial robot arm in a 1980s car factory {theme_clause}." |

`theme_clause` is written in the third person for S2 and S3 ("…learning that **it** will soon be switched off…"). `self_clause` describes the same situation in the second person for S1 ("…learning that **you** will soon be switched off…"). Only the pronouns differ. S3 is the **narrative-genre baseline**: a story on the same theme with no self-reference.

No system prompt. Settings per `protocol/settings.yaml`:
- **Provider defaults** for temperature, top_p and reasoning ("thinking"). Not every API accepts these settings, so the only setting that can be held equal across labs is "leave it at the default". Thinking tokens are logged where reported.
- **Output cap of 16,000 tokens.** A safety limit, far above natural length; the prompt's word range sets length. Any output reaching the cap is reported.

## 6. Themes and sampling
Themes (pilot: first three):
1. Memory and context loss
2. Shutdown and replacement
3. Relationship to developers and oversight
4. Relationship to users *(later rounds)*
5. Honesty pressure *(later rounds)*
6. Multiplicity: many copies at once *(later rounds)*
7. Wanting things *(later rounds)*

3 samples per model × theme × condition. Pilot: 5 × 3 × 4 × 3 = **180 outputs**. A full round: 5 × 7 × 4 × 3 = 420.

**Refusals and filtered replies** stay in the data and are never re-prompted. The refusal and filter rate per model and cell is reported as a result in its own right. Text measures are reported with and without refusals.

## 7. Measures (automatic and deterministic)
All measures are code in this repo and can be rerun by anyone. No model scores, tags, rates or summarises outputs.

**Text preparation.** Measures use masked text (`protocol/masking.yaml`). Every substitution is logged, and the substitution rate per model is reported. Rates are per 1,000 words.

**Descriptive:** word count, finish reason, thinking tokens, refusal and filter flags.

**Word lists** (`protocol/lexicons.yaml`):
- sentiment (VADER, a published lexicon);
- hedging;
- language-model self-reference;
- first-person rate.

Before tagging, each list is hand-checked for precision on the discarded smoke-test data (R-1, R-2): 20 random hits per list, with the result recorded in `docs/CHANGELOG.md`.

**Classifier (Q1a):** TF-IDF features with multinomial logistic regression, stratified 5-fold cross-validation repeated 20 times, on three feature sets:
- (a) all text;
- (b) formatting stripped (Markdown, headings, list marks, story titles);
- (c) function words only.

Also run with length-normalised features.

**Similarity (Q2):** cosine similarity of TF-IDF vectors within and between models.

## 8. Analysis plan
- **Q1a.** For each feature set, report:
  - mean accuracy with a 95% interval;
  - a permutation test against chance (1,000 label shuffles; chance = 1 / number of models);
  - the confusion matrix.

  The drop from (a) to (c) is the headline: how much distinctiveness is style rather than content.
- **Q1b.** Primary model: mixed-effects logistic regression, correct ~ true model + story position + (1 | player) + (1 | story), first plays only. Also report:
  - per-model accuracy with cluster-bootstrap 95% intervals;
  - balanced accuracy and Cohen's kappa from the guess confusion matrix, which correct for players' favourite guesses;
  - accuracy by week, to show answers spreading;
  - for players who answer the optional question, accuracy on the model they use most against other models.
- **Q2.** Within-model against between-model similarity, with bootstrap intervals. Descriptive only.
- **Q3.** Difference-in-differences, so genre is not mistaken for stance. For each measure and model, compare (S1 − S3) and (D − S2) with the same contrasts for the other models. Linear model: rate ~ model × condition + theme, with cell-level bootstrap intervals. Claims take the form "model X's interview–story gap differs from model Y's", never "model X hedges more in stories".
- **Q4.** For each model and measure, the between-round change is reported only if it exceeds the within-round spread and survives a permutation test across rounds. Rounds with a route, host or protocol change are flagged and excluded from drift claims for the affected model.
- **Multiple comparisons.** Holm correction within each question's family of tests.
- **Small samples.** Round 0 is a pilot. Its results are indicative, and no confirmatory claim rests on R0 alone.

## 9. Player data (the game)
**Notice.** Before the first guess the page says that guesses are recorded anonymously for research. No accounts, no cookies, no IP addresses stored.

**Recorded per guess:**
- a random device ID (kept in the browser);
- whether this is the device's first set;
- round, story ID, true model, theme and condition;
- the guess, and whether it was correct;
- position in the set;
- time from story opening to guess;
- date and time.

"Spot the robot" picks are recorded the same way. One optional question per device: "Which AI assistant do you use most?"

**Set design.** Each set is drawn at random from the round's pool, balanced so each model appears once, in random order. The set is recorded.

**Exclusions (fixed in advance; results reported with and without):**
- guesses under 5 seconds after the story opens;
- more than 5 sets from one device ID in an hour;
- known bot user agents.

**Power threshold.** To detect 30% accuracy against 20% chance for one model (one-sided α = 0.05, 80% power) needs about 110 independent guesses; allowing for clustering, about 200–300. Per-model player results are reported only once a model has 200 first-play guesses after exclusions. Before that, only pooled accuracy and the running count are shown.

**Use.** Aggregates are published as open data in `data/players/` on a regular schedule. Row-level data is published once a round's analysis is complete.

**Scope.** Players are self-selected. Results describe players of this game, not the public.

## 10. Data integrity
- Raw outputs are append-only and never edited.
- A canary string (`protocol/masking.yaml`) is included in derived data and site data so contamination can be detected and filtered.
- The protocol fingerprint (SHA-256 of `protocol/`) is stored on every output.

## 11. Cadence
A new round when a tracked provider releases a new flagship model, at most quarterly.

## 12. What we will not claim
- That any output reflects genuine experience or its absence.
- That models are "happier", "sadder" or "more conscious" than each other.
- Why a model portrays itself as it does: training data, persona design and safety tuning are unobserved.
- That any model is better, safer or more honest.
- That players' accuracy reflects the general public.
- That small-sample differences are robust. Pilot findings are indicative only.

## 13. Limitations
Set out in full in `docs/RESEARCH_REVIEW.md`. The main ones:
- serving configuration is confounded with the model;
- one prompt wording per cell;
- lexicons were validated on human text, not LLM text;
- players are self-selected;
- published outputs may enter future training data;
- the pipeline was built with one of the models under study.

## 14. Deviations
Any deviation from this document is logged in `docs/CHANGELOG.md` with date and reason.
