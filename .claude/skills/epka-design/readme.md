# EPKA — Design System

The brand system for **EPKA**, the independent consulting practice of **Paul Renders** — a freelance management consultant in **data-driven marketing, subscription strategy and customer insights**, based in Belgium.

> _"I turn complex data into clear, actionable strategies that drive real growth."_

EPKA works with media, retail/fashion, B2B/industrial and agency clients across Belgium and beyond (Roularta, DPG Media, Streamz, Mayerline, Atlas Copco, TBWA, Universal Music and others). The voice is senior, plain-spoken and outcome-led: less jargon, more "what moves the number."

This folder is a **design-system skill**. It packages EPKA's logo, colour, type and spacing tokens so any agent can produce on-brand artifacts (the Kompas page, decks, one-pagers, mockups) quickly.

---

## Sources this system was built from

Reverse-engineered in Claude Design from Paul's portfolio deck (wordmark, coral network mark, palette, Raleway/Lato type, section copy) and his stationery. The full project, with components, slides, decks and the website UI kit, lives in Claude Design as **EPKA Design System**; this folder is the subset needed to style Kompas and other artifacts.

---

## CONTENT FUNDAMENTALS — how EPKA writes

The brand voice is that of a seasoned consultant talking straight to a marketing director. Confident, concrete, never salesy.

- **Person & address.** First person singular — "**I** turn data into decisions", "**I** look past the surface ask". The client is "**you / your team**". EPKA is a person (Paul), not a faceless agency.
- **Tone.** Direct, pragmatic, results-first. Favours the concrete metric over the abstract promise: _"From churn reduction to subscription growth — I measure what counts."_ A touch of dry wit is welcome ("a way of working, not a deck of slides"; "have a number that needs moving?").
- **Casing.** Sentence case for headlines and body. Eyebrows/kickers are **UPPERCASE** with wide tracking ("WHAT I DO", "HOW I WORK", "SELECTED CLIENTS"). Title Case only for proper service names ("Subscription Strategy", "Dashboarding & KPI Design").
- **Sentence shape.** Short. Often a noun-phrase fragment for impact ("Build frameworks, not reports."). Em-dashes and the "X, not Y" contrast structure recur.
- **Specificity.** Real tools and methods are named, not hidden: Power BI, Looker Studio, Piwik PRO, Snowflake/SQL, RFM segmentation, A/B testing, GDPR migration (GA → Piwik PRO). This specificity _is_ the credibility.
- **Language.** Primary delivery language is **English**; Paul also works in NL (native), FR and DE. Source copy was bilingual EN/NL — keep customer-facing artifacts in English unless asked.
- **Numbers.** Used as proof, sparingly: "20+ years", "freelance since 2019", "4 languages". Never invent client results or fake metrics — only state numbers you can stand behind.
- **Emoji.** **None.** The brand is corporate-professional. No emoji in headings, body, or UI.
- **Vocabulary cues.** churn, retention, RFM, segmentation, KPI model, dashboard, subscription, customer insight, loyalty, ROI, monetisation, framework, delivery.

**Headline patterns that fit the brand**
- "Turn complex data into clear decisions."
- "Six ways I move the number."
- "A way of working, not a deck of slides."
- "Have a number that needs moving?"

---

## VISUAL FOUNDATIONS

The system reads **clean, corporate-modern, data-led** — confident petrol-navy with a single hot coral accent, generous whitespace, and crisp geometric type. Think strategy consultancy, not startup.

### Colour
- **Petrol ink `#0B2B36`** is the primary brand colour — the exact navy of the wordmark. Used for dark sections, headings, and text. It is deep, slightly teal, and serious.
- **Coral `#FC4C50`** (the network-mark colour) is the _single_ accent — CTAs, eyebrows, numbers, the underline rule, active states. Used sparingly for maximum punch; never as large fills beyond buttons/marks.
- **Supporting accents** appear only in data/diagram contexts: **teal `#1B8A7A`** (positive / retention / success) and **soft gold `#F0E199`** (warm callouts). Don't introduce other hues.
- **Neutrals** are a cool grey ramp (`#F7F8F9` paper → `#E5E7EB` borders → `#374151` body → ink). No warm greys.
- Avoid: purple/blue gradients, rainbow data palettes, neon, warm beige. The deck's original Highcharts-default chart colours are **not** brand colours — use the EPKA palette for any new charts.

