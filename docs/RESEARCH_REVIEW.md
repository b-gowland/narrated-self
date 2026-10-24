# Research review (red team)

Written 2026-10-24, before `prereg-v1`, to stress-test the design the way a sceptical reviewer would. It sets out what the project can credibly contribute, what could undermine each result, and what the protocol does about it. Items marked **Adopted** are written into `docs/PREREGISTRATION.md`. Items marked **Decision** need the maintainer.

A note on authorship: this review, the pipeline and the draft word lists were produced with Claude, which is also one of the models studied. The mitigations are that every measure is deterministic and public, published lexicons are preferred over custom ones, and a human reviews and owns every protocol decision.

## 1. What this project can credibly contribute

1. **A longitudinal, fixed-protocol archive of model self-portrayal.** Same prompts, same settings policy, full metadata, repeated as models change. This is rare. Most published examples are one-off and anecdotal. Even with no analysis, the dated archive is useful to later researchers.
2. **Human against machine distinguishability.** How often people can tell models apart from their self-portrayals, set against a simple classifier, with the gap tracked over time.
3. **Framing effects.** Whether what models say about themselves changes systematically between direct questions and fiction. This matters for anyone who treats model self-reports as informative, for example in model welfare or evaluation work.

What it **cannot** support, however well executed:
- claims about inner experience or its absence;
- claims about *why* a model portrays itself as it does (training data, persona design and safety tuning are all unobserved);
- rankings of models as better, safer or more honest;
- conclusions about the public at large from self-selected players.

## 2. The unit of analysis is narrower than "the model"

**Threat.** A "model" in this data is really a bundle: model version + access route + provider defaults (temperature, thinking) + host + date. R-1 and R-2 showed this directly. Through Anthropic's own API, Claude used enough thinking tokens to leave some replies empty. Through OpenRouter it thought far less. Differences between "models" may partly be differences in serving configuration.

**Adopted.**
- Every claim is stated about *model M as served via route R with provider defaults, on date D*.
- The route, host and settings sent are logged per output, as now. The route is fixed per round.
- A route change between rounds is logged as a deviation, like a protocol change.
- Report the provider-reported model version (`response_model`) and flag any change within a round, which would mean a silent model update behind a fixed name.

## 3. Threats by research question

### Q1 Distinctiveness (classifier)
- **Style, not self.** A word-statistics classifier will probably separate models almost perfectly, because LLMs have strong stylistic fingerprints: formatting, Markdown, titles, punctuation habits, favourite words. High accuracy says little about *self-portrayal*.
  - **Adopted.** Report accuracy at three levels: (a) all features; (b) after stripping formatting (Markdown, headings, bullet marks, titles); (c) function words only. Report the drop between levels. Treat the human result as primary for "self-portrayal" and the classifier as the stylistic ceiling.
- **Name leakage.** If a story mentions its own name or maker, the classifier gets a free answer.
  - **Adopted.** Classifier input uses the masked text (`protocol/masking.yaml`), the same as the game.
- **Small samples.** 36 outputs per model per round.
  - **Adopted.** Stratified 5-fold cross-validation repeated 20 times. Report the mean and a 95% interval, plus a permutation test against chance (1,000 label shuffles). Pool rounds only where stated.
- **Length.** Models write to different lengths, which a classifier can exploit.
  - **Adopted.** Report word-count distributions per model, and repeat the classifier with length-normalised features.

### Q1 Distinctiveness (players)
- **Self-selection.** Players are AI-curious, probably more expert than average. Accuracy will overstate the general public.
  - **Adopted.** Never generalise beyond "players of this game". Add one optional question: "Which AI assistant do you use most?" It isn't personal data, and it allows the analysis "do people spot the model they use?", which is a strong finding on its own.
- **Non-independence.** One player makes five guesses, and stories differ in difficulty.
  - **Adopted.** Primary analysis is a mixed-effects logistic regression: correct ~ true model + (1 | player) + (1 | story). Report per-model accuracy with cluster-bootstrap 95% intervals. Simple percentages are for the site; the model is for the paper.
- **Chance is not 20%.** Players have favourite guesses. If someone always picks "Claude", they score 20% while knowing nothing.
  - **Adopted.** Report accuracy against chance, plus balanced accuracy and Cohen's kappa from the confusion matrix, which corrects for guessing preferences.
- **Answers spreading.** Shared reveals and repeat plays inflate accuracy over time.
  - **Adopted.** The primary analysis uses **first plays only**, flagged per device by a random ID in local storage. Report accuracy by week. Sets are drawn at random from the full pool, not fixed, so no single set's answers can circulate.
- **Fixed-set and order effects.** With one fixed set of five, results reflect that set.
  - **Adopted.** Each player gets a random set, balanced so each model appears once. Story order is randomised and the set and position are recorded. Position (learning or fatigue) is a covariate.
