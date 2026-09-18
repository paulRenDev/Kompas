"""Pijler A  Analistrollen definitie.

Elke rol heeft een duidelijke verantwoordelijkheid en werkwijze.
Zie README, "Pijler A  drie vaste rollen + een sector-specialistenpool" voor
detailed uitleg.

De vier rollen:
1. Stock watchers: "Wat gebeurt er met deze naam?"
2. Trend viewers: "Structurele trend of ruis?"
3. Technical stock watchers: "Wat zegt de koers zelf?"
4. Sector specialists: Pool van smalle, diepe specialisten per sector

Elke rol levert signalen in het standaard Poort 1-formaat (Signal dataclass).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class AnalystRole:
    """Definieert een analistrol met zijn verantwoordelijkheid en werkwijze."""

    name: str
    description: str
    core_question: str
    output_type: str
    is_technical: bool = False
    
    # Sector specialisten hebben een dynamische pool
    is_pool: bool = False
    
    # Voor sector specialisten: de sector waar ze op focussen
    sector: str | None = None


# De drie vaste rollen
STOCK_WATCHERS = AnalystRole(
    name="Stock watchers",
    description="Volgt bedrijfsspecifiek nieuws per holding/watchlist-naam",
    core_question="Wat gebeurt er met deze naam?",
    output_type="Gebeurtenis + waarom relevant voor die naam",
    is_technical=False,
    is_pool=False,
)

TREND_VIEWERS = AnalystRole(
    name="Trend viewers",
    description="Analyseert macro-/beleidsnieuws",
    core_question="Structurele trend of ruis?",
    output_type="Trendbevestiging, -breuk of ruis, expliciet benoemd",
    is_technical=False,
    is_pool=False,
)

TECHNICAL_STOCK_WATCHERS = AnalystRole(
    name="Technical stock watchers",
    description="Analyseert koersactie, chartpatronen en momentum",
    core_question="Wat zegt de koers zelf?",
    output_type="Technisch niveau bereikt/gebroken, los van fundamentals",
    is_technical=True,
    is_pool=False,
)


@dataclass(frozen=True)
class SectorSpecialist:
    """Een sector-specialist is een specifieke instantie voor een sector.
    
    In tegenstelling tot de drie vaste rollen, is dit een pool waar
    instanties dynamisch aan toegevoegd/verwijderd kunnen worden.
    """

    sector: str
    
    @property
    def full_name(self) -> str:
        return f"Sector specialist  {self.sector}"


# Standaard sector specialisten pool (kan dynamisch uitgebreid worden)
# Gebaseerd op de portefeuille (ETF's) en watchlist
SECTOR_SPECIALISTS: list[SectorSpecialist] = [
    SectorSpecialist(sector="Halfgeleiders"),
    SectorSpecialist(sector="Defensie"),
    SectorSpecialist(sector="Uranium/Nucleair"),
    SectorSpecialist(sector="Datacenter-infra"),
    SectorSpecialist(sector="Energie"),
    SectorSpecialist(sector="Gezondheidszorg"),
    SectorSpecialist(sector="Consumentengoederen"),
    SectorSpecialist(sector="Edelmetalen"),
    SectorSpecialist(sector="Infrastructuur"),
]


# Alle vaste rollen (excl. sector specialisten pool)
FIXED_ROLES: list[AnalystRole] = [
    STOCK_WATCHERS,
    TREND_VIEWERS,
    TECHNICAL_STOCK_WATCHERS,
]


# Alle rollen (inclusief sector specialisten)
ALL_ROLES: list[AnalystRole | SectorSpecialist] = FIXED_ROLES + SECTOR_SPECIALISTS


def get_role_by_name(name: str) -> AnalystRole | SectorSpecialist | None:
    """Vind een rol op naam."""
    for role in ALL_ROLES:
        if hasattr(role, 'name') and role.name == name:
            return role
        if hasattr(role, 'full_name') and role.full_name == name:
            return role
    return None


def get_sector_specialist(sector: str) -> SectorSpecialist | None:
    """Vind een sector specialist voor een specifieke sector."""
    for specialist in SECTOR_SPECIALISTS:
        if specialist.sector.lower() == sector.lower():
            return specialist
    return None


def add_sector_specialist(sector: str) -> SectorSpecialist:
    """Voeg een nieuwe sector specialist toe aan de pool.
    
    Returns de nieuwe specialist. Deze wordt niet automatisch opgeslagen,
    maar kan worden gebruikt in de huidige cyclus.
    """
    specialist = SectorSpecialist(sector=sector)
    # Voeg toe aan de globale pool als deze nog niet bestaat
    if not any(s.sector.lower() == sector.lower() for s in SECTOR_SPECIALISTS):
        SECTOR_SPECIALISTS.append(specialist)
    return specialist
