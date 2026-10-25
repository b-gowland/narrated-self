# Operations: security and costs

A running register of every account, credential and running cost the project depends on. Review it when something is added, and at least once a round.

Last reviewed: 2026-10-25. The full security and citation review is in `docs/SECURITY_REVIEW.md`.

## Credentials

| Credential | Where it lives | What it can do | If it leaked | Status / action |
|---|---|---|---|---|
| **OpenRouter API key** | `.env` on the maintainer's PC (ignored by git) | Call any model, paid from prepaid credit | Someone spends the remaining credit. No auto top-up, so nothing beyond the balance. | Live. Key limit US$25 (lowered 2026-10-26), about a round and a half of spend. 2FA on. |
| Anthropic, OpenAI, Google keys | (none) | (none) | (none) | **Revoked 2026-10-25**, confirmed rejected by each provider; blanked in `.env`. The accounts and their credit remain. |
| **Cloudflare (Wrangler) login** | Wrangler's config folder in the maintainer's Windows user profile | Broad access to the Cloudflare account: Workers, D1, routes, certificates, email routing and more | Someone with access to the PC could change the Worker, DNS-adjacent settings or other Cloudflare services | Needed only to deploy, which is rare. **Log out between deploys:** `npx.cmd wrangler logout`. Logging back in takes 30 seconds. |
| **EXPORT_TOKEN** | Cloudflare Worker secret and GitHub Actions secret | Read aggregates and anonymous row-level guesses from the API | Early access to anonymous guess data; no personal data is exposed | Live. To rotate: `powershell -ExecutionPolicy Bypass -File C:/dev/narrated-self/scripts/set-export-token.ps1` |
| GitHub CLI login | Maintainer's PC (Windows credential store) | Push, edit repo settings and secrets | Repo changes; secret values can't be read back | Existing, standard. |

## Public surfaces and abuse

| Surface | Risk | Mitigation in place | Recommended |
|---|---|---|---|
| **Guess API** (`narratedself-api.airiskpractice.org`) | Fake guesses with rotating device IDs, which pollute the data and use up the free quota | Story IDs checked server-side; correctness computed server-side; 1,000 guesses per device per day; analysis excludes bots, guesses under 5 seconds and repeat sets | **Cloudflare rate-limiting rule** on `/guess` (the free plan includes one), for example 30 requests per 10 seconds per visitor. Watch the nightly counts for sudden jumps. Add Cloudflare Turnstile only if abuse appears. |
| **`/stats` endpoint** | Each call reads every quiz row, so heavy traffic multiplies database reads | Cached for 5 minutes at Cloudflare's edge (done 2026-10-25) | (none) |
| Answer key in `site/data/R0.json` | Players can look up answers | 5-second and first-play exclusions | Accepted and documented (`docs/PLAYER_DATA.md`). |
| Subdomains of `airiskpractice.org` | Subdomain takeover if a DNS record points at GitHub with no site behind it | `airiskpractice.org` verified on GitHub (2026-10-26), which protects all four subdomains | (none) |

## Privacy
- **No personal data is collected:** no IP address, user agent, cookie or account. A random ID is kept in the browser's local storage. Visits are counted with Plausible (no cookies, no personal data), which is switched off along with guess recording.
- **Australia:** an anonymous random ID isn't personal information under the Privacy Act.
- **EU and UK visitors:** ePrivacy rules can require consent before storing an identifier on a device for a non-essential purpose, and research logging probably counts as non-essential. The plain notice is in place. A one-click "Don't record my guesses" option is live (2026-10-25). This is a practical reading, not legal advice.
- **Personal details in the repo:** the commit history uses the noreply address. Old commits may stay reachable on GitHub by direct ID until GitHub clears them; GitHub Support can purge them on request. A local backup of the old history (with the old email) sits in Claude Code's temporary folder; delete it once you're satisfied.

## Running costs

| Item | Cost | Notes |
|---|---|---|
| Model calls (OpenRouter) | About US$4 per pilot round (180 outputs), about US$10 per full round (420 outputs) | Spent so far US$5.22, including two smoke tests. Quarterly full rounds cost about US$40 a year. OpenRouter adds about 5% when buying credit. Gemini's introductory price is reported to double from 1 December 2026. |
| Cloudflare Worker and D1 | Free plan | Free limits: 100,000 Worker requests a day; D1 5 million rows read and 100,000 written a day, 5 GB stored. At about 7 requests per player, that's roughly 10,000 players a day. On the free plan, going over makes requests fail rather than charging. Check whether the account is on Workers Paid (US$5/month), where overages are billed. |
| GitHub Pages and Actions | Free (public repo) | GitHub disables scheduled workflows in a repo with no activity for 60 days. If the nightly export stops, re-enable it under Actions. |
| Cloudflare DNS | Free | (none) |
| Plausible | Your existing plan | This site's pageviews count towards the plan's monthly quota. |
| Domain | Existing renewal | (none) |

## Routine checks
- **Each round:** re-read this register; run `uv run python scripts/qa.py`; check the OpenRouter balance.
- **Monthly while the game is live:** look at `data/players/R0/aggregates.json` for odd jumps; confirm the nightly export is still running.
