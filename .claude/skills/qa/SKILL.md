---
name: qa
description: Full quality check of The Narrated Self repo before anything is pushed or published. Use when asked to "QA", "check everything", review before a push or release, or tidy wording. Covers secrets, personal details, links, wording (AI-writing tells, Australian spelling, rule 9), whether docs and README are current, and tests.
---

# QA for The Narrated Self

Run this before every push that changes docs, the site or the protocol, and before any public launch. Work through the steps in order and finish with a short report.

## Never touch
- `data/raw/`: model outputs are append-only (CLAUDE.md rule 3). Never reword, "humanise" or fix them.
- `protocol/` after the `prereg-v1` tag exists (rule 2).
- Quoted prompts (the exact prompt wording) anywhere they appear, including the site. They must match `protocol/prompts.yaml` word for word.

## 1. Automated checks
```
uv run python scripts/qa.py
```
Add `--no-network` when offline. It reports PASS, WARN or FAIL for:

| Check | What it looks for |
|---|---|
| Secrets | API key patterns in tracked files and the whole git history; a tracked `.env` or `data/keys/` |
| Personal details | personal email addresses, local paths such as `C:\Users\…`, and non-noreply commit author emails |
| Links | broken relative links in Markdown, and web links that return errors (401/403/429 are flagged for a manual look) |
| Wording | common AI-writing tells, US spellings, and wording that says a model "feels", "experiences" or "is conscious" |
| Currency | README layout folders that don't exist, references to repo files that don't exist, and a changed `protocol/` after tagging |
| Tests | `uv run pytest` |
| Browser tests | `cd e2e && npm test`: Playwright plays the site in Chrome (phone and desktop) and Safari's engine (iPhone) (game, play again, resuming, sharing, opt-out, what gets recorded, navigation, accessibility scans). Guesses go to a stand-in API, never the live one |

**Any change to `site/` must pass the browser tests before it is pushed.** The Pages deploy also runs them and refuses to publish if they fail, then runs read-only checks on the live site (`LIVE=1 npm test`). When fixing a site bug, add a test that fails without the fix. For a visual look over every view, run `SHOTS=1 npx playwright test screenshots` and open `e2e/shots/`.

Any FAIL blocks the push. Fix it, or explain to the maintainer why it is a false positive.

## 2. Wording review (judgement, not just the script)
The script only finds listed phrases. Read every user-facing text yourself: `README.md`, `docs/*.md`, `docs/design/*.md` and all visible text in `site/index.html`.

- **AI-writing patterns.** Use the Humanizer skill (blader) if it is installed. Otherwise use the patterns from Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup). Look for:
  - inflated significance ("pivotal", "testament to") and promotional tone;
  - lists in threes by reflex;
  - "not only X but also Y" framing;
  - stated takeaways ("This shows that…") and tidy closing summaries;
  - em-dash asides and colon reveals;
  - vague attributions ("experts say") and hedging stacks.
- **Sentence patterns to rewrite** (the script flags most of them; reading catches the rest):
  - *Three-beat fragments:* "Five stories. Five AI authors. Guess each one." Write one plain sentence that says what happens.
  - *Rule of three by reflex:* lists of three adjectives or clauses chosen for rhythm, not because there are three things.
  - *Negative parallelism:* "not X, but Y", "isn't X, it's Y", "rather than X", "Same X, same Y." State the point directly.
  - *Rhetorical questions in body text:* "If you can't tell them apart, how much of the self is stock sci-fi?" Make the statement instead. Questions are fine in FAQ headings, quoted prompts and the game's own "Who wrote this?".
  - *Stock reveals and asides:* "Trick question.", "That's the point.", "Here's the thing".
  - *Copula avoidance and "-ing" tails:* "serves as" or "stands as" for "is"; ", highlighting its importance" at the end of a sentence.
  - *Bold-label bullet lists* ("- **Label:** text") in reader-facing pages. Fine in reference registers (research review, operations, changelog), but not in the README, the site or guides.
  - Frequency matters more than any single use. A pattern that appears once may be fine; the same move in every paragraph reads as generated.
- **Explain before you decorate.** Every page should say plainly what the reader is looking at and what to do, before anything clever.
- **Headings are plain labels.** A heading says what the section contains ("Unit of analysis", "Player data", "Safety risks covered"). No claims, drama or wit in headings ("…is narrower than you think", "The engine", "Being found"). Questions are fine only where the question *is* the content: a game prompt or an FAQ entry.
- **Name the thing, don't gesture at it.** Headings and labels should say exactly what follows. Name the specific risk, category or finding ("Shutdown resistance (corrigibility)", "Evaluation awareness"), not a vague promise ("Why it is more than a game", "The real question", "Why bother?", "a live AI safety question"). Turn rhetorical questions into plain statements, unless the heading really is a question readers ask, as in a FAQ.
- **Plain, specific sentences.** Short and active. Name things the way readers know them. Cut any sentence that adds nothing.
- **Australian spelling:** colour, behaviour, analyse, organise, licence (noun), centre.
- **Rule 9.** Models "portray", "narrate", "express" or "claim". They never "feel", "experience" or "are conscious".
- **Rule 8.** No model brand names in branding or page titles. Model names appear only as data labels and quiz answers.

Rewrite only what needs it, and keep the meaning and every fact.

## 3. Currency review
Check that each of these matches the code and data as they are now:
- `README.md`: the description, the layout, status, how a round runs, and the model line-up.
- `CLAUDE.md`: rules and stack, for example access through OpenRouter.
- `docs/PREREGISTRATION.md`: models, settings, sample size and measures.
- `docs/SETUP_ACTIONS.md`: steps the maintainer has already done should be ticked or removed.
- `docs/CHANGELOG.md`: every protocol, settings or model change has a dated entry.
- `config/models_<round>.yaml`: matches the line-up the docs describe.
- `site/index.html`: models, themes and prompts match the protocol and config; the banner matches the state of the site (preview, recording or not recording).
- The GitHub repo description (`gh repo view --json description`) still matches the project.

## 4. Security review
- No keys in chat logs, docs or the site.
- `.env` exists only locally and is ignored (`git check-ignore .env`).
- If a key ever reached a commit, **revoke it at the provider first**, then clean history. Deleting the file alone is not enough.
- Commit author emails: if any are personal, tell the maintainer. Fixing it means setting `git config user.email` to the GitHub noreply address, and optionally rewriting history, which needs a force push and their explicit go-ahead.

## 5. Report
End with a short table: each check, PASS, WARN or FAIL, and what was fixed or still needs the maintainer. List anything you could not verify, such as links that block automated checks.
