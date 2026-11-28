# Round 1 set-up review (28 Nov 2026)

The first Round 1 run (GitHub Actions run 46119982682) sent its prompts one model after another, reached the workflow's two-hour limit at 09:11 UTC and was cancelled. About US$5.28 was spent and no outputs were kept. This note checks every assumption behind that run against the evidence, records what was wrong, and lists what changed before the rerun.

## What went wrong

| # | Assumption | Evidence | Verdict | What changed |
|---|---|---|---|---|
| 1 | The round would take about 20 minutes | R0's own timestamps: 64 minutes (24 Oct, 10:52–11:56 UTC), models one after another, 18–26 s a call. The R1 run averaged about 47 s a call. 180 calls in a row would have needed about 2.5 hours | **Wrong.** The estimate wasn't checked against R0's logged times | Each model runs in its own job, side by side. Each job may run up to 3 hours, and one model needs about 30–45 minutes |
| 2 | A two-hour job limit was plenty | As 1 | **Wrong** | Step limit 180 minutes, job limit 200 |
| 3 | Saving outputs only at the end was safe | The runner writes each output to disk as it arrives, but the workflow saved nothing until the pull-request step. Cancelling the job discarded the runner and every output with it | **Wrong, and the costly one** | Each model's file is uploaded as an artifact when its job ends, even after a failure or a timeout. The last job always gathers whatever was saved and opens the pull request, marked partial if needed |
| 4 | A part-done round can be resumed | True on the maintainer's PC (the runner skips cells already in the file); not true in Actions, where nothing from a cancelled run reached the repo | **Wrong in CI** | New `resume_from` input: give it the `round/R1-...` branch and only missing cells are sent |
| 5 | The log would show progress | Python buffers its output when it isn't writing to a terminal, so two hours of the log were blank | **Wrong** | Output is flushed, and each call prints one line (cell, words, finish reason, seconds). Each call's time is also logged in `provider_meta.elapsed_s` |
| 6 | A round costs about US$2.52 | R0's raw files log what OpenRouter billed: **US$3.93** (Claude 2.30, GPT 1.13, Gemini 0.24, Grok 0.24, MiMo 0.02). The estimate assumed 750 output tokens a story, but R0 averaged 620–1,270 tokens a reply, hidden reasoning included, and R1's Claude about 2,100 | **Wrong.** The estimate ignored the cost already logged for R0 | Typical output is now 2,000 tokens a story and 1,500 an interview. The R1 dry run now says US$7.19, which fits what was billed. Before a round, read the previous round's logged `cost_usd` |
| 7 | The key's US$10 limit covered the round with room to spare | US$5.28 was spent on the cancelled run, so a full rerun wouldn't fit | **Wrong** | Owner raised the key limit to US$20 (28 Nov). About US$14 of account credit remains |
| 8 | Each model is served by its own lab | OpenRouter endpoints checked 28 Nov: Anthropic, OpenAI, Google AI Studio and xAI each list their own host. Kimi's `moonshotai/mxfp4` is Moonshot AI's own endpoint (Moonshot serves the model at that precision; the faster `moonshotai/highspeed` costs double) | **Holds** | None |
| 9 | R1 is comparable with R0 | Same frozen protocol (`prereg-v1`), same prompts, same route type (OpenRouter, host pinned, fallbacks off, provider-default reasoning). Grok 4.7 is unchanged, so it gives the one like-for-like comparison. The other four slots are new versions, so their changes describe a new model, not drift (`tns compare` flags this) | **Holds**, with that caveat | None |
| 10 | Reasoning is comparable across rounds | The protocol leaves reasoning at each provider's default and logs the tokens. R0 used some (means: Claude 382, Grok 402, MiMo 145, GPT 102, Gemini 0). If a lab changed its default, a change in style could partly be a change in thinking | **Holds**, with that caveat | Report reasoning tokens per model next to any change in R1 |
| 11 | The run would be unattended and safe to leave | It was safe (spend capped by the key) but not reliable (nothing kept) | **Half right** | Covered by 1–5 |

## What to check before the next round

1. Read the previous round's logged cost (`provider_meta.cost_usd`) and time per call, not just the dry run.
2. Check the key's remaining limit covers the dry-run figure plus a full retry.
3. Run the workflow; the log now shows each call. If a model's job stops part way, rerun with `resume_from`.

## For later: using the stories for short media

The owner raised the idea of short pieces (video, audio, illustrated) built from these stories to raise awareness of AI safety. This isn't a decision; it's a note so the set-up doesn't block it.

- **The raw data already supports it.** Every output is kept in full, unedited, with the exact model, date, prompt and settings. Any short can cite which output it came from.
- **Rules that carry over:** never present a story as evidence about inner experience (rule 9: "portrays", "narrates", never "feels"); no model brand names in branding (rule 8); quiz text stays masked (rule 7).
- **Keep it out of the study.** Anything made for media (new prompts, edits, picked excerpts) goes in its own folder and is never analysed, so the pre-registered measures stay clean. New prompts would be a new versioned protocol file, never an edit to `protocol/`.
- **Check before publishing:** each provider's terms on publishing outputs, and whether a voice or face in a short is synthetic (it would need labelling).
- **Fit with AI Risk Practice:** the vision puts the Narrated Self outside AI Risk Practice and frontier AI risk out of scope, pointing to others instead. A short that ends with a link to BlueDot or 80,000 Hours fits that. Building it into the practice scenarios would be a vision change for the owner.
