"""Poort 1 -- the ONE EUR 100 answer per cycle, not N repeated ones.

Paul: "you can't just keep repeating to wait... make it a separate line.
If we (and by we I mean the team) had 100 to spend, take this. In the
end I will decide if I follow." That is a direct fix for a concrete
problem: capital_view used to live on every Signal and every Synthesis,
so a recap with twelve signals showed twelve near-identical "wacht"
verdicts. Each one was individually honest -- most subjects really
weren't actionable that day -- but the aggregate read as noise, and it
buried the one thing a daily recap actually needs to answer: if the
team weighs everything it saw this cycle TOGETHER, is there one real
idea worth naming?

CapitalCall is that single answer, built once per cycle after the
cycle's signals and syntheses are written -- never duplicated per item.
`considered` names what it weighed (subjects or signal/synthesis ids),
by reference, so nothing here re-states a Signal or Synthesis. Kelly
still pulls the trigger himself ("the meat in the seat") -- so does
Paul; this is exactly as hypothetical/non-executing as the old
per-signal capital_view was. A genuine "wacht" with no standout subject
is still a real answer and needs no `subject` -- this must never be
forced into naming something just to look decisive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kompas.core.signal import CAPITAL_VIEW_ACTIONS, CapitalView


@dataclass(frozen=True)
class CapitalCall:
    capital_view: CapitalView
    observed_at: str  # RFC3339
    considered: list[str] = field(default_factory=list)  # subjects/signal_ids weighed this cycle
    subject: str | None = None  # the name this call is about; None for a genuine "nothing stands out"


@dataclass(frozen=True)
class CapitalCallValidationResult:
    ok: bool
    errors: list[str]


def validate_capital_call(call: CapitalCall) -> CapitalCallValidationResult:
    """The publication gate for the cycle's one capital call -- same
    discipline as validate_signal/validate_synthesis."""
    errors: list[str] = []

    if not call.observed_at.strip():
        errors.append("observed_at ontbreekt")

    if not call.considered:
        errors.append(
            "considered ontbreekt -- een capital call zonder vermelding van wat er "
            "afgewogen is, is niet controleerbaar"
        )

    cv = call.capital_view
    if cv.action not in CAPITAL_VIEW_ACTIONS:
        errors.append(f"capital_view.action {cv.action!r} is geen van {CAPITAL_VIEW_ACTIONS}")
    if not cv.reasoning.strip():
        errors.append("capital_view.reasoning ontbreekt")
    if not cv.trigger.strip():
        errors.append(
            "capital_view.trigger ontbreekt -- vooral bij 'wacht' verplicht: zonder een "
            "concrete voorwaarde is 'wacht' nooit fout, en dus geen echt standpunt"
        )
    if cv.action in ("nieuwe_positie", "verhoog_bestaand") and not (call.subject or "").strip():
        errors.append(
            f"capital_view {cv.action!r} vereist een subject -- een actie zonder naam "
            "is geen echt standpunt"
        )

    return CapitalCallValidationResult(ok=not errors, errors=errors)
