# Security and content review

Date: 2026-10-25. Scope: the public site (`narratedself.airiskpractice.org`), the guess API (`narratedself-api.airiskpractice.org`), the GitHub repo and its workflows, credentials, dependencies, and the accuracy of every citation on the site.

Approach: hostile requests against the live API (all rejected, so nothing was written), a code review of the site and Worker, a review of the repo's settings and permissions, dependency audits, and a check of each citation against its primary source. Re-run the live tests after any change to `worker/`.

## Summary
No secrets were exposed and no injection or access-control flaw was found. Ten hardening changes were made and verified live. Four recommended settings are left for the maintainer, listed at the end.

## Citations (About page)
Every arXiv citation was checked against arXiv's own metadata (title, date, authors). The other links were opened and their page titles confirmed.

| Citation | Result |
|---|---|
| Butlin, Long and others (2023), arXiv 2308.08708 | Correct. Wording changed to match the paper's own hedge: its analysis "suggests" no current system is conscious. |
| Long, Sebo and others (2024), arXiv 2411.00986 | Correct |
| Perez and Long (2023), arXiv 2311.08576 | Correct |
| Shanahan, McDonell and Reynolds (2023), arXiv 2305.16367 (Nature) | Correct |
| Needham and others (2025), arXiv 2505.23836 | Correct |
| Greenblatt and others (2024), arXiv 2412.14093 | Correct |
| Palisade Research (2025), arXiv 2509.14260 | **Fixed:** now names the authors (Schlatter, Weinstein-Raun and Ladish) and the paper's real title |
| Anil Seth, Behavioral and Brain Sciences | **Fixed:** canonical cambridge.org link; "published online 2025" (the journal issue is dated 2026) |
| Mustafa Suleyman (2025) | **Fixed:** the essay's real title is "We must build AI for people; not to be a person"; "Seemingly Conscious AI" is the term it introduces. Link added. |
| 80,000 Hours, Eleos AI Research, Anthropic "Exploring model welfare" (24 April 2025) | Correct |

## API tests (live)
| Test | Result |
|---|---|
| Wrong methods and unknown paths | 404, no detail |
| Malformed JSON | 400 |
| SQL injection in `device_id` and `story_id` | Rejected by validation. All database queries use bound parameters in any case. |
| Path traversal in the round parameter (`../index`) | Rejected. **Hardened:** the round is now validated before any URL is built from it. |
| 200 KB request body | Rejected. **Hardened:** a declared body over 4 KB is refused before it is read. |
| `/export` with no token, a wrong token, or a token in the query string | 401 in every case. **Hardened:** constant-time token comparison. |
| Cross-origin request from another site | No CORS permission given |
| Plain HTTP | Redirects to HTTPS |
| Response headers | **Added:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` |
| `*.workers.dev` and preview URLs | **Disabled explicitly**, so zone protections such as a rate-limit rule can't be bypassed |
| Database after testing | 0 rows; nothing written |

## Site review
- **Model text is always inserted as text, never as HTML.** A story containing markup or script can't run. This is the most important check for a site that displays model output.
- **Content Security Policy added.** The page script moved to `site/app.js`, so the policy can forbid inline scripts entirely (`script-src 'self'`). Connections are allowed only to the site itself and the guess API. Fonts come only from Google Fonts. Plugins are blocked, and forms can't post anywhere.
- The one place a data value was put into HTML (a theme ID) now uses a data attribute instead.
- No keys, tokens or secrets in any site file.
- GitHub Pages can't send custom headers, so clickjacking protection (`frame-ancestors`) isn't possible. The site has no account or sensitive action to hijack, so this is accepted.

## Repo and workflows
- Secret scanning and push protection: on. Open alerts: 0. Secret patterns in the full git history: none.
- The default GitHub Actions token is read-only. Only the nightly export can write, limited to `contents`.
- **Hardened:** every action in every workflow is pinned to an exact commit ID, so a moved tag can't change what runs.
- The maintainer is the only collaborator; there are no deploy keys.
- **Dependabot alerts: off** (see recommendations).

## Dependencies
- **Python** (locked requirements, `pip-audit`): no known vulnerabilities.
- **Worker tooling** (`npm audit`): three advisories (one high, two moderate) in `undici`, pulled in by Cloudflare's `wrangler` and `miniflare`. These are local development and deploy tools only; none of this code is deployed in the Worker. npm's suggested fix downgrades wrangler, so the risk is accepted until wrangler ships an update. Recheck at each deploy.

## Personal information
The project is linked to its maintainer through the GitHub username and AI Risk Practice; that is accepted. The aim is to keep personal details out of the code and data: commit emails use the GitHub noreply address, no personal email or local path appears in tracked files, and the guess data holds no personal information.

## Recommended settings for the maintainer
1. **Cloudflare rate-limit rule** on `narratedself-api.airiskpractice.org/guess` (in progress).
2. **Verify `airiskpractice.org` on GitHub** to prevent subdomain takeover (in progress).
3. **Turn on Dependabot alerts:** repo **Settings → Code security → Dependabot alerts → Enable**.
4. **Optional, HSTS on the zone:** Cloudflare **SSL/TLS → Edge Certificates → HTTP Strict Transport Security**. Leave "include subdomains" off unless every subdomain of `airiskpractice.org` serves HTTPS.

Also from `docs/OPERATIONS.md`: lower the OpenRouter key limit to the balance, and log Wrangler out between deploys.
