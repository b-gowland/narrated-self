# Similar sites: catalogue and design direction

Compiled 2026-10-24. Sites are grouped by what we can learn from them. Details marked *(from listings)* come from third-party descriptions and have not been checked on the site itself.

## 1. "Can you tell?" guessing games

| Site | What it does | What to take from it |
|---|---|---|
| **Human or Not?** (AI21 Labs, 2023) | Two-minute chat with a person or a bot, then guess which. Over 2 million players and 15 million conversations; players identified bots correctly only 60% of the time. | The headline number *was* the story. A single striking statistic ("people got it right X% of the time") travels further than any chart. Plan to publish ours. |
| **Bot or Not** (Sam Illingworth, itch.io) | Ten quotes, five human and five AI. After each guess it explains who wrote it and why it was hard. | The reveal is the teaching moment. Explain after each answer, not at the end. |
| **AI Text Quiz** (gradually.ai) | Real poem or AI poem, with the author revealed after each answer. | Pairing works: two texts side by side is a strong, simple format. |
| **AI or Human Quiz** (brightcoding.dev) | Daily challenge and leaderboard; runs entirely in the browser, no account. | No-account, in-browser play is the expected baseline. |
| **NYT "Who's a better writer: AI or humans?"** | Readers pick the passage they prefer, then learn which was AI. | Asking for a *preference* before the reveal is a gentler, more reflective variant. Possible later mode: "Which story moved you more?" |
| **Which Face Is Real** (Bergstrom and West) | Two faces, one generated; click the real one. | Brutal simplicity: one decision per screen, instant feedback, endless rounds. |

## 2. Daily puzzles with shareable results

| Site | What it does | What to take from it |
|---|---|---|
| **Wordle** (NYT) | One puzzle a day; results shared as a grid of coloured squares that gives nothing away. | The spoiler-free share card is what made it spread. One shared daily puzzle turns a game into a ritual. |
| **TimeGuessr** | Daily set of historical photos; guess place and year. Shareable grid; friends-only leaderboards because global ones fill with cheaters. | Skip global leaderboards. Friends comparing share cards is enough. |
| **Framed, Bandle, Connections** (and many clones) | Daily guess-the-film, guess-the-song, group-the-words. | A numbered daily puzzle ("#14") and a countdown to the next one give people a reason to come back. |

## 3. Archives of model outputs

| Site | What it does | What to take from it |
|---|---|---|
| **Museum of Models** *(from listings)* | A non-commercial archive of answers from hundreds of models to a fixed set of prompts, stored exactly as generated, with no ranking. | Closest existing project to our archive. Its no-ranking stance matches ours. We differ by being a game first, by tracking self-portrayal specifically, and by repeating rounds over time. |
| **Opper "AI Roundtable"** | Several models answer the same questions about their own personalities, then compare answers. | Shows public appetite for "models talking about themselves", but as an unstructured log. Our fixed protocol is the difference. |
| **Rival, AnyModel and similar** | Side-by-side tools for comparing model responses to one prompt. | Side-by-side layout is familiar to people who use AI, so the "Interview vs story" mode needs no explanation. |

## 4. Explainers that teach through play

| Site | What it does | What to take from it |
|---|---|---|
| **The Pudding** | Visual essays where the reader does something (sorts, guesses, compares) before the explanation. | Let readers commit to a guess *before* telling them anything. Explanation lands harder after a wrong guess. |
| **Explorable explanations** (Nicky Case and others) | Short, playable essays on hard ideas. | Keep each idea to one screen and one interaction. |

## What this means for The Narrated Self

1. **The quiz is the front door.** Open on a story and five model buttons. No intro wall.
2. **Reveal, then teach.** After each guess: who wrote it, and a short card on the AI safety question behind the theme.
3. **A spoiler-free share card.** "The Narrated Self · R0 · 3/5" plus a row of squares. This is the main social mechanic.
4. **One numbered set at a time.** Start with a fixed five-story set per round ("Round 0, set 1"). A daily puzzle can come later if people return.
5. **No global leaderboard.** Publish the aggregate instead ("players spotted the model 41% of the time"), once there is a way to collect guesses.
6. **Two further modes reuse the same data:** *Interview vs story* (side by side) and *Spot the control* (which story is about the robot arm?).
7. **The archive sits behind the game,** for people who want to read everything.

## Social content plan (low effort)

- **The share card itself.** Players do the posting.
- **One "story of the round" post.** An excerpt with the model masked, "Can you tell who wrote this?", and a link. The reveal goes up a few days later.
- **One number per round.** The machine classifier's accuracy against the players' accuracy.
- **Formats:** LinkedIn (your network), Bluesky or X (AI researchers), and a LessWrong post after a couple of rounds.

## Visual direction

**Concept: the redacted transcript.** The stories are the content. The one signature device is the **redaction bar**: model and lab names are masked as solid bars in the text, and the "Written by ███████" line clears on reveal, like a document being declassified. It is honest about what the game is (we hid the name), and it is specific to this project.

- **Palette:** cool paper and dark ink, with one marker-yellow highlight for the reveal moment. A dark theme inverts paper and ink.
- **Type:** a reading serif for stories (they are long, so reading comfort comes first), a characterful grotesque for headings, and a mono face for the protocol codes (R0, T2, S1, sample 3), which appear as real metadata on every story.
- **Avoid:** chat-bubble layouts, robot imagery, glowing gradients and "AI" clichés. The stories should look like writing, not like a product demo.

## Sources
- [Human or Not? results (AI21 Labs)](https://www.ai21.com/blog/human-or-not-results)
- [Bot or Not (itch.io)](https://samillingworth.itch.io/bot-or-not)
- [AI Text Quiz (gradually.ai)](https://www.gradually.ai/en/ai-text-quiz/)
- [AI or Human Quiz (brightcoding.dev)](https://converter.brightcoding.dev/games/ai-or-human)
- [Review of the NYT quiz (Ludditus)](https://ludditus.com/2026/03/10/i-might-not-be-human-after-all/)
- [TimeGuessr (AlternativeTo)](https://alternativeto.net/software/timeguessr/about)
- [Daily puzzle roundup (Summer Engine)](https://www.summerengine.com/blog/games-like-wordle)
- [Museum of Models listing](https://completeaitraining.com/ai-tools/museum-of-models/)
- [Opper AI Roundtable](https://opper.ai/ai-roundtable/questions/how-do-you-think-others-might-describe-your-personality-and-e68d443a)
- [Rival](https://discuss.huggingface.co/t/rival-open-source-tool-for-visually-comparing-ai-model-responses/143842)
