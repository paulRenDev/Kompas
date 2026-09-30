"""Pijler B orchestration — the one place that knows the order of operations.

Still takes raw dump text as input rather than fetching it, so the full
pipeline is testable without a live session (see kompas/db/kompas_db.py for
why the fetch/write edges can't be pure). A real cycle's outer loop (inside
a Claude session) is: fetch raw text -> call run_cycle -> if not
result.ok: report and stop -> else: pass write_batch to ArtifactData.batch,
pinned with if_version read just before writing.
"""

from __future__ import annotations

from dataclasses import dataclass

from kompas.core.schema import PortfolioSnapshot, ReconciliationResult
from kompas.db.kompas_db import build_batch
from kompas.pijler_b.parser import parse_aandelen_csv, parse_aandelen_dump
from kompas.pijler_b.reconcile import reconcile


@dataclass(frozen=True)
class CycleResult:
    snapshot: PortfolioSnapshot
    reconciliation: ReconciliationResult
    write_batch: list[dict] | None  # None when reconciliation failed — nothing to write


def run_cycle(raw_dump_text: str) -> CycleResult:
    return _run(parse_aandelen_dump(raw_dump_text))


def run_cycle_csv(
    csv_text: str,
    previous_qty: dict[str, float] | None = None,
    previous_refreshed_at: str | None = None,
) -> CycleResult:
    """previous_qty: {wallet-positions doc id: qty} as read from the database
    just before this refresh -- needed to record what Paul bought or sold."""
    return _run(parse_aandelen_csv(csv_text), previous_qty, previous_refreshed_at)


def _run(
    snapshot: PortfolioSnapshot,
    previous_qty: dict[str, float] | None = None,
    previous_refreshed_at: str | None = None,
) -> CycleResult:
    result = reconcile(snapshot)
    batch = build_batch(snapshot, result, previous_qty=previous_qty, previous_refreshed_at=previous_refreshed_at) if result.ok else None
    return CycleResult(snapshot=snapshot, reconciliation=result, write_batch=batch)
