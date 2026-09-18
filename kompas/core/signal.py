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

    return ValidationResult(ok=not errors, errors=errors)
