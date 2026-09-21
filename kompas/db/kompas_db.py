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

import re
import unicodedata

from kompas.core.schema import PortfolioSnapshot, Position, ReconciliationResult, WatchlistEntry
from kompas.core.signal import Signal, validate_signal

AANDELEN_SHEET_ID = "1l1XSohzp0wS8JAQFaMTGkJe0zrur1BKbZdkbN6MLR7A"

# This Kompas build's own artifact + database — created 18/9/2026,
# separate from the old Stocazzo-linked Kompas artifact
# (https://claude.ai/code/artifact/9f6bc549-e4df-4082-874b-cf5907bbaab0).
# That one is NOT this project's database; an earlier version of this
# file pointed at it by mistake, carried over from the original design
# doc's description of the old system. Never write to that URL from here.
ARTIFACT_URL = "https://claude.ai/artifact/9NceTjMZzLgV99KMEGGh1e"


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


def _position_doc_id(position: Position) -> str:
    """Ticker alone is not unique: the real portfolio holds IWDA on both
    AMS and LON as separate positions. Composite id, found by trying to
    write the real data, not assumed up front."""
    return f"{position.ticker}-{position.exchange}"


def wallet_position_doc(position: Position, refreshed_at: str) -> dict:
    return {
        "path": f"wallet-positions/{_position_doc_id(position)}",
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


def _slugify(text: str) -> str:
    """A signal's doc id: readable, stable, ASCII-safe for the path grammar."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", normalized).strip("-").lower()
    return slug or "signal"


def signal_event_doc(signal: Signal, *, is_technical: bool = False) -> dict:
    """Poort 1's write payload for one signal into the `events` collection.

    Raises ValueError if the signal fails validate_signal — this function
    will not build a payload for a signal that could not be published, the
    same discipline as build_batch trusting reconciliation.ok: the caller
    is expected to have validated already, but this is cheap enough and
    consequential enough (bad data landing in the memory store) to check
    again here rather than only document the expectation.
    """
    result = validate_signal(signal, is_technical=is_technical)
    if not result.ok:
        raise ValueError(f"signal failed validation, not writing: {result.errors}")

    doc_id = f"{_slugify(signal.subject)}-{signal.observed_at[:10]}-{_slugify(signal.role)}"
    return {
        "path": f"events/{doc_id}",
        "role": signal.role,
        "subject": signal.subject,
        "text": signal.text,
        "source": signal.source,
        "source_tier": signal.source_tier,
        "magnitude": signal.magnitude,
        "timeframe_horizon": signal.timeframe_horizon,
        "data_confidence": signal.data_confidence,
        "signal_confidence": signal.signal_confidence,
        "chart_timeframe": signal.chart_timeframe,
        "related_positions": signal.related_positions,
        "related_watchlist": signal.related_watchlist,
        "conflict_note": signal.conflict_note,
        "capital_view": (
            {"action": signal.capital_view.action, "reasoning": signal.capital_view.reasoning}
            if signal.capital_view is not None
            else None
        ),
        "observed_at": signal.observed_at,
    }


def split_path(path: str) -> tuple[str, str]:
    """'wallet-positions/IWDA-AMS' -> ('wallet-positions', 'IWDA-AMS').

    ArtifactData's batch writes take `collection` and `doc_id` separately,
    not one path string — this is the one place that seam is crossed.
    """
    collection, _, doc_id = path.rpartition("/")
    if not collection or not doc_id:
        raise ValueError(f"not a collection/doc_id path: {path!r}")
    return collection, doc_id


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
