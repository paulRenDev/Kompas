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
"""

from __future__ import annotations

from dataclasses import dataclass, field

SIGNAL_CONFIDENCE_LEVELS = ("speculatief", "voorlopig", "hoog")

# Paul's framing: "if I had an uncommitted EUR 100 today, would THIS signal
# move it?" -- deliberately marginal-money language, never "what should I do
# with my actual position." nieuwe_positie = a name not currently held or
# watched at all; verhoog_bestaand = adds conviction to something already
# HELD (a real position, not just a watchlist name -- see validate_signal);
# wacht = real signal, not (yet) actionable.
CAPITAL_VIEW_ACTIONS = ("nieuwe_positie", "verhoog_bestaand", "wacht")


@dataclass(frozen=True)
class CapitalView:
    """One specialist's marginal-euro judgment on their own signal.

    An attribute of the signal, same standing as related_positions/
    related_watchlist -- never a separate, position-keyed page section.
    Optional: a broad macro signal with no single-name angle can honestly
    have none, rather than a forced opinion.
    """

    action: str  # one of CAPITAL_VIEW_ACTIONS
    reasoning: str  # the "because of this and that" -- required, non-empty


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
    capital_view: CapitalView | None = None


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

    if signal.capital_view is not None:
        cv = signal.capital_view
        if cv.action not in CAPITAL_VIEW_ACTIONS:
            errors.append(
                f"capital_view.action {cv.action!r} is geen van {CAPITAL_VIEW_ACTIONS}"
            )
        if not cv.reasoning.strip():
            errors.append("capital_view.reasoning ontbreekt")
        if cv.action == "verhoog_bestaand" and not signal.related_positions:
            errors.append(
                "capital_view 'verhoog_bestaand' vereist een echte related_positions-tag "
                "-- je kan geen bestaande positie vergroten die er niet is (een "
                "watchlist-naam is geen positie)"
            )

    return ValidationResult(ok=not errors, errors=errors)
