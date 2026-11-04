"""The daily briefing -- every run opens a new edition of the page.

Paul, 4/11/2026: "waarom ziet dat kompas er niet uit alsof er een nieuwe dag
gestart is? je kan toch geen platform beheren waarop nauwelijks iets
wijzigt? dit moet leven he!!!"

The team found three causes. The morning call stayed on one idea for over a
week, and each day was only a "nog altijd". The monitors mostly said
"ongewijzigd". And nothing on the page said what happened since yesterday.
So every Pijler A run (and the midday run) writes one edition:
`briefing/{date}-{edition}`. An edition has:
- a headline: the one thing to know about today, in one sentence;
- 2 to 5 items. "gebeurd" is what happened and needs a source. "betekent" is
  what it means for Paul, the team's judgment, and names the team doc it
  rests on. "vandaag" is what to watch today, with a time if there is one;
- an optional market pulse: a handful of sourced figures (index futures,
  yield, oil, euro) with value, change, source and as_of. These are market
  levels, never Paul's own positions (he keeps those in his Sheet: "ik wil
  mijn eigen koersen niet opvolgen").

A quiet night still gets an edition. It says plainly that little moved, and
puts the weight on "vandaag". It never pads with filler.

The page opens with the newest edition and shows, next to it, what changed
since the reader's last visit. Those changes are computed from the other docs,
not written here.

Also here: the call-staleness rule. Once the same pick has stood for more than
STALE_CALL_DAYS calendar days,
the morning call must either name a NEW sourced fact that makes it the best
idea again, or put a fresh candidate forward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

EDITIONS = ("ochtend", "middag", "avond")
ITEM_KINDS = ("gebeurd", "betekent", "vandaag")
MIN_ITEMS, MAX_ITEMS = 2, 5
MAX_PULSE = 6
MAX_HEADLINE = 160
STALE_CALL_DAYS = 3


@dataclass(frozen=True)
class BriefItem:
    kind: str  # one of ITEM_KINDS
    text: str  # one or two plain sentences
    source: str  # for "gebeurd": the outside source; otherwise the team doc it rests on


@dataclass(frozen=True)
class PulseItem:
    name: str  # e.g. "S&P 500-futures", "Brent", "VS 10-jaarsrente"
    value: str  # as reported, e.g. "4,906%" or "USD 115,81"
    change: str  # as reported, e.g. "-6 bp", "-1,1%"; "" if the source gives none
    source: str
    as_of: str  # when the figure was taken, as the source dates it


@dataclass(frozen=True)
class Briefing:
    edition: str  # one of EDITIONS
    headline: str
    items: list[BriefItem]
    observed_at: str  # RFC3339
    pulse: list[PulseItem] = field(default_factory=list)


@dataclass(frozen=True)
class BriefingValidationResult:
    ok: bool
    errors: list[str]


def edition_for_hour(utc_hour: int) -> str:
    """Before 11:00 UTC ochtend, before 14:00 middag, after that avond."""
    if utc_hour < 11:
        return "ochtend"
    if utc_hour < 14:
        return "middag"
    return "avond"


def validate_briefing(b: Briefing) -> BriefingValidationResult:
    errors: list[str] = []
    if b.edition not in EDITIONS:
        errors.append(f"editie {b.edition!r} is geen van {EDITIONS}")
    head = b.headline.strip()
    if not head:
        errors.append("geen kop: wat moet Paul vandaag weten?")
    elif len(head) > MAX_HEADLINE:
        errors.append(f"kop is {len(head)} tekens, hoogstens {MAX_HEADLINE}")
    if not MIN_ITEMS <= len(b.items) <= MAX_ITEMS:
        errors.append(f"{len(b.items)} punten, verwacht {MIN_ITEMS} tot {MAX_ITEMS}")
    for i in b.items:
        if i.kind not in ITEM_KINDS:
            errors.append(f"punt-soort {i.kind!r} is geen van {ITEM_KINDS}")
        if not i.text.strip():
            errors.append("een leeg punt")
        if not i.source.strip():
            errors.append(f"{i.kind}: zonder bron is het een gevoel")
    if not any(i.kind == "vandaag" for i in b.items):
        errors.append("geen 'vandaag': waar let Paul vandaag op?")
    if len(b.pulse) > MAX_PULSE:
        errors.append(f"{len(b.pulse)} marktcijfers, hoogstens {MAX_PULSE}")
    for p in b.pulse:
        for name, text in (("name", p.name), ("value", p.value), ("source", p.source), ("as_of", p.as_of)):
            if not text.strip():
                errors.append(f"marktcijfer {p.name or '?'}: {name} ontbreekt")
    if not b.observed_at.strip():
        errors.append("observed_at ontbreekt")
    return BriefingValidationResult(ok=not errors, errors=errors)


def call_streak(calls: list[dict]) -> tuple[str, int, str]:
    """(subject, days, since) for the standing idea in `capital_calls` docs.

    `calls` is newest first. Days counts calendar days since the first call in
    the unbroken run of the same subject, inclusive, so today's first call on a
    new pick is day 1.
    """
    if not calls:
        return "", 0, ""
    subject = calls[0].get("subject", "")
    since = calls[0].get("observed_at", "")
    for c in calls[1:]:
        if c.get("subject", "") != subject:
            break
        since = c.get("observed_at", since)
    newest = date.fromisoformat(calls[0]["observed_at"][:10])
    first = date.fromisoformat(since[:10])
    return subject, (newest - first).days + 1, since


def call_is_stale(calls: list[dict]) -> bool:
    """True once the standing pick is older than STALE_CALL_DAYS (day 4 on)."""
    return call_streak(calls)[1] > STALE_CALL_DAYS
