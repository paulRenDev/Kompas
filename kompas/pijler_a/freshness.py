"""Signaalversheid — the lookup half of the freshness gate.

See README, "Signaalversheid — geen herhaling zonder wijziging": a memory
that can only detect a repeat but doesn't block publication is decoration.
This module is the deterministic half of that gate — finding what was
already said about a subject. Whether a new candidate is a MATERIAL change
over what it finds is a judgment call (new figures, a broken technical
level, new sector data) that belongs to whoever is running the cycle, not
to a pure function — so this stops at "here is the prior art," on purpose,
the same way kompas/db/kompas_db.py stops at building payloads instead of
performing the write.
"""

from __future__ import annotations


def find_prior_signals(
    events: list[dict],
    subject: str,
    *,
    role: str | None = None,
) -> list[dict]:
    """Events already on record for this subject (case-insensitive), most
    recent first. Empty in means nothing to compare against — always fresh.
    """
    subject_l = subject.strip().lower()
    matches = [
        e
        for e in events
        if str(e.get("subject", "")).strip().lower() == subject_l
        and (role is None or e.get("role") == role)
    ]
    return sorted(matches, key=lambda e: e.get("observed_at", ""), reverse=True)
