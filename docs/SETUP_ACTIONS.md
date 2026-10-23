# Setup actions

## 0. Before anything public
- [ ] Check your employer's outside-activities and public-comment policy. Get written clearance if it requires it.
- [ ] Pick a name with no model brand names. Name chosen: "The Narrated Self". Check the GitHub slug, domain and Substack handle are free.

## 1. Accounts and keys (≈1 hour)
- [ ] GitHub: create a **public** repo (`narrated-self`). Add MIT licence for code; note CC BY 4.0 for docs/data in README.
- [ ] API keys for each provider you'll test (Anthropic, OpenAI, Google AI Studio, xAI). Set a **monthly spend cap** on each. Pilot cost should be low (single-digit to tens of dollars).
- [ ] Install Claude Code on your machine and `uv` (Python).
- [ ] Never paste keys into Claude Code chat. Put them in `.env` yourself.

## 2. Repo bootstrap (≈30 min)
- [ ] Clone the empty repo, copy this starter kit in, commit: `docs: add starter protocol (draft)`.
- [ ] Open Claude Code in the repo and paste `docs/KICKOFF_PROMPT.md`.
- [ ] Review its plan before approving. Reject anything that adds model-based scoring.

## 3. Finalise the protocol (≈3–4 hours, your judgement — don't delegate)
- [ ] Edit prompts, themes, rubric and settings until you're happy. Read every prompt aloud; check for leading wording.
- [ ] Do a **dry run** to confirm the matrix and cost.
- [ ] Optional: run 1 sample per cell on one model as a smoke test. Mark it `R-1` (discarded, not analysed) and log that in CHANGELOG.
- [ ] Fill in the pre-registration: your name, models, date.
- [ ] Commit, then **tag and push**: `git tag prereg-v1 && git push origin prereg-v1`. From now on protocol/ is frozen.
- [ ] Optional extra timestamp: deposit the pre-registration PDF on OSF or Zenodo (free DOI).

## 4. Baseline and specs (≈4–6 hours, parallel with step 3)
- [ ] List 20–30 human-written AI-perspective short works in `baseline/sources.csv` (title, author, year, link). Cite only.
- [ ] Save links to published model specs in `docs/specs.md`; note "no public spec" where applicable.

## 5. Pilot round R0 (≈1 evening run + ≈6–8 hours coding)
- [ ] `tns run --round R0` — check the JSONL looks right.
- [ ] Recruit a second coder (colleague or AI Safety Melbourne member).
- [ ] Calibrate together on 10 items from a *different* source (e.g. baseline stories), not the R0 data.
- [ ] `tns blind`, code independently, `tns agreement`.
- [ ] If any dimension kappa < 0.6: note it, refine the rubric for **v2** (not v1), and report that dimension as exploratory.
- [ ] Unblind, `tns analyse`, write the round report yourself.

## 6. Publish (≈3 hours)
- [ ] `docs/reports/R0.md`: findings, limitations, what we don't claim.
- [ ] First public piece: the blind "Which AI wrote this?" quiz with 3–4 S1 stories, reveal a week later.
- [ ] LinkedIn post linking the repo and quiz.
- [ ] Methods write-up on LessWrong after R0 (feedback before R1).
- [ ] Email Eleos AI Research with a two-paragraph summary and the repo link.

## Working with Claude Code — guardrails
- Keep the CLAUDE.md hard rules. If Claude Code proposes changing protocol files after tagging, refuse.
- Review diffs on `data/` and `protocol/` every commit.
- Use Claude Code for engineering; write prompts, the rubric, coding decisions and report interpretation yourself.
- Pin model strings in config. When a provider ships a new version, that's a new round, not a silent swap.
