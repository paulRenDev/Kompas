"""Poort 1 (Signaalbron) data shapes and the publication gate for them.

Belongs to the core, same reasoning as core/schema.py for Poort 2: every
Poort 1 adapter (today: the analyst roles + sector-specialist pool, doing
their own research via RSS/WebSearch/WebFetch) must produce this shape.
The fields here are not a suggestion — they were made a hard publication
requirement after the sector-analyst and technical-analyst reviews (see
README, Poort 1): a claim without a real source, a magnitude, a timeframe
and a confidence split cannot be combined with another signal into a
decision object, so the synthesis layer would have nothing to build on.

`related_positions`/`related_watchlist` are explicitly OPTIONAL tags, never
a filter: see README, "Posities zijn een signaal-attribuut, nooit de
paginastructuur." A signal about something Paul doesn't own is exactly as
valid as one about something he does.

`capital_view` used to live here, one per Signal (and one per Synthesis).
Paul: "you can't just keep repeating to wait... make it a separate line."
A recap with 12 signals showed 12 near-identical "wacht" verdicts -- each
individually honest, numbing in aggregate. It moved to
kompas/core/capital_call.py as ONE answer per cycle instead -- see that
module for why. CapitalView (the action/reasoning/trigger shape) stays
here since capital_call.py still uses it; it just no longer lives on a
Signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SIGNAL_CONFIDENCE_LEVELS = ("speculatief", "voorlopig", "hoog")

# Paul's framing: "if I had an uncommitted EUR 100 today, would THIS signal
# move it?" -- deliberately marginal-money language, never "what should I do
# with my actual position." nieuwe_positie = a name not currently held or
# watched at all; verhoog_bestaand = adds conviction to something already
# HELD (a real position, not just a watchlist name); wacht = real signal,
# not (yet) actionable. See kompas/core/capital_call.py.
CAPITAL_VIEW_ACTIONS = ("nieuwe_positie", "verhoog_bestaand", "wacht")


@dataclass(frozen=True)
class CapitalView:
    """The marginal-euro judgment shape: action/reasoning/trigger.

    "wacht" without a `trigger` is unfalsifiable -- it is always "correct"
    because nothing was ever claimed. Paul caught this directly: it lets
    the specialist avoid ever being wrong by never actually saying
    anything. `trigger` forces every action, "wacht" included, to name the
    concrete condition that would change it -- a real trend/price/event to
    watch for, not "not sure yet." Used by kompas/core/capital_call.py,
    once per cycle -- not an attribute of an individual Signal any more.
    """

    action: str  # one of CAPITAL_VIEW_ACTIONS
    reasoning: str  # the "because of this and that" -- required, non-empty
    trigger: str  # what would change this stance -- required, non-empty


@dataclass(frozen=True)
class Signal:
    role: str  # e.g. "Trend viewers", "Sector specialist – Uranium/Nucleair"
    subject: str  # the name or sector this signal is about
    text: str
    source: str  # citable: a specific outlet/document, never a bare category
    source_tier: str  # e.g. "tier 1", "tier 2"
    magnitude: str  # a sized claim, never a bare qualifier without a number
    timeframe_horizon: str  # when this should become visible
    data_confidence: str  # is the underlying figure correctly computed
    signal_confidence: str  # speculatief / voorlopig / hoog — see SIGNAL_CONFIDENCE_LEVELS
    observed_at: str  # RFC3339
    chart_timeframe: str | None = None  # required only for technical signals
    related_positions: list[str] = field(default_factory=list)
    related_watchlist: list[str] = field(default_factory=list)
    # An editorial call, not a mechanical diff of confidence levels: does
    # THIS signal genuinely contradict another already-published one on the
    # same subject (e.g. technical bearish vs. a sector tailwind)? Set by
    # whoever writes the signal, after reading both texts. None = no known
    # conflict. See kompas/pijler_a/spotlight.py for why this isn't inferred.
    conflict_note: str | None = None
    # Recap lifecycle, not a quality judgment: is this story still live?
    # Paul: "drop items when not relevant... only when the story is still
    # relevant keep it, otherwise move on. it's a daily recap." A signal is
    # never deleted (see README materiality-bar section for why the DB stays
    # an honest record) -- it just stops being shown once its own story has
    # concluded, been superseded, or lost the relevance it had when written.
    # Default True: a signal starts relevant and is closed explicitly, never
    # implicitly by age alone.
    relevant: bool = True
    closed_reason: str | None = None  # required once relevant=False -- why it no longer belongs in the recap


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


_CATEGORY_ONLY_SOURCES = {
    "sectorpers",
    "beleidsnieuws",
    "financiële pers",
    "financiele pers",
    "tier 1",
    "tier 2",
    "aggregator",
    "marktnieuws",
}


def validate_signal(signal: Signal, *, is_technical: bool = False) -> ValidationResult:
    """The hard publication gate for Poort 1 — see README, Poort 1.

    Does not decide whether a signal is CORRECT, only whether it carries
    enough structure for the synthesis layer to combine it with another
    one. A signal that fails this never gets published or written.
    """
    errors: list[str] = []

    if not signal.source.strip():
        errors.append("bron ontbreekt")
    elif signal.source.strip().lower() in _CATEGORY_ONLY_SOURCES:
        errors.append(f"bron {signal.source!r} is een categorie, geen citeerbare bron")

    if not signal.source_tier.strip():
        errors.append("brontier ontbreekt")

    if not signal.magnitude.strip():
        errors.append("omvang ontbreekt")

    if not signal.timeframe_horizon.strip():
        errors.append("tijdshorizon ontbreekt")

    if not signal.data_confidence.strip():
        errors.append("databetrouwbaarheid ontbreekt")

    sc = signal.signal_confidence.strip().lower()
    if not sc:
        errors.append("signaalbetrouwbaarheid ontbreekt")
    elif sc not in SIGNAL_CONFIDENCE_LEVELS:
        errors.append(
            f"signaalbetrouwbaarheid {signal.signal_confidence!r} is geen van "
            f"{SIGNAL_CONFIDENCE_LEVELS}"
        )

    if is_technical and not (signal.chart_timeframe or "").strip():
        errors.append("timeframe ontbreekt (verplicht voor technische signalen)")

    if not signal.relevant and not (signal.closed_reason or "").strip():
        errors.append(
            "closed_reason ontbreekt -- een niet langer relevant signaal moet zeggen "
            "waarom het verhaal is afgerond of achterhaald, anders is 'niet relevant' "
            "zelf net zo goedkoop als een ongefundeerde 'wacht' was"
        )

    return ValidationResult(ok=not errors, errors=errors)
