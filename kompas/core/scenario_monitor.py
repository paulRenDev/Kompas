"""The macro-scenario monitor -- five risk scenarios, checked every evening.

Paul, 12/10/2026, after the team mapped what US rate risk and the
geopolitical mess could do to his portfolio: "nemen jullie deze afweging mee
in jullie dagelijkse bespreking? ik wil niet te risico avers worden maar we
moeten de signalen wel tijdig opmerken."

Two halves of one instruction, both encoded here:
- notice in time: each scenario has written thresholds for "stijgend" and
  "acuut", checked against sourced facts every evening (like the bubble
  monitor -- a status changes only on a fact, never on a mood);
- don't turn risk-averse: insurance is capped. Outside an "acuut" scenario
  or a bubble alarm, hedges (gold, a cash reserve) stay within HEDGE_CAP of
  the portfolio, and a "stijgend" status is information, not a reason to
  buy more insurance. The free-money call keeps hunting opportunities unless a
  scenario is acuut.
"""

from __future__ import annotations

from dataclasses import dataclass

STATUSES = ("laag", "stijgend", "acuut", "onbekend")

# Gold and a cash reserve together, as a share of the portfolio, outside
# acuut/alarm. Above it the team is buying peace of mind, not return.
HEDGE_CAP = 0.15
HEDGE_TICKERS = ("GOLD",)  # Amundi Physical Gold ETC on Euronext Paris

# key -> (name, what we watch, stijgend when, acuut when, what it does to Paul's portfolio)
SCENARIOS: dict[str, tuple[str, str, str, str, str]] = {
    "rente_inflatie": (
        "Rente door inflatie en olie",
        "Amerikaanse 10-jaarsrente, de kans op een Fed-verhoging, ECB-beslissingen en de inflatie in VS en eurozone.",
        "de rente of de inflatie loopt verder op, of een centrale bank verhoogt",
        "10-jaarsrente slot boven 5,5%, of een renteverhoging die de markt niet verwachtte",
        "groei-aandelen in IWDA en de rentegevoelige thema's (INRE, NUCL) dalen; een sterkere dollar buffert je Amerikaanse posities",
    ),
    "vertrouwen_vs": (
        "Vertrouwen in Amerikaanse schuld",
        "De termijnpremie op Amerikaanse staatsobligaties, veilingen van Amerikaans staatspapier, en of rente en dollar samen of tegengesteld bewegen.",
        "de termijnpremie loopt op of een veiling valt tegen",
        "op vijf beursdagen stijgt de 10-jaarsrente meer dan 0,2 procentpunt terwijl de dollar meer dan 2% verliest (obligaties en dollar dalen samen)",
        "Amerikaanse aandelen én de dollar dalen: als eurobelegger verlies je twee keer; goud is de buffer",
    ),
    "olie_geopolitiek": (
        "Olie en geopolitiek",
        "Brent, de Straat van Hormuz, aanvallen op olie-infrastructuur en scheepvaart in de Golf en de Rode Zee, Rusland/Oekraïne.",
        "Brent boven USD 100 of een nieuwe aanval op olie- of transportinfrastructuur",
        "Brent slot boven USD 115, of schade aan Golf-olie-installaties of scheepvaart buiten Hormuz",
        "meer inflatie en dus meer rente; energie en waarde (IWVL) houden beter stand dan groei",
    ),
    "groeischok": (
        "Groeischok of AI-barst",
        "De AI-bubbelmonitor, de S&P 500 tegenover zijn top, en of de rente hard daalt (vlucht naar veiligheid).",
        "de bubbelmonitor staat op opletten en de beurs zakt meer dan 5% onder zijn top",
        "de bubbelmonitor staat op alarm, of de S&P 500 staat meer dan 10% onder zijn top terwijl de 10-jaarsrente op een maand meer dan 0,4 procentpunt daalt",
        "groei en thema's dalen het hardst; wie cash heeft, kan goedkoop bijkopen; goud en defensief (HLTW, COSW) houden beter stand",
    ),
    # Added 19/10/2026, when riots in France pushed the OAT-Bund spread back
    # towards its October peak: the other four look at the US, while Paul
    # lives, saves and pays tax in the eurozone.
    "eurozone_schuld": (
        "Schuldstress in de eurozone",
        "Het renteverschil tussen Franse en Duitse 10-jaarsrente (OAT-Bund), het Belgisch-Duitse verschil, de euro, en of de ECB moet ingrijpen.",
        "het OAT-Bund-verschil boven 120 basispunten, of een Franse begroting die vastloopt",
        "OAT-Bund-verschil slot boven 180 basispunten, of de ECB zet haar noodinstrument (TPI) in voor een land",
        "je beleggingen zitten nauwelijks in Frankrijk: een Parijse notering (NUCL, HLTW, COSW, INRE, GOLD) is een beursplaats, geen Frans risico; een zwakkere euro maakt je dollarposities en goud in euro meer waard; Europese banken en de euro dalen het hardst",
    ),
}


@dataclass(frozen=True)
class ScenarioReading:
    key: str
    status: str
    evidence: str
    source: str  # required unless status is "onbekend"


@dataclass(frozen=True)
class ScenarioSnapshot:
    readings: list[ScenarioReading]
    note: str
    observed_at: str


@dataclass(frozen=True)
class ScenarioValidationResult:
    ok: bool
    errors: list[str]


def any_acute(snapshot: ScenarioSnapshot) -> bool:
    return any(r.status == "acuut" for r in snapshot.readings)


def hedge_share(value_by_ticker: dict[str, float], cash_reserve_eur: float = 0.0) -> float:
    """Share of the portfolio in insurance (gold + a cash reserve)."""
    total = sum(value_by_ticker.values()) + cash_reserve_eur
    hedged = sum(value_by_ticker.get(t, 0.0) for t in HEDGE_TICKERS) + cash_reserve_eur
    return hedged / total if total else 0.0


def hedge_room_eur(value_by_ticker: dict[str, float], cash_reserve_eur: float = 0.0) -> float:
    """How much more insurance fits under HEDGE_CAP (0 when full)."""
    total = sum(value_by_ticker.values()) + cash_reserve_eur
    hedged = sum(value_by_ticker.get(t, 0.0) for t in HEDGE_TICKERS) + cash_reserve_eur
    # extra x keeps (hedged + x) / (total + x) <= cap
    room = (HEDGE_CAP * total - hedged) / (1 - HEDGE_CAP)
    return round(max(room, 0.0), 2)


def validate_scenarios(snapshot: ScenarioSnapshot) -> ScenarioValidationResult:
    errors: list[str] = []
    keys = [r.key for r in snapshot.readings]
    missing = [k for k in SCENARIOS if k not in keys]
    if missing:
        errors.append(f"scenario's ontbreken: {missing}")
    unknown = [k for k in keys if k not in SCENARIOS]
    if unknown:
        errors.append(f"onbekende scenario's: {unknown}")
    if len(set(keys)) != len(keys):
        errors.append("een scenario staat er twee keer in")
    for r in snapshot.readings:
        if r.status not in STATUSES:
            errors.append(f"{r.key}: status {r.status!r} is geen van {STATUSES}")
        if not r.evidence.strip():
            errors.append(f"{r.key}: evidence ontbreekt")
        if r.status != "onbekend" and not r.source.strip():
            errors.append(f"{r.key}: een status zonder bron is een gevoel, geen signaal")
    if not snapshot.note.strip():
        errors.append("note ontbreekt")
    if not snapshot.observed_at.strip():
        errors.append("observed_at ontbreekt")
    return ScenarioValidationResult(ok=not errors, errors=errors)
