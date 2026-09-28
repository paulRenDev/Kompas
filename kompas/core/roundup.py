"""The evening portfolio round-up -- where Pijler A and Pijler B meet.

Paul, 28/9/2026: "an update end of day of my positions would be nice, as
would a short round up like this would do good in the evening update."
"Like this" was a portfolio-wide read: what the positions add up to, how
that compares with his own target allocation in the sheet, what today's
signals mean for what he actually holds -- and one EUR 100 answer (which
is written separately, as that evening's CapitalCall, never repeated here).

Positions only. Paul, same day: "don't take into account my watchlist.
these are not positions." The watchlist feeds signal tagging, never this.

Short on purpose: MAX_TEXT_CHARS is a hard cap, not a suggestion -- a
round-up that needs more room is doing the signal feed's job.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_TEXT_CHARS = 900


@dataclass(frozen=True)
class PortfolioRoundup:
    text: str
    observed_at: str  # RFC3339
    value_eur: float
    gain_eur: float
    gain_pct: float
    day_change_eur: float | None = None


@dataclass(frozen=True)
class RoundupValidationResult:
    ok: bool
    errors: list[str]


def validate_roundup(roundup: PortfolioRoundup) -> RoundupValidationResult:
    errors: list[str] = []
    text = roundup.text.strip()
    if not text:
        errors.append("text ontbreekt")
    elif len(text) > MAX_TEXT_CHARS:
        errors.append(f"text is {len(text)} tekens, max {MAX_TEXT_CHARS} -- een round-up is kort")
    if not roundup.observed_at.strip():
        errors.append("observed_at ontbreekt")
    if roundup.value_eur <= 0:
        errors.append("value_eur moet positief zijn -- geschreven tegen een lege of mislukte refresh?")
    return RoundupValidationResult(ok=not errors, errors=errors)
