"""The AI-bubble monitor -- six fixed indicators, checked every evening.

Paul, 9/10/2026, after Ray Dalio called AI "a classic bubble" nearing its
bursting point (Bloomberg, 7/10): "Houden jullie actief bubbel breek
signalen bij? Ik zou niet weten wat te monitoren hiervoor maar jullie vast
wel. [...] Het komt er op aan om de signalen tijdig te zijn."

Why a fixed set with written thresholds instead of "the team keeps an eye
on it": a bubble never announces itself, and a monitor whose criteria move
with the mood is a story, not a monitor. The indicators follow Dalio's own
mechanism (debt-financed AI capex meets rising rates, then wealth has to be
turned into money) plus the classic late-bubble tells (narrowing
leadership, record leverage). Each status change needs a sourced fact --
"oranje" because it feels frothy is not allowed.

Honest limits, stated on purpose: this is checked once a day, not live; it
raises the odds of seeing a break coming, it does not time the top; and
Dalio himself has warned since January 2026 while markets kept rising, so
"opletten" can last months. No reading here is ever a sell order -- what
Paul does with it is his decision.
"""

from __future__ import annotations

from dataclasses import dataclass

STATUSES = ("groen", "oranje", "rood", "onbekend")

# key -> (name, what we watch, when it turns orange, when it turns red)
INDICATORS: dict[str, tuple[str, str, str, str]] = {
    "rente": (
        "Rente",
        "Amerikaanse 10-jaarsrente: Dalio's trigger, want de AI-uitbouw wordt steeds meer met schuld betaald.",
        "boven 4,5% of duidelijk stijgend",
        "boven 5%, of +0,5 procentpunt op drie maanden",
    ),
    "krediet": (
        "Krediet voor AI",
        "Rentevoet (spreads) op obligaties van Microsoft, Alphabet, Amazon, Meta, Oracle en AI-datacenters, en of hun grote leningen nog vlot geplaatst raken.",
        "hun spreads lopen sneller op dan die van de brede bedrijfsobligatiemarkt",
        "brede high-yield spreads +1 procentpunt op een maand, of een grote AI-lening die niet geplaatst raakt",
    ),
    "capex": (
        "Investeringen",
        "Wat de vier grote techbedrijven bij hun kwartaalcijfers zeggen over hun AI-investeringen voor dit en volgend jaar.",
        "één van de vier remt af of spreekt van een pauze",
        "twee of meer verlagen hun investeringsplannen",
    ),
    "ai_omzet": (
        "AI-omzet en chips",
        "Verdient AI het geld terug: omzet van OpenAI, Anthropic en de clouddiensten, cijfers van Nvidia en TSMC, en de chipsectorindex (SOX).",
        "een grote AI-speler stelt teleur en chips verkopen daarop",
        "herhaalde tegenvallers en de SOX zakt onder zijn 200-dagengemiddelde",
    ),
    "breedte": (
        "Breedte",
        "Hoeveel van de beurs nog meedoet: de top 10 tegenover de rest (S&P 500 gelijk gewogen tegenover gewogen naar grootte) en hoe ver de Nasdaq-100 onder zijn top staat.",
        "de concentratie neemt toe (gelijk gewogen blijft meer dan 3 procentpunt per maand achter)",
        "de Nasdaq-100 staat meer dan 10% onder zijn top",
    ),
    "hefboom": (
        "Hefboom en cash-out",
        "Geleend geld op de beurs (FINRA margin debt), beursgangen en grote verkopen door insiders: Dalio's 'vermogen omzetten in geld'.",
        "margin debt op of net onder een record, of een golf grote beursgangen en insiderverkopen",
        "margin debt meer dan 10% onder zijn record (gedwongen verkopen), of een mislukte grote beursgang",
    ),
}


@dataclass(frozen=True)
class IndicatorReading:
    key: str
    status: str  # one of STATUSES
    evidence: str  # what the team found, plain Dutch, with numbers
    source: str  # where it comes from; required unless status is "onbekend"


@dataclass(frozen=True)
class BubbleReading:
    readings: list[IndicatorReading]
    note: str  # Vera: what changed since the last reading, in one or two sentences
    observed_at: str  # RFC3339


@dataclass(frozen=True)
class BubbleValidationResult:
    ok: bool
    errors: list[str]


def level(reading: BubbleReading) -> str:
    """rustig / opletten / alarm -- one fixed rule, so the headline can't
    drift with the mood: alarm at three reds, opletten at one red or three
    oranges."""
    reds = sum(r.status == "rood" for r in reading.readings)
    oranges = sum(r.status == "oranje" for r in reading.readings)
    if reds >= 3:
        return "alarm"
    if reds >= 1 or oranges >= 3:
        return "opletten"
    return "rustig"


def validate_bubble_reading(reading: BubbleReading) -> BubbleValidationResult:
    errors: list[str] = []
    keys = [r.key for r in reading.readings]
    missing = [k for k in INDICATORS if k not in keys]
    if missing:
        errors.append(f"indicatoren ontbreken: {missing}")
    unknown = [k for k in keys if k not in INDICATORS]
    if unknown:
        errors.append(f"onbekende indicatoren: {unknown}")
    if len(set(keys)) != len(keys):
        errors.append("een indicator staat er twee keer in")
    for r in reading.readings:
        if r.status not in STATUSES:
            errors.append(f"{r.key}: status {r.status!r} is geen van {STATUSES}")
        if not r.evidence.strip():
            errors.append(f"{r.key}: evidence ontbreekt")
        if r.status != "onbekend" and not r.source.strip():
            errors.append(f"{r.key}: een status zonder bron is een gevoel, geen signaal")
    if not reading.note.strip():
        errors.append("note ontbreekt")
    if not reading.observed_at.strip():
        errors.append("observed_at ontbreekt")
    return BubbleValidationResult(ok=not errors, errors=errors)
