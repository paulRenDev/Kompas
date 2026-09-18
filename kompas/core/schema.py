"""Poort 2 (Portefeuillebron) data shapes.

These belong to the core, not to any adapter: every Poort 2 adapter (the
Google Sheet adapter today, a Bolero/custodian adapter later) must produce
these shapes. Nothing here knows about Google Sheets, ledgers, or ACTIVE
columns — that detail lives entirely in kompas/pijler_b/parser.py.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Position:
    """An active holding — real money, real cost basis (PORTEFEUILLE)."""

    name: str
    ticker: str
    exchange: str
    type_effect: str
    currency: str
    qty: float
    cost_eur: float
    value_eur: float
    gain_eur: float
    gain_pct: float


@dataclass(frozen=True)
class WatchlistEntry:
    """A name being watched, not owned.

    gain_pct here is an opportunity-cost indicator — "what one hypothetical
    share would have gained or lost since this name was put on the
    watchlist" — never real P&L. Do not rename these fields to look like
    Position's; the distinction is the point (see README, "Werkelijke
    portefeuille-structuur").
    """

    name: str
    ticker: str
    exchange: str
    type_effect: str
    currency: str
    set_date: str
    reference_value_eur: float
    current_value_eur: float
    opportunity_gain_eur: float
    opportunity_gain_pct: float


@dataclass(frozen=True)
class PortfolioSummary:
    """The sheet's own totals row for PORTEFEUILLE — never recomputed here."""

    value_eur: float
    cost_eur: float
    gain_eur: float
    gain_pct: float


@dataclass(frozen=True)
class PortfolioSnapshot:
    positions: list[Position] = field(default_factory=list)
    watchlist: list[WatchlistEntry] = field(default_factory=list)
    summary: PortfolioSummary | None = None


@dataclass(frozen=True)
class ReconciliationResult:
    """Poort B's hard publication gate: computed vs. the sheet's own totals."""

    ok: bool
    computed_value_eur: float
    computed_cost_eur: float
    computed_gain_eur: float
    computed_gain_pct: float
    sheet_value_eur: float
    sheet_cost_eur: float
    sheet_gain_eur: float
    sheet_gain_pct: float
    diffs: dict[str, float]
    watchlist_count: int
