"""Reconciliation — the hard publication gate for Poort 2.

Recomputes portfolio totals independently from the parsed positions and
compares them against the sheet's own summary row. Never publish (write to
the Kompas database) on a mismatch outside tolerance — this is the rule the
old Kompas never actually enforced; here it's a function that returns
ok=False rather than a paragraph asking nicely.
"""

from __future__ import annotations

from kompas.core.schema import PortfolioSnapshot, ReconciliationResult

# Rounding in the sheet's own display (amounts shown to 1-2 decimals) can
# create a cent-level gap between an independently summed total and the
# sheet's own rounded summary row. This tolerance exists for that, not to
# paper over a real discrepancy.
TOLERANCE_EUR = 0.10
TOLERANCE_PCT = 0.05


def reconcile(snapshot: PortfolioSnapshot) -> ReconciliationResult:
    if snapshot.summary is None:
        raise ValueError("cannot reconcile a snapshot with no summary row")

    computed_value = sum(p.value_eur for p in snapshot.positions)
    computed_cost = sum(p.cost_eur for p in snapshot.positions)
    computed_gain = computed_value - computed_cost
    computed_gain_pct = (computed_gain / computed_cost * 100) if computed_cost else 0.0

    diffs = {
        "value_eur": round(computed_value - snapshot.summary.value_eur, 2),
        "cost_eur": round(computed_cost - snapshot.summary.cost_eur, 2),
        "gain_eur": round(computed_gain - snapshot.summary.gain_eur, 2),
        "gain_pct": round(computed_gain_pct - snapshot.summary.gain_pct, 2),
    }

    ok = (
        abs(diffs["value_eur"]) <= TOLERANCE_EUR
        and abs(diffs["cost_eur"]) <= TOLERANCE_EUR
        and abs(diffs["gain_eur"]) <= TOLERANCE_EUR
        and abs(diffs["gain_pct"]) <= TOLERANCE_PCT
    )

    return ReconciliationResult(
        ok=ok,
        computed_value_eur=round(computed_value, 2),
        computed_cost_eur=round(computed_cost, 2),
        computed_gain_eur=round(computed_gain, 2),
        computed_gain_pct=round(computed_gain_pct, 2),
        sheet_value_eur=snapshot.summary.value_eur,
        sheet_cost_eur=snapshot.summary.cost_eur,
        sheet_gain_eur=snapshot.summary.gain_eur,
        sheet_gain_pct=snapshot.summary.gain_pct,
        diffs=diffs,
        watchlist_count=len(snapshot.watchlist),
    )
