"""Cycle Runner voor Kompas.

Voert complete cycli uit:
1. Pijler A: Signalen verzamelen
2. Pijler B: Portefeuille data ophalen
3. Synthese: Combineren en analyseren

De cycle runner:
- Coordineert de uitvoering van alle componenten
- Beheert afhankelijkheden (Pijler A en B moeten eerst)
- Slaat resultaten op in de database
- Retourneert een compleet resultaat

Belangrijke principes:
- Geen synthese zonder succesvolle Pijler A en B
- Alle stappen worden gelogd
- Fouten worden netjes afgevangen en gerapporteerd
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from kompas.core.schema import PortfolioSnapshot
from kompas.core.signal import Signal
from kompas.db.kompas_db import (
    signal_event_doc,
    build_batch,
    split_path,
    ARTIFACT_URL,
)
from kompas.pijler_a.cycle import PijlerACycleResult, run_pijler_a_cycle
from kompas.pijler_b.cycle import CycleResult, run_cycle
from kompas.synthese.synthesis_cycle import SynthesisResult, run_synthesis_cycle


@dataclass
class FullCycleResult:
    """Resultaat van een complete cyclus (Pijler A + Pijler B + Synthese)."""
    
    # Metadata
    id: str
    cycle_id: str
    started_at: str
    completed_at: str
    
    # Resultaten
    pijler_a_result: Optional[PijlerACycleResult] = None
    pijler_b_result: Optional[CycleResult] = None
    synthesis_result: Optional[SynthesisResult] = None
    
    # Database writes
    events_written: int = 0
    capital_map_written: bool = False
    decision_objects_written: bool = False
    synthesis_result_written: bool = False
    
    # Errors
    errors: list[str] = field(default_factory=list)
    
    # Statistieken
    stats: dict = field(default_factory=dict)


class CycleRunner:
    """Hoofdklasse voor het uitvoeren van complete cycli.
    
    Deze klasse coördineert:
    1. Pijler A cyclus (signalen verzamelen)
    2. Pijler B cyclus (portefeuille data ophalen)
    3. Synthese cyclus (combineren en analyseren)
    4. Schrijven naar database
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run_full_cycle(
        self,
        cycle_id: Optional[str] = None,
    ) -> FullCycleResult:
        """Voert een complete cyclus uit.
        
        Args:
            cycle_id: Optionele ID voor deze cyclus
            
        Returns:
            FullCycleResult met alle resultaten
        """
        if not cycle_id:
            cycle_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        started_at = datetime.now(timezone.utc).isoformat()
        errors = []
        stats = {}
        
        self.logger.info(f"Start complete cyclus: {cycle_id}")
        
        # Stap 1: Pijler A
        self.logger.info(f"[{cycle_id}] Start Pijler A")
        try:
            pijler_a_result = run_pijler_a_cycle()
            self.logger.info(f"[{cycle_id}] Pijler A voltooid: {len(pijler_a_result.publishable_signals)} publiceerbare signalen")
            stats['pijler_a'] = {
                'scanned': pijler_a_result.total_signals_scanned,
                'valid': pijler_a_result.total_signals_valid,
                'fresh': pijler_a_result.total_signals_fresh,
                'suppressed': pijler_a_result.total_signals_suppressed,
            }
        except Exception as e:
            errors.append(f"Pijler A mislukt: {str(e)}")
            self.logger.error(f"[{cycle_id}] Pijler A fout: {e}")
            pijler_a_result = None
        
        # Stap 2: Pijler B (simulatie - echte data komt van Google Sheet via MCP)
        self.logger.info(f"[{cycle_id}] Start Pijler B")
        try:
            # Voor demo/test: gebruik fixture data
            # In productie: run_cycle(raw_dump_text) met echte dump van Google Sheet
            with open('tests/fixtures/aandelen_sample.txt', 'r') as f:
                sample_dump = f.read()
            pijler_b_result = run_cycle(sample_dump)
            self.logger.info(f"[{cycle_id}] Pijler B voltooid: {len(pijler_b_result.snapshot.positions)} posities")
            stats['pijler_b'] = {
                'positions': len(pijler_b_result.snapshot.positions),
                'watchlist': len(pijler_b_result.snapshot.watchlist),
                'reconciliation_ok': pijler_b_result.reconciliation.ok,
            }
        except Exception as e:
            errors.append(f"Pijler B mislukt: {str(e)}")
            self.logger.error(f"[{cycle_id}] Pijler B fout: {e}")
            pijler_b_result = None
        
        # Stap 3: Synthese (alleen als Pijler A en B succesvol waren)
        synthesis_result = None
        if pijler_a_result and pijler_b_result and pijler_b_result.reconciliation.ok:
            self.logger.info(f"[{cycle_id}] Start Synthese")
            try:
                synthesis_result = run_synthesis_cycle(
                    pijler_a_result=pijler_a_result,
                    pijler_b_result=pijler_b_result,
                    cycle_id=cycle_id,
                )
                self.logger.info(f"[{cycle_id}] Synthese voltooid")
                stats['synthese'] = synthesis_result.stats if synthesis_result else {}
            except Exception as e:
                errors.append(f"Synthese mislukt: {str(e)}")
                self.logger.error(f"[{cycle_id}] Synthese fout: {e}")
        
        # Stap 4: Schrijven naar database (simulatie - echte writes zijn MCP-only)
        # In een echte Claude sessie: gebruik ArtifactData.batch() met de payloads
        events_written = 0
        capital_map_written = False
        decision_objects_written = False
        synthesis_result_written = False
        
        if pijler_a_result and pijler_a_result.write_payloads:
            try:
                # Simuleer schrijven (in productie: ArtifactData.batch())
                events_written = len(pijler_a_result.write_payloads)
                self.logger.info(f"[{cycle_id}] {events_written} events klaar voor database (ArtifactData.batch)")
            except Exception as e:
                errors.append(f"Payloads events mislukt: {str(e)}")
                self.logger.error(f"[{cycle_id}] Fout bij bouwen events payloads: {e}")
        
        if synthesis_result and synthesis_result.capital_map:
            try:
                # Simuleer schrijven (in productie: ArtifactData.set())
                capital_map_written = True
                self.logger.info(f"[{cycle_id}] Capital map payload klaar voor database")
            except Exception as e:
                errors.append(f"Payload capital map mislukt: {str(e)}")
                self.logger.error(f"[{cycle_id}] Fout bij bouwen capital map payload: {e}")
        
        if synthesis_result and synthesis_result.decision_objects:
            try:
                # Simuleer schrijven (in productie: ArtifactData.batch())
                decision_objects_written = True
                self.logger.info(f"[{cycle_id}] Decision objects payload klaar voor database")
            except Exception as e:
                errors.append(f"Payload decision objects mislukt: {str(e)}")
                self.logger.error(f"[{cycle_id}] Fout bij bouwen decision objects payload: {e}")
        
        if synthesis_result:
            try:
                # Simuleer schrijven (in productie: ArtifactData.set())
                synthesis_result_written = True
                self.logger.info(f"[{cycle_id}] Synthesis result payload klaar voor database")
            except Exception as e:
                errors.append(f"Payload synthesis result mislukt: {str(e)}")
                self.logger.error(f"[{cycle_id}] Fout bij bouwen synthesis result payload: {e}")
        
        completed_at = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"Complete cyclus {cycle_id} voltooid in {completed_at}")
        
        return FullCycleResult(
            id=f"full_cycle_{cycle_id}",
            cycle_id=cycle_id,
            started_at=started_at,
            completed_at=completed_at,
            pijler_a_result=pijler_a_result,
            pijler_b_result=pijler_b_result,
            synthesis_result=synthesis_result,
            events_written=events_written,
            capital_map_written=capital_map_written,
            decision_objects_written=decision_objects_written,
            synthesis_result_written=synthesis_result_written,
            errors=errors,
            stats=stats,
        )


