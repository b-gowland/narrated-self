# Design brief

## Audience
- **Primary: curious general readers** who use AI chat tools but don't follow AI research. They arrive from a shared link (a group chat or social media), on a phone, with a few minutes to spare. No onboarding tolerance.
- **Secondary: people who work near AI** (tech, policy, education) who will share it as a conversation starter and may dig into the method and data.
- **Tertiary: AI safety researchers and journalists**, who want the archive, the protocol and the numbers.

The game must work for the first group without any explanation; depth is there for the other two, one tap away.

## Market position
- Existing "AI or human?" quizzes ask whether *a machine* wrote something. Ours asks *which* machine, about *itself*. That is new.
- Archives of model outputs exist (Museum of Models), but none are playable and none track self-portrayal over time.
- So the hook is the game, the depth is the archive, and the reason to come back is the next round.

## UX principles
1. **Restraint (after NYT Games).** One decision per screen. If something needs explaining, simplify it.
2. **Story first.** On a phone the first story begins within the first screen.
3. **The guess lives in the thumb zone.** A sticky bottom tray of five big buttons, usable at any point while reading.
4. **Reveal, then teach.** The stamp names the author, then one short paragraph naming the safety risk the theme covers, then an optional link deeper.
5. **Shareable without spoilers.** A Wordle-style result line; the native share sheet where available, copy otherwise.
6. **Every number is real metadata.** Word count, reading time, round, theme and format codes come from the data.
7. **Accessible.** 4.5:1 contrast for body and small text, 44px tap targets, visible focus, reduced-motion support, a skip link.

## Visual language
1970s pulp sci-fi paperbacks (see `CATALOGUE.md`): flat print colours per theme, halftone, condensed all-caps titles in the manner of Futura Extra Bold Condensed covers, heavy black frames, rubber stamps, paper grain and the odd handwritten mark. Story text in a sturdy, newspaper-era sans (Franklin Gothic lineage) for long reading.

## Iteration log
- **v1 (redacted transcript):** muted paper, serif, mono labels. Read as generic AI product design. Dropped.
- **v2 (pulp paperback):** right direction. Problems at phone width: four blocks of chrome before the story; guess buttons below 500 words of text; slashed zeros in the body face read as code; the red off-register headline looked like WordArt; the demo banner was louder than the game.
- **v3:** compact masthead; story starts on the first screen; sticky guess tray; Libre Franklin body; registration effect only on cover titles, in ink; slim demo strip; word count and reading time on each cover; per-story breakdown on the score card; native share with copy fallback; a link from each reveal to that model's interview answer.
- **v3 review rounds (screenshots at 375px and 1280px):**
  - *Round 2, reveal:* stamp, answer loop and "real question" read clearly; wrong-guess path checked.
  - *Round 3, score card and desktop:* tally rows and share line work; the desktop column is calm, not sparse.
  - *Round 4, 375px:* nav clipped "About"; names touched button edges; demo strip wrapped. Fixed with a wrapping nav, tighter tray type and a shorter strip.
  - *Round 5, score copy:* the result line now changes with the score instead of a flat "1 in 5".
- **Not yet verified:** dark mode in a real browser (the local preview renders light only), and the native share sheet on a phone.