### Type
- **Raleway** (display, 400–800) — all headings, eyebrows, numbers, buttons, labels. Geometric, matches the lowercase wordmark. Headings are heavy (700/800) and tightly tracked (`-0.02em`); display sizes are large and confident.
- **Lato** (body, 400/700/italic) — paragraphs, tables, running UI text. Humanist, calm, readable.
- Eyebrows: Raleway 600, UPPERCASE, `0.16em` tracking, usually coral.

### Layout & space
- 4px spacing base; generous section padding (80–120px vertical on web, 72–88px on slides).
- Centered max-width containers (~1180px web). Lots of breathing room — the brand is not dense.
- A recurring **split layout**: petrol panel (title) beside a white panel (content) — used on slides and the Approach section.

### Shape, border, elevation
- **Corner radii are restrained:** 10px default (cards, inputs, buttons), 14px feature cards, pill only for tags/badges/avatars/small toggles. Never heavily rounded large surfaces.
- **Borders are 1px hairlines** in cool grey (`#E5E7EB`). Cards = white surface + hairline + soft shadow.
- **Shadows are cool and petrol-tinted** (`rgba(11,43,54,…)`), low-spread, soft — never harsh black. Coral CTAs get a coral-tinted lift (`--shadow-coral`) on hover.
- Signature motif: a short **coral underline rule** (56–64px × 4–5px, pill-capped) under section titles.

### Imagery
- **Photography** is cool and wide: snow-capped mountains (clarity, distance, calm) and candid professional portraits (human, approachable). One warm architectural shot (atrium) provides contrast. Images are often used at low opacity behind petrol with a left-to-right fade-to-transparent mask.
- **Client logos** are shown **grayscale at ~60% opacity** on white cells for a unified, understated wall.
- The **coral network mark** (four connected nodes) is used as a faint, large watermark motif on closing/dark surfaces (~6–10% opacity).
- No illustration, no 3D, no stock-y "business handshake" clichés.

### Motion & states
- Quiet and confident. Short durations (120–360ms), standard easing (`cubic-bezier(0.2,0,0,1)`) — **no bounce, no spring**.
- **Hover:** buttons darken (coral → `#E63A3E`) and gain a coral shadow; cards lift 3px with a larger shadow; ghost/secondary fill with mist grey.
- **Press:** 1px downward nudge (`translateY(1px)`).
- **Focus:** 3px soft coral ring (`--ring-focus`).
- Respect `prefers-reduced-motion` (handled in `tokens/base.css`).

---

## ICONOGRAPHY

The source material is **icon-light** — the deck leaned on type, numbered markers and colour blocks rather than an icon set, and the brand mark itself (the connected-node graph) carries the "data/network" idea.