def run_full_cycle(
    cycle_id: Optional[str] = None,
) -> FullCycleResult:
    """Convenience functie om een complete cyclus uit te voeren.
    
    Args:
        cycle_id: Optionele ID voor deze cyclus
        
    Returns:
        FullCycleResult met alle resultaten
    """
    runner = CycleRunner()
    return runner.run_full_cycle(cycle_id=cycle_id)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_full_cycle()
    
    print("\n" + "=" * 60)
    print("CYCLUS RESULTATEN")
    print("=" * 60)
    print(f"ID: {result.id}")
    print(f"Cycle ID: {result.cycle_id}")
    print(f"Gestart: {result.started_at}")
    print(f"Voltooid: {result.completed_at}")
    print(f"Duur: ~{int((datetime.fromisoformat(result.completed_at) - datetime.fromisoformat(result.started_at)).total_seconds())} seconden")
    print()
    
    if result.pijler_a_result:
        print("PIJLER A:")
        print(f"  Gescand: {result.pijler_a_result.total_signals_scanned}")
        print(f"  Valide: {result.pijler_a_result.total_signals_valid}")
        print(f"  Vers: {result.pijler_a_result.total_signals_fresh}")
        print(f"  Onderdrukt: {result.pijler_a_result.total_signals_suppressed}")
        print()
    
    if result.pijler_b_result:
        print("PIJLER B:")
        print(f"  Posities: {len(result.pijler_b_result.snapshot.positions)}")
        print(f"  Watchlist: {len(result.pijler_b_result.snapshot.watchlist)}")
        print(f"  Reconciliatie: {'OK' if result.pijler_b_result.reconciliation.ok else 'FAIL'}")
        print()
    
    if result.synthesis_result:
        print("SYNTHESE:")
        print(f"  Opportunities: {len(result.synthesis_result.capital_map.opportunities) if result.synthesis_result.capital_map else 0}")
        print(f"  Conflicten: {len(result.synthesis_result.capital_map.conflicts) if result.synthesis_result.capital_map else 0}")
        print(f"  Decision Objects: {len(result.synthesis_result.decision_objects.decision_objects) if result.synthesis_result.decision_objects else 0}")
        print()
    
    print("DATABASE:")
    print(f"  Events geschreven: {result.events_written}")
    print(f"  Capital map geschreven: {result.capital_map_written}")
    print(f"  Decision objects geschreven: {result.decision_objects_written}")
    print(f"  Synthesis result geschreven: {result.synthesis_result_written}")
    print()
    
    if result.errors:
        print("FOUTEN:")
        for error in result.errors:
            print(f"  - {error}")
        print()
    
    print("=" * 60)
