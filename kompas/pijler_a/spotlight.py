"""Poort 1 -- grouping published signals into the richer feed layout.

Pure, read-only grouping over the `events` collection. One mechanical
grouping, no interpretation:

- cross_specialist_subjects: a subject touched by 2+ distinct roles is
  shown as a "spotlight" card (the intersection IS the story -- see
  README, sector-spotlight mockup). A subject touched by exactly one role
  stays in the plain per-role grid (single_role_events/group_by_role).

Conflict between signals is NOT inferred here -- see Signal.conflict_note
in kompas/core/signal.py. Whether two signals genuinely disagree (e.g.
"technical trend bearish but momentum neutral, not exhaustion") is an
editorial judgment made by reading both texts, not a mechanical diff of
confidence levels or roles; an algorithm guessing at that would either
flag false conflicts or miss real ones -- worse than showing none.
"""

from __future__ import annotations

from collections import defaultdict


def group_by_subject(events: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        groups[event["subject"]].append(event)
    return dict(groups)


def cross_specialist_subjects(events: list[dict]) -> list[str]:
    """Subjects touched by 2+ distinct roles, most recently observed first.

    This is the mechanical half of what the mockup calls a "sector
    spotlight": a real intersection between roles, not one specialist's
    own read shown large. Order matters for the feed: newest first.
    """
    groups = group_by_subject(events)
    subjects = [
        subject
        for subject, items in groups.items()
        if len({item["role"] for item in items}) >= 2
    ]
    subjects.sort(key=lambda s: max(item["observed_at"] for item in groups[s]), reverse=True)
    return subjects


def single_role_events(events: list[dict]) -> list[dict]:
    """The complement of cross_specialist_subjects: signals whose subject
    only one role has touched so far -- rendered in the plain per-role
    grid rather than as a spotlight card."""
    spotlight_subjects = set(cross_specialist_subjects(events))
    return [e for e in events if e["subject"] not in spotlight_subjects]


def group_by_role(events: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        groups[event["role"]].append(event)
    return dict(groups)


def events_with_conflict_notes(events: list[dict]) -> list[dict]:
    """Signals an author explicitly flagged as contradicting another one --
    never inferred, see module docstring."""
    return [e for e in events if (e.get("conflict_note") or "").strip()]