- **No proprietary icon font or SVG sprite** was shipped with the brand, so none is bundled.
- **Approach in this system:** prefer **numbered markers** (`01`–`06` in coral) and the **network mark** over decorative icons — it's the most faithful, most distinctive choice. Use icons only where genuinely functional (mail, phone, arrow, chevron, search, menu).
- **Where icons are needed,** the components and kits use a small set of **inline, single-stroke line icons** drawn in the [Lucide](https://lucide.dev) style — 2px stroke, round caps/joins, `currentColor`. This is a **substitution** (no brand icon set exists); if you want a specific library, Lucide or Heroicons (outline) both match the clean, geometric, single-weight feel. **Flag:** swap in your preferred set and keep stroke weight consistent.
- **Emoji:** never. **Unicode symbols:** only the star (★) for the language-proficiency meter, as in the source deck.
- Keep icons small and secondary — they support text, they don't lead.

Key brand assets live in `assets/`:
- `logos/`: `epka-logo` (full lockup), `epka-wordmark`, `epka-mark` (the nodes), plus `-white` reversed variants for dark surfaces.
- `fonts/`: Raleway (variable) + Lato (400/700/italic) woff2.

---

## INDEX — what's in this folder

- `SKILL.md`: the skill entry point.
- `styles.css`: the single global entry point (`@import`s only).
- `tokens/`: `fonts.css`, `colors.css`, `typography.css`, `spacing.css`, `base.css`.
- `assets/logos/`, `assets/fonts/`: see above.
- `thumbnail.html`: the system's cover card.

Kept in the Claude Design project only (not in this public repo): the React components (Button, IconButton, Input, Select, Checkbox, Radio, Switch, Card, StatCard, Badge, Tag, Avatar, Tabs, Callout) and their compiled `_ds_bundle.js`, the guideline cards, the portfolio sample slides (`slides/`), the Roularta and portfolio decks (`decks/`), the EPKA Deck and QGIS map templates (`templates/`), the website UI kit, client logos, the portrait and the email signature.

---

## Using this system

1. Link `styles.css` for tokens, fonts and base styling, or copy the token values into a self-contained page.
2. For static artifacts (slides, one-pagers), copy assets out of `assets/` and follow the foundations above.
3. Lead with petrol + one coral accent. Raleway headlines, Lato body. Restrained radii, hairline borders, cool soft shadows. Keep copy direct and outcome-led. No emoji.

---

## Kompas — how the brand is applied to `web/index.html`

Kompas is published as a single self-contained Artifact page, so it cannot link `styles.css`. The page copies the token values into its own `:root` block instead, and loads Raleway + Lato from Google Fonts.

- **Header:** a petrol (`#0B2B36`) panel, 14px radius. One line: the date left as the page heading (Raleway 800, 32px), the Kompas lockup right, with "kompas" on the date's baseline. Then the coral underline rule and the "team keek laatst" line. On phones there is no room for both, so the lockup sits above the date.
- **Kompas lockup:** no separate Kompas logo (Paul, 26/10). "kompas" in Raleway 800 lowercase (28px) with the coral EPKA mark beside it, and under it "finance intelligence by" plus the white epka wordmark (without the mark). Designed for its size, not copied from the epka logo: the mark is 1.15 x-heights tall and 0.7 x-heights from the word, bottom on the baseline (the logo's own 0.89 / 1.25 make it a speck this small). The second line is 11/30 of the word size with -0.02em tracking, so both lines share one left and one right edge. Every size derives from one `--brand` variable; keep the two lines flush if you change it. Both images are cropped from `assets/logos/` and inlined as small base64 PNGs.
- **Uppercase is rare:** only the eyebrow, section labels and status pills/badges (OPLETTEN, HOOG, NIEUWE POSITIE) are Raleway 700 uppercase with wide tracking. Section labels are coral (`#C32C30` as text); their right-hand note is muted Lato. Every other small label ("Vervalt als", "omvang", "raakt:") is sentence-case Lato in a muted grey.
- **Values lead, labels recede:** next to a status dot, or under a small label, the label is Lato regular and muted, and the value is Raleway 700 in petrol ink (chips, fact values, the current share in the portfolio sleeves).
- **Figures:** Raleway defaults to old-style figures, which bounce. The page sets `lining-nums` everywhere and `tabular-nums` wherever values line up (chips, dates, percentages, the weather axis, footer).
- **Body:** Lato. Headings and subjects use petrol ink, running text uses graphite `#374151`.
- **Cards:** white, 1px `#E5E7EB` hairline, 10px radius, 18/20px padding, soft petrol shadow. The call and a sell proposal get a straight 4px coral or deep-coral bar along the top (clipped by the card, not a bent border). No coloured side edges.
- **Text fills the card:** running text (`.lede`, `.prose`, `.item-text`) has no `ch` cap; the page's 860px column already bounds the line length (Paul, 26/10: use the full width).
- **Lists** in playbooks have no bullets, so nothing round competes with the status dots.
- **Status scale** (Paul, 26/10: the steps must differ in lightness, not just hue): ok teal `#1B8A7A` (L\* 52) · watch gold `#E3BE45` (L\* 78) · alert deep coral `#8E1F2C` (L\* 32). Dark mode: teal · `#F0D267` · `#FF6B6E`. Keep this ordering when changing any of them.
- **No new hues.** The old blue accent is replaced by lifted petrol (`#16404C`); purple is gone.
- **Dark mode** is petrol-based (`#071E26` page, `#0B2B36` surfaces), not neutral grey.
