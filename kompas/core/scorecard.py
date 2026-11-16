"""Farah's scorecard -- the team keeps score on itself, with free sources.

Paul, 16/11/2026, on Farah's wish to keep score: "top idee, maar ik ben nog
niet bereid om te betalen voor bronnen." So scoring runs inside Farah's
weekly session, with prices the team finds in public, citable sources
(exchange pages, fund pages, news). When a price can't be found, the entry
says "onbekend": an honest gap beats an invented number.

Two kinds of entry:
- a CALL IDEA, scored per idea, not per day: one run of calls on the same
  subject counts once, from its first day. After 7 and after 28 days the
  team compares the idea with simply buying more of the core (IWDA), since
  that is what the money would otherwise do. "beter", "gelijk" or
  "slechter" than IWDA, within BAND percentage points.
- a PLAYBOOK, scored once it is voorbij, or 28 days after it went actief:
  did the what-if happen, and was the disruption estimate about right?

Never Paul's own positions or purchases: the instruments the team named, at
public prices.
"""

from __future__ import annotations

from dataclasses import dataclass

HORIZONS = (7, 28)  # days after an idea's first call
BAND = 2.0  # percentage points either side of IWDA that count as "gelijk"
CALL_VERDICTS = ("beter", "gelijk", "slechter", "onbekend")
PLAYBOOK_VERDICTS = ("uitgekomen", "niet_uitgekomen", "deels")


@dataclass(frozen=True)
class CallScore:
    idea: str  # capital_calls doc id of the first call in the run
    subject: str
    given_at: str  # RFC3339, the first call's observed_at
    horizon_days: int  # one of HORIZONS
    change_pct: float | None  # the named instrument over the horizon, in %
    bench_change_pct: float | None  # IWDA over the same days, in %
    prices: str  # the closes used, as reported, e.g. "TTE EUR 80,10 -> 82,71; IWDA ..."
    source: str
    scored_at: str  # RFC3339


@dataclass(frozen=True)
class PlaybookScore:
    key: str
    what_if: str
    verdict: str  # one of PLAYBOOK_VERDICTS
    disruption_then: int  # the score it had when written
    what_happened: str  # one or two sentences, with the market reaction if any
    source: str
    scored_at: str  # RFC3339


@dataclass(frozen=True)
class ScoreValidationResult:
    ok: bool
    errors: list[str]


def call_verdict(change_pct: float | None, bench_change_pct: float | None) -> str:
    if change_pct is None or bench_change_pct is None:
        return "onbekend"
    gap = change_pct - bench_change_pct
    if gap >= BAND:
        return "beter"
    if gap <= -BAND:
        return "slechter"
    return "gelijk"


def validate_call_score(s: CallScore) -> ScoreValidationResult:
    errors: list[str] = []
    if s.horizon_days not in HORIZONS:
        errors.append(f"horizon {s.horizon_days} is geen van {HORIZONS}")
    for name, text in (("idea", s.idea), ("subject", s.subject), ("given_at", s.given_at), ("scored_at", s.scored_at)):
        if not text.strip():
            errors.append(f"{name} ontbreekt")
    known = s.change_pct is not None and s.bench_change_pct is not None
    if known and (not s.prices.strip() or not s.source.strip()):
        errors.append("een score zonder de gebruikte koersen en hun bron is niet na te gaan")
    return ScoreValidationResult(ok=not errors, errors=errors)


def validate_playbook_score(s: PlaybookScore) -> ScoreValidationResult:
    errors: list[str] = []
    if s.verdict not in PLAYBOOK_VERDICTS:
        errors.append(f"oordeel {s.verdict!r} is geen van {PLAYBOOK_VERDICTS}")
    if s.disruption_then not in range(1, 6):
        errors.append("disruption_then valt buiten 1 tot 5")
    for name, text in (("key", s.key), ("what_if", s.what_if), ("what_happened", s.what_happened),
                       ("source", s.source), ("scored_at", s.scored_at)):
        if not text.strip():
            errors.append(f"{name} ontbreekt")
    return ScoreValidationResult(ok=not errors, errors=errors)


def call_ideas(calls: list[dict]) -> list[dict]:
    """The first call of every run of the same subject, oldest first.
    `calls` may come in any order."""
    ordered = sorted(calls, key=lambda c: c.get("observed_at", ""))
    ideas: list[dict] = []
    for c in ordered:
        if not ideas or ideas[-1].get("subject") != c.get("subject"):
            ideas.append(c)
    return ideas
