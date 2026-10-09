"""Sell proposals -- allowed since 9/10/2026, under a written plan.

Until then the rule was "never propose selling". Paul lifted it after the
AI-bubble monitor went live: "Zeker! Mag! Ik volg jullie oordeel. Jullie
taak samen is het rendement ten allen tijde te beschermen en optimaliseren."

That mandate cuts both ways. Selling to protect costs beurstaks, spread and
possibly meerwaardebelasting, and a sale that's wrong twice (out too early,
back in too late) destroys more return than a drawdown it was meant to
dodge. So the team may propose a sale only in two situations, both written
down here so the bar can't drift with the mood of a single day:

1. The de-risk plan (DERISK_PLAN): agreed with Paul in calm, executed when
   the bubble monitor says "alarm" -- move a third of IWDA to value and
   gold. Its mirror image, the re-entry rule, says when to move back.
2. A broken thesis: a sourced fact that kills the reason a specific
   position is held (not a bad day, not a scary headline).

A proposal is hypothetical and non-executing, like every call: Paul trades
himself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DERISK_PLAN = {
    "trigger": "de AI-bubbelmonitor staat op alarm (drie of meer indicatoren rood)",
    "sell_ticker": "IWDA",
    "sell_fraction": 1 / 3,
    # where the proceeds go, as fractions of the amount sold
    "buy": {
        "IWVL": 0.5,  # value: held up far better than growth after 2000
        "PPFB": 0.5,  # iShares Physical Gold ETC, IE00B4ND3602, Xetra in EUR -- Dalio's own hedge
    },
    "re_entry": (
        "terug naar IWDA wanneer de monitor 20 beursdagen op rustig staat, of wanneer de "
        "Nasdaq-100 meer dan 30% onder zijn top staat (dan is de bubbel geprikt en is "
        "goedkoop terugkopen de kans)"
    ),
}

SOURCES = ("plan", "these_breuk", "herinstap")


@dataclass(frozen=True)
class Leg:
    ticker: str
    amount_eur: float


@dataclass(frozen=True)
class SellProposal:
    source: str  # one of SOURCES
    sell: list[Leg]
    buy: list[Leg]  # may be empty: proceeds stay in cash
    reasoning: str  # why now, with sourced facts
    costs: str  # beurstaks, spread, meerwaardebelasting -- named, not ignored
    undo: str  # what would make the team reverse this
    observed_at: str
    signal_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SellValidationResult:
    ok: bool
    errors: list[str]


def derisk_legs(value_by_ticker: dict[str, float]) -> tuple[list[Leg], list[Leg]]:
    """The plan in euros, from the live wallet (values summed per ticker)."""
    amount = round(value_by_ticker.get(DERISK_PLAN["sell_ticker"], 0.0) * DERISK_PLAN["sell_fraction"], 2)
    sell = [Leg(DERISK_PLAN["sell_ticker"], amount)]
    buy = [Leg(t, round(amount * f, 2)) for t, f in DERISK_PLAN["buy"].items()]
    return sell, buy


def validate_sell_proposal(p: SellProposal, value_by_ticker: dict[str, float]) -> SellValidationResult:
    errors: list[str] = []
    if p.source not in SOURCES:
        errors.append(f"source {p.source!r} is geen van {SOURCES}")
    if not p.sell:
        errors.append("een verkoopvoorstel zonder verkoop")
    for leg in p.sell:
        held = value_by_ticker.get(leg.ticker, 0.0)
        if leg.amount_eur <= 0:
            errors.append(f"{leg.ticker}: bedrag moet positief zijn")
        elif leg.amount_eur > held + 0.01:
            errors.append(f"{leg.ticker}: verkoopt EUR {leg.amount_eur:.2f} maar Paul heeft er EUR {held:.2f}")
    sold = sum(l.amount_eur for l in p.sell)
    bought = sum(l.amount_eur for l in p.buy)
    if bought > sold + 0.01:
        errors.append("er wordt meer gekocht dan verkocht -- dat is geen verschuiving maar nieuw geld")
    for name, text in (("reasoning", p.reasoning), ("costs", p.costs), ("undo", p.undo), ("observed_at", p.observed_at)):
        if not text.strip():
            errors.append(f"{name} ontbreekt")
    if p.source == "these_breuk" and not p.signal_refs:
        errors.append("een gebroken these zonder signaal is een gevoel -- verwijs naar het signaal")
    return SellValidationResult(ok=not errors, errors=errors)
