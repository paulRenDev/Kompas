"""Pijler A  Orchestratie van de complete signaalcyclus.

Deze module coördineert:
1. Het scannen van alle bronnen voor alle rollen
2. De signaalversheid-check (geen herhaling zonder wijziging)
3. De validatie van signalen
4. Het bouwen van write-payloads voor Poort 3 (Geheugen/opslag)

De cyclus draait op de twee dagelijkse verversmomenten (09:00 en 18:00 CEST),
gelijktijdig voor alle rollen, zodat de synthese-laag altijd met volledige,
gelijktijdige input werkt.

Belangrijke principes:
- Elke rol draait onafhankelijk
- Signaalversheid is een HARDE publicatievoorwaarde
- Conflicten tussen rollen worden zichtbaar gemaakt, nooit gemiddeld
- Alleen signalen die voldoen aan het Poort 1-schema worden gepubliceerd
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from kompas.core.signal import Signal, validate_signal
from kompas.db.kompas_db import signal_event_doc
from kompas.pijler_a.freshness import find_prior_signals
from kompas.pijler_a.scanner import Scanner, SignalCandidate
from kompas.pijler_a.roles import FIXED_ROLES, SECTOR_SPECIALISTS, ALL_ROLES
from kompas.pijler_a.sources import get_all_sources, get_sources_for_role


@dataclass(frozen=True)
class RoleScanResult:
    """Resultaat van het scannen van een enkele rol."""
    
    role_name: str
    signals: list[Signal]
    invalid_candidates: list[SignalCandidate]
    scan_errors: list[str]
    scanned_at: str


@dataclass(frozen=True)
class FreshnessCheckResult:
    """Resultaat van de signaalversheid-check."""
    
    signal: Signal
    is_fresh: bool
    prior_signals: list[dict]
    reason: str  # "no_prior", "material_change", "suppressed"


@dataclass(frozen=True)
class PijlerACycleResult:
    """Resultaat van een complete Pijler A cyclus."""
    
    # Resultaten per rol
    role_results: dict[str, RoleScanResult] = field(default_factory=dict)
    
    # Alle valide, verse signalen die gepubliceerd mogen worden
    publishable_signals: list[Signal] = field(default_factory=list)
    
    # Signalversheid statistieken
    total_signals_scanned: int = 0
    total_signals_valid: int = 0
    total_signals_fresh: int = 0
    total_signals_suppressed: int = 0
    
    # Write payloads voor Poort 3
    write_payloads: list[dict] = field(default_factory=list)
    
    # Tijdstempel
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Fouten
    errors: list[str] = field(default_factory=list)


class FreshnessChecker:
    """Voert de signaalversheid-check uit.
    
    Deze check is een HARDE publicatievoorwaarde: een signaal dat al
    eerder is gepubliceerd zonder materiële wijziging wordt onderdrukt.
    """
    
    @staticmethod
    def check_signal_freshness(
        signal: Signal,
        existing_events: list[dict],
    ) -> FreshnessCheckResult:
        """Controleert of een signaal vers is.
        
        Args:
            signal: Het nieuwe signaal
            existing_events: Lijst van bestaande events uit de database
            
        Returns:
            FreshnessCheckResult met de uitkomst
        """
        # Zoek naar eerdere signalen voor hetzelfde onderwerp
        prior_signals = find_prior_signals(
            existing_events,
            signal.subject,
            role=signal.role,
        )
        
        # Als er geen eerdere signalen zijn, is het vers
        if not prior_signals:
            return FreshnessCheckResult(
                signal=signal,
                is_fresh=True,
                prior_signals=prior_signals,
                reason="no_prior",
            )
        
        # Controleer of er een materiële wijziging is
        # Voor nu: we gaan uit van "vers" als er eerdere signalen zijn
        # In een echte implementatie zou hier gekeken worden naar:
        # - Nieuwe cijfers in het signaal
        # - Technisch niveau gebroken
        # - Nieuwe sectordata
        # - Andere materiële wijzigingen
        
        # Voor deze baseline implementatie: onderdruk herhaling
        # Dit is conservatief maar veilig
        return FreshnessCheckResult(
            signal=signal,
            is_fresh=False,
            prior_signals=prior_signals,
            reason="suppressed (herhaling zonder materiële wijziging)",
        )


class PijlerACycle:
    """Hoofdklasse voor het uitvoeren van een Pijler A cyclus.
    
    Deze klasse coördineert het complete proces:
    1. Scan alle bronnen voor alle rollen
    2. Valideer de signalen
    3. Voer signaalversheid-check uit
    4. Bouw write payloads voor valide, verse signalen
    """
    
    def __init__(self):
        self.scanner = Scanner()
        self.freshness_checker = FreshnessChecker()
    
    def run_role_cycle(self, role_name: str) -> RoleScanResult:
        """Voert een cyclus uit voor een enkele rol.
        
        Args:
            role_name: De naam van de rol (bv. "Stock watchers")
            
        Returns:
            RoleScanResult met de resultaten
        """
        scan_errors = []
        candidates = []
        
        try:
            # Scan de rol
            if role_name in [r.name for r in FIXED_ROLES]:
                candidates = self.scanner.scan_role(role_name)
            else:
                # Check of het een sector specialist is
                for specialist in SECTOR_SPECIALISTS:
                    if specialist.full_name == role_name:
                        candidates = self.scanner.scan_sector_specialist(specialist.sector)
                        break
        except Exception as e:
            scan_errors.append(f"Fout bij scannen van {role_name}: {str(e)}")
        
        # Valideer de kandidaten
        valid_signals, invalid_candidates = self.scanner.validate_candidates(candidates)
        
        return RoleScanResult(
            role_name=role_name,
            signals=valid_signals,
            invalid_candidates=invalid_candidates,
            scan_errors=scan_errors,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )
    
    def run_full_cycle(
        self,
        existing_events: list[dict] | None = None,
    ) -> PijlerACycleResult:
        """Voert een complete Pijler A cyclus uit voor alle rollen.
        
        Args:
            existing_events: Lijst van bestaande events uit de database
                           (voor signaalversheid-check). Als None, wordt
                           aangenomen dat er geen eerdere events zijn.
            
        Returns:
            PijlerACycleResult met alle resultaten
        """
        if existing_events is None:
            existing_events = []
        
        role_results = {}
        publishable_signals = []
        total_stats = {
            'scanned': 0,
            'valid': 0,
            'fresh': 0,
            'suppressed': 0,
        }
        errors = []
        write_payloads = []
        
        # Scan alle rollen
        all_roles = [r.name for r in FIXED_ROLES] + [s.full_name for s in SECTOR_SPECIALISTS]
        
        for role_name in all_roles:
            try:
                result = self.run_role_cycle(role_name)
                role_results[role_name] = result
                
                total_stats['scanned'] += len(result.signals) + len(result.invalid_candidates)
                total_stats['valid'] += len(result.signals)
                
                # Voer signaalversheid-check uit voor valide signalen
                for signal in result.signals:
                    freshness_result = self.freshness_checker.check_signal_freshness(
                        signal,
                        existing_events,
                    )
                    
                    if freshness_result.is_fresh:
                        publishable_signals.append(signal)
                        total_stats['fresh'] += 1
                        
                        # Bouw write payload
                        try:
                            is_technical = signal.role == "Technical stock watchers"
                            payload = signal_event_doc(signal, is_technical=is_technical)
                            write_payloads.append(payload)
                        except ValueError as e:
                            errors.append(f"Fout bij bouwen payload voor signaal {signal.subject}: {str(e)}")
                    else:
                        total_stats['suppressed'] += 1
                        
            except Exception as e:
                errors.append(f"Fout bij verwerken van rol {role_name}: {str(e)}")
        
        return PijlerACycleResult(
            role_results=role_results,
            publishable_signals=publishable_signals,
            total_signals_scanned=total_stats['scanned'],
            total_signals_valid=total_stats['valid'],
            total_signals_fresh=total_stats['fresh'],
            total_signals_suppressed=total_stats['suppressed'],
            write_payloads=write_payloads,
            errors=errors,
        )


def run_pijler_a_cycle(
    existing_events: list[dict] | None = None,
) -> PijlerACycleResult:
    """Convenience functie om een complete Pijler A cyclus uit te voeren.
    
    Args:
        existing_events: Lijst van bestaande events uit de database
        
    Returns:
        PijlerACycleResult met alle resultaten
    """
    cycle = PijlerACycle()
    return cycle.run_full_cycle(existing_events=existing_events)
