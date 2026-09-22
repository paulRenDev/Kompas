"""Poort 1 -- combining multiple signals on one subject into one read.

Named after the pattern in the Bracket22 article Paul shared (Kelly's
four-agent trading desk): Houston (mission controller) pulls the pieces
together into one narrative; Doocy (red team) tries to tear that
narrative down before it ships. Kompas already had the equivalent of
Desmond (fundamentals/news -- Stock watchers + sector specialists) and
Steffi (technicals -- Technical stock watchers) as independent roles;
this module is the missing piece that combines their output per subject
instead of leaving it as unreconciled, side-by-side signals.

Synthesis is deliberately NOT a fifth capital_view that averages the
others away -- see kompas/core/signal.py and the README's
"Conflict zichtbaar gehouden, niet gemiddeld" principle. It sits on top
of the underlying signals (referenced by id, never duplicated) and adds
one thing they don't have on their own: a combined narrative that says
plainly where the angles agree and where they don't, followed by a red
team pass and only then a final stance. Kelly still pulls the trigger
himself ("the meat in the seat") -- so does Paul; capital_view here is
exactly as hypothetical/non-executing as it is on a single Signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kompas.core.signal import CapitalView, CAPITAL_VIEW_ACTIONS


@dataclass(frozen=True)
class RedTeamChallenge:
    """Doocy's job: argue against the thesis Houston just built, using the
    same facts. Not a formality -- if nothing here is a genuine attempt to
    break the thesis, it isn't a red team, it's a rubber stamp."""

    objection: str  # the strongest real case against the thesis
    survives: bool  # did the thesis hold up against this objection?


@dataclass(frozen=True)
class Synthesis:
    subject: str
    narrative: str  # Houston's combined read -- names where signals agree/disagree
    signal_ids: list[str]  # doc_ids of the underlying events this combines (2+)
    red_team: RedTeamChallenge
    capital_view: CapitalView
    observed_at: str  # RFC3339
    related_positions: list[str] = field(default_factory=list)
    related_watchlist: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SynthesisValidationResult:
    ok: bool
    errors: list[str]


def validate_synthesis(synthesis: Synthesis) -> SynthesisValidationResult:
    """A synthesis that fails this never gets published -- same discipline
    as validate_signal for a single Signal."""
    errors: list[str] = []

    if not synthesis.narrative.strip():
        errors.append("narrative ontbreekt")

    if len(synthesis.signal_ids) < 2:
        errors.append("synthesis vereist minstens 2 onderliggende signalen -- anders is er niets om samen te voegen")

    if not synthesis.red_team.objection.strip():
        errors.append("red_team.objection ontbreekt -- geen rubber stamp zonder een echte tegenwerping")

    cv = synthesis.capital_view
    if cv.action not in CAPITAL_VIEW_ACTIONS:
        errors.append(f"capital_view.action {cv.action!r} is geen van {CAPITAL_VIEW_ACTIONS}")
    if not cv.reasoning.strip():
        errors.append("capital_view.reasoning ontbreekt")
    if not cv.trigger.strip():
        errors.append("capital_view.trigger ontbreekt")
    if cv.action == "verhoog_bestaand" and not synthesis.related_positions:
        errors.append(
            "capital_view 'verhoog_bestaand' vereist een echte related_positions-tag "
            "-- een watchlist-naam is geen positie"
        )

    return SynthesisValidationResult(ok=not errors, errors=errors)
