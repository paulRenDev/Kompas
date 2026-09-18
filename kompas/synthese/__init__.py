"""Synthese-laag voor Kompas.

Combineert signalen van Pijler A met portefeuille/watchlist data van Pijler B
tot een capital map en decision objects.

Structuur:
- capital_map.py: Bouwt de capital map met opportunities en allocaties
- decision_objects.py: Genereert decision objects voor elke positie/watchlist
- synthesis_cycle.py: Orchestreert de complete synthese cyclus
"""

from kompas.synthese.capital_map import (
    CapitalMap,
    CapitalMapBuilder,
    Opportunity,
    OpportunityType,
    RiskLevel,
    CapitalAllocation,
    OpportunityBuilder,
)
from kompas.synthese.decision_objects import (
    DecisionObject,
    DecisionObjectCollection,
    DecisionObjectBuilder,
    ActionType,
    DecisionConfidence,
)
from kompas.synthese.synthesis_cycle import (
    SynthesisResult,
    SynthesisCycle,
    run_synthesis_cycle,
)

__all__ = [
    # capital_map
    'CapitalMap',
    'CapitalMapBuilder',
    'Opportunity',
    'OpportunityType',
    'RiskLevel',
    'CapitalAllocation',
    'OpportunityBuilder',
    # decision_objects
    'DecisionObject',
    'DecisionObjectCollection',
    'DecisionObjectBuilder',
    'ActionType',
    'DecisionConfidence',
    # synthesis_cycle
    'SynthesisResult',
    'SynthesisCycle',
    'run_synthesis_cycle',
]
