---
name: epka-design
description: Use this skill to style anything for EPKA (Paul Renders' consultancy) on-brand, including the Kompas page in web/index.html, decks, one-pagers and HTML mocks. Contains the EPKA colour, type, spacing and shadow tokens, the Raleway/Lato webfonts, and the logo files. Use it whenever a Kompas UI change touches colours, fonts, layout or visual states.
user-invocable: true
---

Read `readme.md` in this folder first: it holds the brand voice, visual foundations and the rules for how Kompas applies them.

If creating visual artifacts (slides, mocks, one-pagers), copy assets out of `assets/` and create static HTML files for the user to view. If working on production code such as `web/index.html`, follow the tokens in `tokens/` and the rules in `readme.md`.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask a few focused questions, then act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Quick brand reference

- **Brand:** EPKA, the consultancy of Paul Renders (data-driven marketing, subscription strategy, customer insights). Belgium.
- **Logo:** lowercase petrol wordmark + coral four-node network mark. Files in `assets/logos/`, with `-white` variants for dark surfaces. The mark always sits *beside* the wordmark, never below it.
- **Colours:** petrol ink `#0B2B36` (primary dark) · coral `#FC4C50` (the single accent) · teal `#1B8A7A` and gold `#F0E199` (data accents only) · cool grey neutrals. Tokens in `tokens/colors.css`.
- **Type:** Raleway (headings, eyebrows, labels, numbers; 700–800, tight tracking) + Lato (body). Fonts in `assets/fonts/`; on a published Artifact page, load both from Google Fonts instead.
- **Shape:** restrained radii (10px default, 14px feature cards, pill for tags), 1px cool hairline borders, soft petrol-tinted shadows, a coral underline rule under titles.
- **Voice:** direct, outcome-led, specific. Sentence-case headlines, UPPERCASE eyebrows. **No emoji.**

## What's here

- `readme.md`: the design guide, plus the Kompas-specific rules.
- `styles.css` + `tokens/`: the full token system (link `styles.css` to inherit everything).
- `assets/logos/`, `assets/fonts/`: logo PNGs and woff2 webfonts.
- `thumbnail.html`: the system's cover card (petrol, white wordmark, colour strip).

The React components, sample slides, decks, website UI kit and email signature live in the EPKA Design System project in Claude Design. They are not copied here because this repository is public.
