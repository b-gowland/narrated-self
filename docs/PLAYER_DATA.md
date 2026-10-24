# Player data: how guesses are collected

This implements the player-data protocol in `docs/PREREGISTRATION.md` §9.

## How it works
- **The site** (`site/index.html`) sends each guess to a small Cloudflare Worker, but only on the live site. Previews and local copies record nothing.
- **The Worker** (`worker/`) checks the story ID against the published round data (`site/data/<round>.json`) and works out the true model and whether the guess was right itself. The browser can't claim a guess was correct. It stores one row per guess in a Cloudflare D1 database.
- **A nightly GitHub Action** (`.github/workflows/players-export.yml`) copies the aggregates into `data/players/<round>/aggregates.json`.

## What is stored
| Stored | Not stored |
|---|---|
| A random device ID kept in the player's browser | IP address |
| A random set ID; whether this is the device's first set | User agent or any browser details (only a yes/no "known bot" flag) |
| Round, story ID, true model, theme and condition | Cookies, accounts, names, emails |
| The guess, whether it was right, position in the set, time to guess | Location |
| Server time (UTC) | Cloudflare request logs (turned off) |
| Optional answer: which AI assistant the player uses most | |

## What is published, and when
- **Nightly:**
  - total guesses;
  - qualifying guesses, which means first sets only, not bots, and 5 seconds or more;
  - exclusion counts;
  - pooled accuracy;
  - "AI vs robot arm" totals from earlier picks, if any (the view no longer has a guess);
  - answers to the optional question.
- **Per-model accuracy** for a model is published once it has 200 qualifying guesses. **The confusion matrix** is published once every model has.
- **Row-level data** is published once a round's analysis is complete.
- **The site** shows pooled accuracy only.

## Implementation choices not spelled out in §9
- **Flood limit:** at most 1,000 guesses per device per day are accepted. This guards against abuse, so it is separate from the analysis exclusions.
- **Known bots:** user agents matching common crawler and script patterns are flagged as bots. An empty user agent counts as a bot.
- **"AI vs robot arm"** (formerly "Spot the robot") no longer has a guess, so nothing is recorded from it. The Worker still accepts the "control" mode in case a guess returns.
- **The optional question** has fixed options: Claude, ChatGPT, Gemini, Grok, Copilot, Meta AI, DeepSeek, another one, or none. "Skip" records nothing.

## Known limitations
- **Clearing browser data gives a new device ID.** A returning player then counts as a first set again. Answers can also spread between players.
- **The answer key is visible to anyone who reads the site's data file,** so a determined cheat can score perfectly. The 5-second exclusion and first-play rule limit this, but don't stop it.
- **Bot detection is basic.** Cloudflare's advanced bot scoring isn't available on the free plan.

## One-time setup (about 10 minutes)
Run these from the repo folder in a terminal.
1. Install and log in to Cloudflare:
   ```
   cd worker
   npm.cmd install
   npx.cmd wrangler login
   ```
   A browser window opens; approve access to your Cloudflare account.
2. Create the database:
   ```
   npx.cmd wrangler d1 create narratedself
   ```
   Copy the `database_id` it prints into `worker/wrangler.toml`, replacing `REPLACE_WITH_ID_FROM_wrangler_d1_create`.
3. Create the tables, then deploy:
   ```
   npm.cmd run db:remote
   npx.cmd wrangler deploy
   ```
   This also creates `narratedself-api.airiskpractice.org` on your Cloudflare zone.
4. Set the shared export token. It's generated and stored without being shown:
   ```
   cd ..
   powershell -ExecutionPolicy Bypass -File C:/dev/narrated-self/scripts/set-export-token.ps1
   ```
5. Check it works by opening `https://narratedself-api.airiskpractice.org/stats?round=R0`. It should return JSON with `"all_guesses": 0`.

Steps 2, 3 and 5 can be run by Claude Code once you have done step 1. Step 4 is best run by you, so the token never passes through a chat.
