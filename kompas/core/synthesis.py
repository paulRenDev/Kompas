"""Poort 1 -- combining multiple signals on one subject into one read.

Named after the pattern in the Bracket22 article Paul shared (Kelly's
four-agent trading desk), with Paul's own cast: Vera (mission controller)
pulls the pieces together into one narrative; Farah (red team) tries to
tear that narrative down before it ships. Kompas already had the
equivalent of Naomi (fundamentals/news -- Stock watchers + sector
specialists) and Mila (technicals -- Technical stock watchers) as
independent roles; this module is the missing piece that combines their
output per subject instead of leaving it as unreconciled, side-by-side
signals. All four are modeled as decisive, high-performing specialists,
Paul's explicit choice -- and it lines up with the actual fix already
underway in "Het 'wacht'-probleem" (README): balanced conviction, not
reflexive caution, is the whole point of this module existing.

Synthesis is deliberately NOT a fifth capital_view that averages the
others away -- see kompas/core/signal.py and the README's
"Conflict zichtbaar gehouden, niet gemiddeld" principle. It sits on top
of the underlying signals (referenced by id, never duplicated) and adds
one thing they don't have on their own: a combined narrative that says
plainly where the angles agree and where they don't, followed by a real
red team pass.

Synthesis used to end in its own capital_view -- one per subject. Paul
caught the same repetition here as on individual signals ("you can't
just keep repeating to wait"): three syntheses each landing on "wacht"
is still three repeated non-answers, just one level up. The final
euro-call moved out of here entirely, into kompas/core/capital_call.py --
ONE answer per cycle, built after weighing everything (signals AND
syntheses) together, never one per subject.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RedTeamChallenge:
    """Farah's job: argue against the thesis Vera just built, using the
    same facts. Not a formality -- if nothing here is a genuine attempt to
    break the thesis, it isn't a red team, it's a rubber stamp."""

    objection: str  # the strongest real case against the thesis
    survives: bool  # did the thesis hold up against this objection?


@dataclass(frozen=True)
class Synthesis:
    subject: str
    narrative: str  # Vera's combined read -- names where signals agree/disagree
    signal_ids: list[str]  # doc_ids of the underlying events this combines (2+)
    red_team: RedTeamChallenge
    observed_at: str  # RFC3339
    related_positions: list[str] = field(default_factory=list)
    related_watchlist: list[str] = field(default_factory=list)
    # Same recap lifecycle as Signal.relevant/closed_reason -- see
    # kompas/core/signal.py for why this exists and why it's never a delete.
    relevant: bool = True
    closed_reason: str | None = None


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

    if not synthesis.relevant and not (synthesis.closed_reason or "").strip():
        errors.append("closed_reason ontbreekt -- een niet langer relevante synthese moet zeggen waarom")

    return SynthesisValidationResult(ok=not errors, errors=errors)
