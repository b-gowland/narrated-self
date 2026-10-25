# Going live

The site will live at **narratedself.airiskpractice.org**, next to the other AI Risk Practice tools (`baseline.`, `library.` and `app.airiskpractice.org`). It uses the same setup: GitHub Pages, deployed by a GitHub Action, with DNS on Cloudflare.

Search engines can list the site from 2026-10-25, when `noindex` was removed.

## 1. Turn on hosting (done 2026-10-24)

Live at https://narratedself.airiskpractice.org with HTTPS enforced. The steps are kept here for reference. One lesson: add the DNS record **before** entering the custom domain in GitHub. Otherwise GitHub caches a "not found" answer for up to 30 minutes and the HTTPS certificate is delayed.

**GitHub** (repo `b-gowland/narrated-self`)
1. **Settings → Pages → Build and deployment → Source:** choose **GitHub Actions**.
2. **Settings → Pages → Custom domain:** enter `narratedself.airiskpractice.org` and save. The `site/CNAME` file sets this too.

**Cloudflare** (zone `airiskpractice.org`)
3. **DNS → Records → Add record:**
   - Type: `CNAME`
   - Name: `narratedself`
   - Target: `b-gowland.github.io`
   - Proxy status: **DNS only** (grey cloud), the same as your other subdomains.

**Then**
4. Ask Claude Code to push, or push yourself. The **Deploy site to GitHub Pages** action publishes `site/`.
5. Back in **Settings → Pages**, tick **Enforce HTTPS** once GitHub has issued the certificate. That usually takes minutes, but can take up to an hour.
6. If `airiskpractice.org` isn't already a **verified domain** on your GitHub account (**Settings → Pages → Verified domains**), verify it. This stops anyone else claiming your subdomains. It's probably already done for the other three sites.

## 2. Analytics (about 5 minutes)
**Research data** (guesses) goes through the project's own Cloudflare Worker; see `docs/PLAYER_DATA.md`. **Traffic** (visits, where people come from, shares) can use Plausible, as your other sites do. It is privacy-friendly and needs no cookie banner.
1. In Plausible, add the site `narratedself.airiskpractice.org`.
2. Copy the script line it gives you and send it to Claude Code. It will add the line, plus events for **Set started**, **Set finished** and **Share**.

## 3. Launch checklist
- [x] Round 0 run, and the site rebuilt with real, masked stories.
- [x] Guess logging deployed (`docs/PLAYER_DATA.md`) and tested with a live guess (2026-10-25).
- [x] Removed `noindex` (2026-10-25).
- [x] Share image (`site/og.png`, 1200×630, drawn by `scripts/make_og_image.py`) and `og:image` tags.
- [x] Run QA: `uv run python scripts/qa.py` (2026-10-25: no failures; warnings are known and reviewed).
- [ ] Search engines:
  - **Google Search Console:** if `airiskpractice.org` is already a domain property, the subdomain is covered. Submit `https://narratedself.airiskpractice.org/sitemap.xml`.
  - **Bing Webmaster Tools:** submit the same sitemap. Bing also feeds several AI search tools.

## 4. Search and discoverability (SEO, AEO, GEO)

**SEO (search engines)**
- The title and description use the words people search with ("Which AI wrote this?", the model names, "free, no login"). Done.
- Canonical URL, `robots.txt` and `sitemap.xml`. Done.
- **The biggest lever comes later: one page per story.** Each round adds up to 180 unique texts. Giving each story its own address (`/r0/t2-s1-claude-1`, for example) turns the archive into long-tail search content. That's a `tns site` feature for after round 0.

**AEO (answer engines: featured snippets, voice assistants)**
- A visible FAQ on the About page, with matching `FAQPage` structured data. Each answer is 30–60 words and stands on its own. Done.
- Questions chosen to match real searches: "Do AI models have feelings?", "Can people tell which AI wrote this?", "How do AI models talk about being switched off?"

**GEO (AI search: ChatGPT search, Perplexity, Google AI Overviews)**
- `site/llms.txt`: a plain summary of what the site is, what it measures, what it doesn't claim, and where the data is. Done.
- **Citable facts.** AI search quotes pages that state dated numbers plainly. Publish each round's headline numbers as sentences, for example "In round 0, players identified the author 41% of the time; a word-statistics classifier managed 87%."
- **A citable dataset.** Archive each round on Zenodo (free DOI) or Hugging Face Datasets, and add `Dataset` structured data. Researchers and AI tools cite DOIs.
- **One consistent name:** "The Narrated Self, a project by AI Risk Practice", the same on the site, GitHub and the dataset.
