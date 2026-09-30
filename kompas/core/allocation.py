"""The team's allocation view -- what the portfolio should look like.

Paul, 28/9/2026: "hou niet vast aan de doelstellingen % verdeling die zijn
oud. ik wil dat het team me stuurt en energy transition maakt er natuurlijk
ook deel van uit." The target percentages in his sheet are retired as an
anchor. This replaces them with a view the team owns: sleeves with ranges,
a reason per sleeve, Vera's narrative, and Farah's red team -- the same
discipline as a Synthesis, because an allocation nobody tried to break is
just a guess with decimals.

Steering happens with new money only: a sleeve under its range is where the
next euro goes, a sleeve above it gets nothing new. Nothing here ever says
"sell" -- selling to rebalance costs tax and fees, and it's Paul's call.

Stable on purpose. A new view is written only when its own `trigger` fires
or something structural changes (a new position, a sold one), never as a
daily reshuffle -- steering that moves every day isn't steering.
"""

from __future__ import annotations

from dataclasses import dataclass

from kompas.core.synthesis import RedTeamChallenge


@dataclass(frozen=True)
class Sleeve:
    name: str
    low_pct: float
    high_pct: float
    holdings: list[str]  # position tickers that count toward this sleeve
    reasoning: str


@dataclass(frozen=True)
class AllocationView:
    sleeves: list[Sleeve]
    narrative: str  # Vera: why this shape, for this investor, now
    red_team: RedTeamChallenge  # Farah: the strongest case against it
    trigger: str  # what would make the team write a new view
    observed_at: str  # RFC3339


@dataclass(frozen=True)
class AllocationValidationResult:
    ok: bool
    errors: list[str]


def validate_allocation(view: AllocationView) -> AllocationValidationResult:
    errors: list[str] = []
    if not view.sleeves:
        errors.append("geen sleeves")
    seen: dict[str, str] = {}
    for s in view.sleeves:
        if not s.name.strip():
            errors.append("sleeve zonder naam")
        if not s.reasoning.strip():
            errors.append(f"sleeve {s.name!r}: reasoning ontbreekt")
        if not (0 <= s.low_pct <= s.high_pct <= 100):
            errors.append(f"sleeve {s.name!r}: range {s.low_pct}-{s.high_pct} is ongeldig")
        if not s.holdings and s.low_pct > 0:
            errors.append(f"sleeve {s.name!r}: een minimum boven 0% zonder posities kan niet gehaald worden")
        for t in s.holdings:
            if t in seen:
                errors.append(f"{t} staat in twee sleeves ({seen[t]!r} en {s.name!r})")
            seen[t] = s.name
    if view.sleeves:
        lows = sum(s.low_pct for s in view.sleeves)
        highs = sum(s.high_pct for s in view.sleeves)
        if lows > 100 or highs < 100:
            errors.append(f"ranges tellen niet op tot 100% (minima {lows}, maxima {highs})")
    if not view.narrative.strip():
        errors.append("narrative ontbreekt")
    if not view.red_team.objection.strip():
        errors.append("red_team.objection ontbreekt -- geen rubber stamp zonder een echte tegenwerping")
    if not view.trigger.strip():
        errors.append("trigger ontbreekt -- wanneer herziet het team deze verdeling?")
    return AllocationValidationResult(ok=not errors, errors=errors)


@dataclass(frozen=True)
class SleeveStatus:
    name: str
    weight_pct: float
    low_pct: float
    high_pct: float
    status: str  # "onder" / "binnen" / "boven"


def sleeve_status(view: AllocationView, value_by_ticker: dict[str, float]) -> tuple[list[SleeveStatus], list[str]]:
    """Actual weight per sleeve from current position values (summed per
    ticker across exchanges), plus the tickers no sleeve claims -- a new
    position the view doesn't know about yet is a reason to revisit it."""
    total = sum(value_by_ticker.values())
    out: list[SleeveStatus] = []
    for s in view.sleeves:
        w = round(sum(value_by_ticker.get(t, 0.0) for t in s.holdings) / total * 100, 2) if total else 0.0
        status = "onder" if w < s.low_pct else ("boven" if w > s.high_pct else "binnen")
        out.append(SleeveStatus(s.name, w, s.low_pct, s.high_pct, status))
    claimed = {t for s in view.sleeves for t in s.holdings}
    unassigned = sorted(t for t in value_by_ticker if t not in claimed)
    return out, unassigned


def steer_target(view: AllocationView, value_by_ticker: dict[str, float]) -> tuple[str, str]:
    """Where the next euro goes -- one fixed rule, so calls can't invent a
    new stopping point each time (they did: "until ~17%", then "until the
    midpoint", while Paul kept buying).

    1. A sleeve under its minimum: the one furthest under it.
    2. Otherwise: the sleeve furthest below the middle of its range.
    Returns (sleeve name, reason in plain Dutch)."""
    status, _ = sleeve_status(view, value_by_ticker)
    under = [s for s in status if s.weight_pct < s.low_pct]
    if under:
        s = max(under, key=lambda s: s.low_pct - s.weight_pct)
        return s.name, f"{s.name} staat op {s.weight_pct:.1f}%, onder het minimum van {s.low_pct:g}%"
    s = max(status, key=lambda s: (s.low_pct + s.high_pct) / 2 - s.weight_pct)
    mid = (s.low_pct + s.high_pct) / 2
    return s.name, f"alles binnen de marges; {s.name} zit het verst onder het midden ({s.weight_pct:.1f}% tegenover {mid:g}%)"
