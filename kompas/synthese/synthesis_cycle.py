"""Synthese-laag - Synthese Cyclus.

Orchestreert de complete synthese cyclus die Pijler A en Pijler B combineert.

De synthese cyclus:
1. Ontvangt resultaten van Pijler A (signalen) en Pijler B (portefeuille)
2. Valideert de reconciliatie van Pijler B
3. Bouwt de capital map
4. Genereert decision objects
5. Retourneert een SynthesisResult met alle output

Belangrijke principes:
- Geen synthese zonder succesvolle reconciliatie
- Alle signalen moeten voldoen aan Poort 1 schema
- Conflicten worden zichtbaar gemaakt, niet gemiddeld
- De cyclus is idempotent: zelfde input = zelfde output
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from kompas.core.schema import PortfolioSnapshot, ReconciliationResult
from kompas.core.signal import Signal
from kompas.pijler_a.cycle import PijlerACycleResult
from kompas.pijler_b.cycle import CycleResult
from kompas.synthese.capital_map import CapitalMap, CapitalMapBuilder
from kompas.synthese.decision_objects import DecisionObjectCollection, DecisionObjectBuilder


@dataclass
class SynthesisResult:
    """Resultaat van een synthese cyclus."""
    
    # Metadata
    id: str
    cycle_id: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Resultaten
    capital_map: Optional[CapitalMap] = None
    decision_objects: Optional[DecisionObjectCollection] = None
    
    # Input data (voor audit)
    pijler_a_result: Optional[PijlerACycleResult] = None
    pijler_b_result: Optional[CycleResult] = None
    
    # Errors
    errors: list[str] = field(default_factory=list)
    
    # Statistieken
    stats: dict = field(default_factory=dict)


@dataclass
class SynthesisCycle:
    """Hoofdklasse voor de synthese cyclus."""
    
    cycle_id: str
    pijler_a_result: PijlerACycleResult
    pijler_b_result: CycleResult
    
    def __post_init__(self):
        """Valideer input bij initialisatie."""
        if not self.pijler_a_result:
            raise ValueError("Pijler A result is required")
        if not self.pijler_b_result:
            raise ValueError("Pijler B result is required")
    
    def run(self) -> SynthesisResult:
        """Voert de complete synthese cyclus uit.
        
        Returns:
            SynthesisResult met capital map, decision objects en statistieken
        """
        errors = []
        
        # Stap 1: Valideer Pijler B reconciliatie
        if not self.pijler_b_result.reconciliation.ok:
            errors.append(
                f"Pijler B reconciliatie mislukt: {self.pijler_b_result.reconciliation.diffs}"
            )
            return SynthesisResult(
                id=f"synth_{self.cycle_id}",
                cycle_id=self.cycle_id,
                pijler_a_result=self.pijler_a_result,
                pijler_b_result=self.pijler_b_result,
                errors=errors,
            )
        
        # Stap 2: Bouw capital map
        try:
            capital_map = CapitalMapBuilder.build_capital_map(
                signals=self.pijler_a_result.publishable_signals,
                portfolio=self.pijler_b_result.snapshot,
                cycle_id=self.cycle_id,
            )
        except Exception as e:
            errors.append(f"Fout bij bouwen capital map: {str(e)}")
            return SynthesisResult(
                id=f"synth_{self.cycle_id}",
                cycle_id=self.cycle_id,
                pijler_a_result=self.pijler_a_result,
                pijler_b_result=self.pijler_b_result,
                errors=errors,
            )
        
        # Stap 3: Bouw decision objects
        try:
            decision_objects = DecisionObjectBuilder.build_decision_objects(
                capital_map=capital_map,
                portfolio=self.pijler_b_result.snapshot,
                cycle_id=self.cycle_id,
            )
        except Exception as e:
            errors.append(f"Fout bij bouwen decision objects: {str(e)}")
            return SynthesisResult(
                id=f"synth_{self.cycle_id}",
                cycle_id=self.cycle_id,
                capital_map=capital_map,
                pijler_a_result=self.pijler_a_result,
                pijler_b_result=self.pijler_b_result,
                errors=errors,
            )
        
        # Stap 4: Bouw statistieken
        stats = self._build_stats(capital_map, decision_objects)
        
        return SynthesisResult(
            id=f"synth_{self.cycle_id}",
            cycle_id=self.cycle_id,
            capital_map=capital_map,
            decision_objects=decision_objects,
            pijler_a_result=self.pijler_a_result,
            pijler_b_result=self.pijler_b_result,
            errors=errors,
            stats=stats,
        )
    
    def _build_stats(
        self,
        capital_map: CapitalMap,
        decision_objects: DecisionObjectCollection,
    ) -> dict:
        """Bouwt statistieken voor het synthese resultaat."""
        pijler_a = self.pijler_a_result
        pijler_b = self.pijler_b_result
        
        return {
            # Pijler A stats
            'pijler_a': {
                'total_signals_scanned': pijler_a.total_signals_scanned,
                'total_signals_valid': pijler_a.total_signals_valid,
                'total_signals_fresh': pijler_a.total_signals_fresh,
                'total_signals_suppressed': pijler_a.total_signals_suppressed,
                'publishable_signals': len(pijler_a.publishable_signals),
            },
            # Pijler B stats
            'pijler_b': {
                'reconciliation_ok': pijler_b.reconciliation.ok,
                'positions_count': len(pijler_b.snapshot.positions) if pijler_b.snapshot else 0,
                'watchlist_count': len(pijler_b.snapshot.watchlist) if pijler_b.snapshot else 0,
                'portfolio_value_eur': pijler_b.snapshot.summary.value_eur if pijler_b.snapshot else 0,
            },
            # Capital map stats
            'capital_map': capital_map.stats if capital_map else {},
            # Decision objects stats
            'decision_objects': decision_objects.stats if decision_objects else {},
            # Totaal
            'total': {
                'signals_processed': len(pijler_a.publishable_signals),
                'opportunities_created': len(capital_map.opportunities) if capital_map else 0,
                'decision_objects_created': len(decision_objects.decision_objects) if decision_objects else 0,
                'conflicts_detected': len(capital_map.conflicts) if capital_map else 0,
            },
        }


def run_synthesis_cycle(
    pijler_a_result: PijlerACycleResult,
    pijler_b_result: CycleResult,
    cycle_id: str = "",
) -> SynthesisResult:
    """Voert een complete synthese cyclus uit.
    
    Dit is de hoofd-functie voor het combineren van Pijler A en Pijler B resultaten.
    
    Args:
        pijler_a_result: Resultaat van Pijler A cyclus
        pijler_b_result: Resultaat van Pijler B cyclus
        cycle_id: Optionele ID voor deze cyclus
        
    Returns:
        SynthesisResult met alle output en statistieken
    """
    if not cycle_id:
        cycle_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    cycle = SynthesisCycle(
        cycle_id=cycle_id,
        pijler_a_result=pijler_a_result,
        pijler_b_result=pijler_b_result,
    )
    
    return cycle.run()
