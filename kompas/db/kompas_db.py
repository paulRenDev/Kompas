"""Poort 3 (Geheugen/opslag) — write payloads for the Google Sheet adapter.

Honest platform constraint, stated once here instead of implied everywhere:
`ArtifactData` (like `mcp__Google_Drive__read_file_content`) is an MCP tool
only callable from inside a live Claude/Claude Code session — there is no
API key or SDK in this repo that lets a bare `python cycle.py` reach it.
That is why this module stops at building the write payloads (pure, tested
below) rather than performing the write itself.

The runbook for a real cycle, executed by whatever Claude session is
running it:
    1. Call mcp__Google_Drive__read_file_content(fileId=AANDELEN_SHEET_ID),
       extract .fileContent.
    2. snapshot = parser.parse_aandelen_dump(file_content)
    3. result  = reconcile.reconcile(snapshot)
    4. if not result.ok: stop, do not write, report the diff.
    5. else: build_batch(snapshot, result) -> pass the returned list
       straight to the ArtifactData `batch` call, with `if_version` filled
       in from whatever `get`/`list` returned for each doc just before
       writing (never write blind — see README, "De Kompas-database").

Everything below this point is pure and unit-tested against the fixture.
"""

from __future__ import annotations

from datetime import datetime, timezone

from kompas.core.schema import PortfolioSnapshot, Position, ReconciliationResult, WatchlistEntry

AANDELEN_SHEET_ID = "1l1XSohzp0wS8JAQFaMTGkJe0zrur1BKbZdkbN6MLR7A"
ARTIFACT_URL = "https://claude.ai/code/artifact/9f6bc549-e4df-4082-874b-cf5907bbaab0"


def wallet_state_doc(result: ReconciliationResult, refreshed_at: str) -> dict:
    return {
        "path": "wallet/state",
        "value_eur": result.computed_value_eur,
        "cost_eur": result.computed_cost_eur,
        "gain_eur": result.computed_gain_eur,
        "gain_pct": result.computed_gain_pct,
        "reconciled": result.ok,
        "refreshed_at": refreshed_at,
    }


def wallet_position_doc(position: Position, refreshed_at: str) -> dict:
    return {
        "path": f"wallet-positions/{position.ticker}",
        "name": position.name,
        "ticker": position.ticker,
        "exchange": position.exchange,
        "type_effect": position.type_effect,
        "currency": position.currency,
        "qty": position.qty,
        "cost_eur": position.cost_eur,
        "value_eur": position.value_eur,
        "gain_eur": position.gain_eur,
        "gain_pct": position.gain_pct,
        "refreshed_at": refreshed_at,
    }


def watchlist_doc(entry: WatchlistEntry, refreshed_at: str) -> dict:
    return {
        "path": f"watchlist/{entry.ticker}",
        "name": entry.name,
        "ticker": entry.ticker,
        "exchange": entry.exchange,
        "type_effect": entry.type_effect,
        "currency": entry.currency,
        "set_date": entry.set_date,
        "reference_value_eur": entry.reference_value_eur,
        "current_value_eur": entry.current_value_eur,
        "opportunity_gain_eur": entry.opportunity_gain_eur,
        "opportunity_gain_pct": entry.opportunity_gain_pct,
        "refreshed_at": refreshed_at,
    }


def meta_refresh_doc(result: ReconciliationResult, refreshed_at: str) -> dict:
    return {
        "path": "meta/last_refresh",
        "pijler": "B",
        "reconciled": result.ok,
        "diffs": result.diffs,
        "watchlist_count": result.watchlist_count,
        "refreshed_at": refreshed_at,
    }


def build_batch(
    snapshot: PortfolioSnapshot,
    result: ReconciliationResult,
    refreshed_at: str | None = None,
) -> list[dict]:
    """The full write set for one Pijler B cycle. Caller must check
    result.ok first — this function does not check it for you, on purpose:
    a cycle script that calls build_batch without checking ok first is a
    bug the type checker/reviewer should catch, not something this
    function should silently guard.
    """
    refreshed_at = refreshed_at or datetime.now(timezone.utc).isoformat()
    docs = [wallet_state_doc(result, refreshed_at)]
    docs += [wallet_position_doc(p, refreshed_at) for p in snapshot.positions]
    docs += [watchlist_doc(w, refreshed_at) for w in snapshot.watchlist]
    docs.append(meta_refresh_doc(result, refreshed_at))
    return docs
