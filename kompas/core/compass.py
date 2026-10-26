"""The Kompasroos -- where the team stands, per theme, in one picture.

Paul, 26/10/2026, after the redesign: "ik mis toch nog wat 'op het eerste
zicht' dingen [...] we moeten echt het verschil kunnen maken tov de
concurrentie" -- and, when the first idea turned out to track his own
prices: "ik wil mijn eigen koersen niet opvolgen ik wil geen kopie van de
bestaande excel". So this shows the one thing only Kompas has: the team's
judgment, and how it moves.

One reading per evening (`compass/{date}`): for each fixed THEME a stance
(positief / neutraal / voorzichtig), one plain sentence why, and where that
comes from (a monitor reading, a signal, a call). A stance changes only
when the reasoning changes, never with the mood of a day. The page draws
it as a compass rose with one needle per theme.
"""

from __future__ import annotations

from dataclasses import dataclass

STANCES = ("positief", "neutraal", "voorzichtig")

# key -> name; fixed, so the rose keeps its shape day after day.
THEMES: dict[str, str] = {
    "kern": "Wereldwijde kern",
    "ai_chips": "AI en chips",
    "energie_netten": "Energie en netten",
    "waarde_defensief": "Waarde en defensief",
    "europa": "Europa",
    "verzekering": "Verzekering (goud, cash)",
}


@dataclass(frozen=True)
class ThemeStance:
    key: str
    stance: str  # one of STANCES
    reason: str  # one plain sentence, the why
    source: str  # the team doc or signal it rests on


@dataclass(frozen=True)
class CompassReading:
    stances: list[ThemeStance]
    note: str  # Vera: what moved since the last reading, one sentence
    observed_at: str  # RFC3339


@dataclass(frozen=True)
class CompassValidationResult:
    ok: bool
    errors: list[str]


def validate_compass(reading: CompassReading) -> CompassValidationResult:
    errors: list[str] = []
    keys = [s.key for s in reading.stances]
    missing = [k for k in THEMES if k not in keys]
    if missing:
        errors.append(f"thema's ontbreken: {missing}")
    unknown = [k for k in keys if k not in THEMES]
    if unknown:
        errors.append(f"onbekende thema's: {unknown}")
    if len(set(keys)) != len(keys):
        errors.append("een thema staat er twee keer in")
    for s in reading.stances:
        if s.stance not in STANCES:
            errors.append(f"{s.key}: stand {s.stance!r} is geen van {STANCES}")
        if not s.reason.strip():
            errors.append(f"{s.key}: zonder reden is een stand een gevoel")
        if not s.source.strip():
            errors.append(f"{s.key}: waar komt deze stand vandaan?")
    if not reading.note.strip():
        errors.append("note ontbreekt")
    if not reading.observed_at.strip():
        errors.append("observed_at ontbreekt")
    return CompassValidationResult(ok=not errors, errors=errors)