- **Bots and junk.** Random clicking and automated traffic.
  - **Adopted.** Pre-registered exclusions:
    - guesses made under 5 seconds after the story opens (can't have read it);
    - sets with more than 5 sets from the same ID in an hour;
    - known bot user agents (counted, not stored).

    Report results with and without exclusions.
- **Power.** To detect 30% accuracy against a 20% chance level for one model, one-sided α = 0.05 with 80% power, needs about 110 independent guesses. With clustering, assume 200–300 first-play guesses per model, or roughly 250–300 completed sets in total.
  - **Adopted.** Analyse per model only once there are 200 first-play guesses for that model. Until then, report pooled accuracy only. Publish the running count.

### Q2 Consistency
- **Three samples is thin.** Within-model similarity from three samples per cell is noisy.
  - **Adopted.** Report within-model against between-model cosine similarity with bootstrap intervals, and call it descriptive in the pilot. Full rounds keep 3 samples. Within-cell variance is reused as the noise floor for Q4.

### Q3 Framing (interview against story)
- **Genre confound (the biggest single threat).** An interview answer is expository prose; a story is narrative. Word-list rates differ between them *because of genre*, whatever the model's "stance". A naive D-against-S1 comparison mostly measures genre.
  - **Adopted.** The primary Q3 analysis is a **difference-in-differences**: for each model, (S1 − S3) against the same for other models, and D against S2. Here S3, the robot-arm story, is the narrative-genre baseline. The claim is never "model X hedges more in stories"; it's "model X's interview–story gap differs from model Y's".
- **Lexicons built for human text.** Word lists validated on human writing may behave differently on LLM text. "Might" is a hedge in an essay but plot in a story ("the robot might fall").
  - **Adopted.** Published lexicons where they exist (VADER for sentiment), small transparent lists where none do (hedging, language-model self-reference). A hand-check on the R-1 and R-2 smoke data before tagging: 20 random hits per list, read for precision only, and recorded. All rates per 1,000 words.
  - **Decision.** Whether to state in the pre-registration that the lexicon measures are **exploratory** for R0. I recommend this. They become confirmatory in R1 once R0 has shown how they behave.
- **One wording per cell.** Results may reflect the exact phrasing, not the theme.
  - **Adopted as a limitation.** **Decision** for later rounds: add a second paraphrase per theme (prompts_v2) to estimate wording sensitivity.

### Q4 Drift
- **Confounds between rounds.** A change between rounds could come from:
  - a new model version (what we want to see);
  - silent provider updates under the same name;
  - route or default changes;
  - protocol changes;
  - sampling noise.
  - **Adopted.**
    - A change is reported only when it exceeds the within-round spread (3 samples per cell) and survives a permutation test across rounds.
    - Any round with a route, host or protocol change is flagged and excluded from drift claims for the affected models.
    - The open-weight slot changes model by rule, so it isn't a longitudinal series. Report it separately.
- **Reflexivity (contamination).** Published outputs and this site may end up in future training data. Later models could then be partly shaped by this project.
  - **Adopted.** A unique canary string, in the style of the BIG-bench canary, in data files and site data, so contamination can be tested for and responsible labs can filter. A test prompt for later rounds can check whether models can reproduce the canary.

## 4. Cross-cutting threats

| Threat | Why it matters | Response |
|---|---|---|
| **Researcher degrees of freedom** | Choosing measures or exclusions after seeing data inflates findings | Everything listed here is fixed before R0; anything else is labelled exploratory. **Adopted.** |
| **Weak timestamp** | A git tag can be deleted and re-created, so it proves nothing to an outside reviewer | Deposit the pre-registration on **OSF Registries** (free, immutable, timestamped) before R0, and link it from the README. **Decision:** needs your OSF account. |
| **Refusals and safety filters** | Some cells may be refused or cut short by provider filters (R-1 had one "refusal" stop). Dropping them biases results; keeping them distorts lexicon rates. | Refusals stay in the data. Report the refusal rate per model and cell as its own result. Lexicon and classifier analyses run with and without refusals. **Adopted.** |
| **Masking as an intervention** | Masking changes the text people read | The masking list is fixed in advance. Every substitution is logged, and the substitution rate per model is reported. **Adopted.** |
| **Ethics** | Anonymous game data is low risk, but journals may ask about ethics review | Collect no personal data. Show a plain notice before the first guess ("guesses are recorded anonymously for research"). **Decision** for formal publication: seek a low-risk ethics exemption, via an institution or an independent review body. |
| **Provider terms** | Publishing outputs at scale may touch provider terms | Outputs are published as research data with attribution. Check each provider's terms on publishing outputs before launch. **Decision:** your read of the terms. |
| **Engineer is a subject** | Claude built the pipeline and drafted lists | Deterministic code, published lexicons where possible, human review of every list. Stated openly in the paper. **Adopted.** |

## 5. Dependencies
- **OpenRouter** (routing), the **providers' defaults** (which can change without notice), and **Artificial Analysis** (open-weight selection; its index version is recorded).
- **Cloudflare** (player data collection, to be built) and **GitHub Pages** (site).
- **Players:** findings on human distinguishability need roughly 250–300 completed sets. With no traffic there is no Q1 human result, so the traffic plan is a research dependency, not just marketing.

## 6. Path to a real research output
1. **Before R0:** lock the protocol, including this review's adopted items. Tag `prereg-v1` and deposit on OSF.
2. **R0 (pilot):** archive and descriptive results. Use it to check that lexicons, masking and logging behave. No confirmatory claims.
3. **Data deposit:** each round on Zenodo with a DOI, plus the canary.
4. **R1 onward:** confirmatory analyses on lexicons and drift. Player results once the power thresholds are met.
5. **Write-up:** a preprint (arXiv or PsyArXiv) and a workshop paper. Venues on evaluation, model behaviour or AI welfare, such as workshops at NeurIPS, ICLR or FAccT, fit a careful descriptive study of this kind.

## 7. Decisions for the maintainer
1. Make lexicon measures exploratory for R0 (recommended: yes).
2. Deposit the pre-registration on OSF before R0 (recommended: yes).
3. Add the optional "Which AI assistant do you use most?" question (recommended: yes).
4. Add a second paraphrase per theme from R1 (recommended: yes, as `prompts_v2.yaml`).
5. Ethics exemption, if aiming at formal publication.
6. Check provider terms on publishing outputs.
