"""Synthese-laag - Capital Map.

Bouwt een capital map die kansen tegen elkaar en tegen cash afweegt.

De capital map:
- Weegt alle actieve signalen af tegen de portefeuille
- Identificeert kansen en risico's
- Rangschikt deze op basis van omvang, tijdshorizon en betrouwbaarheid
- Houdt rekening met cash beschikbaarheid

Belangrijke principes:
- Alleen signalen die voldoen aan het Poort 1-schema worden meegenomen
- Conflicten tussen rollen worden zichtbaar gemaakt
- De capital map is een momentopname, geen voorspelling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from kompas.core.schema import Position, WatchlistEntry, PortfolioSnapshot
from kompas.core.signal import Signal


class OpportunityType(Enum):
    """Type kans in de capital map."""
    BUY = "buy"           # Koopkans
    SELL = "sell"         # Verkoopkans (winst nemen of verlies beperken)
    HOLD = "hold"         # Houden (geen actie)
    WATCH = "watch"       # Volgen (potentiele kans in de toekomst)
    HEDGE = "hedge"       # Afdekken (risico beperken)


class RiskLevel(Enum):
    """Risiconiveau."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Opportunity:
    """Een single kans of risico in de capital map."""
    
    # Identificatie
    id: str
    subject: str
    
    # Type en prioriteit
    opportunity_type: OpportunityType
    priority: int  # 1-10, hoger = belangrijker
    
    # Financiele data
    estimated_impact_eur: float = 0.0
    estimated_impact_pct: float = 0.0
    
    # Tijdshorizon
    timeframe_horizon: str = "onbekend"
    
    # Betrouwbaarheid
    confidence: str = "voorlopig"
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Gerelateerde items
    related_positions: list[str] = field(default_factory=list)
    related_watchlist: list[str] = field(default_factory=list)
    source_signals: list[str] = field(default_factory=list)  # IDs van bron-signalen
    
    # Actie
    recommended_action: str = ""
    action_threshold: float = 0.0  # Prijsniveau waar actie aanbevolen wordt
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    role_consensus: dict[str, str] = field(default_factory=dict)  # {rol: standpunt}
    conflict: bool = False


@dataclass
class CapitalAllocation:
    """Allocatie van capital over verschillende kansen."""
    
    # Huidige allocatie
    current_positions: dict[str, float] = field(default_factory=dict)  # {ticker: percentage}
    current_cash_pct: float = 0.0
    
    # Voorgestelde allocatie
    proposed_positions: dict[str, float] = field(default_factory=dict)
    proposed_cash_pct: float = 0.0
    
    # Wijzigingen
    changes: dict[str, float] = field(default_factory=dict)  # {ticker: percentage change}
    
    # Statistieken
    total_portfolio_value: float = 0.0
    total_risk_exposure: float = 0.0
    diversification_score: float = 0.0  # 0-100, hoger = beter gespreid


@dataclass
class CapitalMap:
    """De complete capital map."""
    
    # Metadata
    id: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cycle_id: str = ""
    
    # Input data
    portfolio_snapshot: Optional[PortfolioSnapshot] = None
    signals: list[Signal] = field(default_factory=list)
    
    # Opportunities
    opportunities: list[Opportunity] = field(default_factory=list)
    
    # Capital allocation
    allocation: CapitalAllocation = field(default_factory=CapitalAllocation)
    
    # Rangschikking
    ranking: list[dict] = field(default_factory=list)  # Gerangschikte opportuniteiten
    
    # Conflicten
    conflicts: list[dict] = field(default_factory=list)  # Conflicten tussen rollen
    
    # Statistieken
    stats: dict = field(default_factory=dict)


class OpportunityBuilder:
    """Bouwt opportunities uit signalen."""
    
    # Mapping van signaal betrouwbaarheid naar prioriteit bonus
    CONFIDENCE_PRIORITY_BONUS: dict[str, int] = {
        "hoog": 3,
        "voorlopig": 1,
        "speculatief": 0,
    }
    
    # Mapping van tijdshorizon naar prioriteit
    TIMEFRAME_PRIORITY: dict[str, int] = {
        "direct": 10,
        "kort termijn": 8,
        "middellange termijn": 5,
        "lange termijn": 3,
        "onbekend": 1,
    }
    
    @classmethod
    def build_opportunity(cls, signal: Signal, portfolio: PortfolioSnapshot | None = None) -> Opportunity | None:
        """Bouwt een opportunity uit een signaal.
        
        Args:
            signal: Het bron-signaal
            portfolio: Optionele portfolio snapshot voor context
            
        Returns:
            Opportunity of None als het signaal niet bruikbaar is
        """
        # Bepaal het type opportunity
        opportunity_type = cls._determine_opportunity_type(signal)
        
        # Bepaal de prioriteit
        priority = cls._calculate_priority(signal)
        
        # Bepaal de geschatte impact
        estimated_impact_eur, estimated_impact_pct = cls._estimate_impact(signal, portfolio)
        
        # Bepaal het risiconiveau
        risk_level = cls._determine_risk_level(signal)
        
        # Bouw de opportunity
        opportunity = Opportunity(
            id=f"opp_{signal.subject}_{signal.observed_at[:10]}_{signal.role.replace(' ', '_')}",
            subject=signal.subject,
            opportunity_type=opportunity_type,
            priority=priority,
            estimated_impact_eur=estimated_impact_eur,
            estimated_impact_pct=estimated_impact_pct,
            timeframe_horizon=signal.timeframe_horizon,
            confidence=signal.signal_confidence,
            risk_level=risk_level,
            related_positions=signal.related_positions,
            related_watchlist=signal.related_watchlist,
            source_signals=[signal.subject],
            recommended_action=cls._generate_recommended_action(signal, opportunity_type),
            role_consensus={signal.role: signal.signal_confidence},
        )
        
        return opportunity
    
    @classmethod
    def _determine_opportunity_type(cls, signal: Signal) -> OpportunityType:
        """Bepaalt het type opportunity op basis van het signaal."""
        text_lower = signal.text.lower()
        
        # Eerst checken op verkoop (moet voor koop omdat "koop" in "verkoop" zit)
        sell_keywords = [
            'verkoop ', ' sell ', 'bearish', 'negatief', 'daling', 
            'downgrade', 'target cut', 'daalt', 'verkoop aanbevolen', 
            'verkoop aanbeveling', 'verkoopaanbeveling'
        ]
        if any(kw in text_lower for kw in sell_keywords):
            return OpportunityType.SELL
        
        # Zoek naar koop-signalen
        buy_keywords = [
            ' koop ', ' buy ', 'bullish', 'positief', 'stijging', 
            'upgrade', 'target raised', ' stijgt ', 'koop aanbevolen', 
            'koop aanbeveling', 'koopaanbeveling'
        ]
        if any(kw in text_lower for kw in buy_keywords):
            return OpportunityType.BUY
        
        # Zoek naar hedge-signalen
        hedge_keywords = ['hedge', 'afdekken', 'risico', 'volatiliteit', 'uncertainty']
        if any(kw in text_lower for kw in hedge_keywords):
            return OpportunityType.HEDGE
        
        # Standaard: watch
        return OpportunityType.WATCH
    
    @classmethod
    def _calculate_priority(cls, signal: Signal) -> int:
        """Berekent de prioriteit van een opportunity."""
        # Basis prioriteit
        priority = 5
        
        # Voeg bonus toe voor betrouwbaarheid
        priority += cls.CONFIDENCE_PRIORITY_BONUS.get(signal.signal_confidence, 0)
        
        # Voeg bonus toe voor tijdshorizon
        priority += cls.TIMEFRAME_PRIORITY.get(signal.timeframe_horizon.lower(), 0)
        
        # Voeg bonus toe voor magnitude (als er een getal in zit)
        magnitude = signal.magnitude
        if '%' in magnitude:
            try:
                pct = float(magnitude.replace('%', '').strip())
                if pct > 10:
                    priority += 2
                elif pct > 5:
                    priority += 1
            except ValueError:
                pass
        
        # Limiteer tot 1-10
        return max(1, min(10, priority))
    
    @classmethod
    def _estimate_impact(cls, signal: Signal, portfolio: PortfolioSnapshot | None) -> tuple[float, float]:
        """Schat de financiele impact van een signaal."""
        # Als er een magnitude is met een percentage
        if '%' in signal.magnitude:
            try:
                pct = float(signal.magnitude.replace('%', '').replace(',', '.').strip())
                
                # Als we portfolio data hebben, bereken dan de impact
                if portfolio:
                    total_value = sum(p.value_eur for p in portfolio.positions)
                    impact_eur = total_value * (pct / 100)
                    return impact_eur, pct
                else:
                    return 0.0, pct
            except ValueError:
                pass
        
        # Als er een bedrag in zit
        if '$' in signal.magnitude or '\u20ac' in signal.magnitude or 'eur' in signal.magnitude.lower():
            try:
                amount_str = signal.magnitude.replace('$', '').replace('\u20ac', '').replace('eur', '').replace(',', '').strip()
                amount = float(amount_str)
                return amount, 0.0
            except ValueError:
                pass
        
        return 0.0, 0.0
    
    @classmethod
    def _determine_risk_level(cls, signal: Signal) -> RiskLevel:
        """Bepaalt het risiconiveau van een signaal."""
        # Lage betrouwbaarheid = hoog risico
        if signal.signal_confidence == "speculatief":
            return RiskLevel.HIGH
        
        # Hoge betrouwbaarheid = laag risico
        if signal.signal_confidence == "hoog" and signal.data_confidence == "hoog":
            return RiskLevel.LOW
        
        # Standaard: medium
        return RiskLevel.MEDIUM
    
    @classmethod
    def _generate_recommended_action(cls, signal: Signal, opportunity_type: OpportunityType) -> str:
        """Genereert een aanbevolen actie."""
        if opportunity_type == OpportunityType.BUY:
            return f"Overweeg koop bij {signal.subject} (confidentie: {signal.signal_confidence})"
        elif opportunity_type == OpportunityType.SELL:
            return f"Overweeg verkoop van {signal.subject} (confidentie: {signal.signal_confidence})"
        elif opportunity_type == OpportunityType.HEDGE:
            return f"Overweeg afdekken voor {signal.subject}"
        else:
            return f"Volg {signal.subject} (confidentie: {signal.signal_confidence})"


class CapitalMapBuilder:
    """Bouwt de complete capital map."""
    
    @classmethod
    def build_capital_map(
        cls,
        signals: list[Signal],
        portfolio: PortfolioSnapshot | None = None,
        cycle_id: str = "",
    ) -> CapitalMap:
        """Bouwt een capital map uit signalen en portfolio data.
        
        Args:
            signals: Lijst van valide, verse signalen
            portfolio: Optionele portfolio snapshot
            cycle_id: ID van de huidige cyclus
            
        Returns:
            CapitalMap object
        """
        opportunities = []
        conflicts = []
        role_opinions = {}  # {subject: {role: opinion}}
        
        # Bouw opportunities uit signalen
        for signal in signals:
            opportunity = OpportunityBuilder.build_opportunity(signal, portfolio)
            if opportunity:
                opportunities.append(opportunity)
                
                # Track opinions per subject per role (gebaseerd op opportunity_type)
                if signal.subject not in role_opinions:
                    role_opinions[signal.subject] = {}
                role_opinions[signal.subject][signal.role] = opportunity.opportunity_type.value
        
        # Detecteer conflicten
        conflicts = cls._detect_conflicts(role_opinions)
        
        # Update opportunities met conflict informatie
        for opportunity in opportunities:
            if opportunity.subject in [c['subject'] for c in conflicts]:
                opportunity.conflict = True
        
        # Rangschik opportunities
        ranking = cls._rank_opportunities(opportunities)
        
        # Bouw capital allocation
        allocation = cls._build_allocation(opportunities, portfolio)
        
        # Bouw statistieken
        stats = cls._build_stats(opportunities, signals, conflicts)
        
        return CapitalMap(
            id=f"capital_map_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            cycle_id=cycle_id,
            portfolio_snapshot=portfolio,
            signals=signals,
            opportunities=opportunities,
            allocation=allocation,
            ranking=ranking,
            conflicts=conflicts,
            stats=stats,
        )
    
    @classmethod
    def _detect_conflicts(cls, role_opinions: dict[str, dict[str, str]]) -> list[dict]:
        """Detecteert conflicten tussen rollen voor hetzelfde onderwerp."""
        conflicts = []
        
        for subject, opinions in role_opinions.items():
            if len(opinions) > 1:
                # Check of er verschillende meningen zijn
                unique_opinions = set(opinions.values())
                if len(unique_opinions) > 1:
                    conflicts.append({
                        'subject': subject,
                        'roles': list(opinions.keys()),
                        'opinions': opinions,
                        'severity': 'high' if len(unique_opinions) >= 3 else 'medium',
                    })
        
        return conflicts
    
    @classmethod
    def _rank_opportunities(cls, opportunities: list[Opportunity]) -> list[dict]:
        """Rangschikt opportunities op prioriteit."""
        # Sorteer op prioriteit (descending)
        sorted_opps = sorted(opportunities, key=lambda o: o.priority, reverse=True)
        
        # Bouw ranking lijst
        ranking = []
        for i, opp in enumerate(sorted_opps, 1):
            ranking.append({
                'rank': i,
                'opportunity_id': opp.id,
                'subject': opp.subject,
                'priority': opp.priority,
                'opportunity_type': opp.opportunity_type.value,
                'estimated_impact_eur': opp.estimated_impact_eur,
                'estimated_impact_pct': opp.estimated_impact_pct,
            })
        
        return ranking
    
    @classmethod
    def _build_allocation(cls, opportunities: list[Opportunity], portfolio: PortfolioSnapshot | None) -> CapitalAllocation:
        """Bouwt de capital allocation."""
        allocation = CapitalAllocation()
        
        if portfolio:
            # Bereken huidige allocatie
            total_value = sum(p.value_eur for p in portfolio.positions)
            for pos in portfolio.positions:
                allocation.current_positions[pos.ticker] = (pos.value_eur / total_value) * 100
            
            # Cash percentage
            allocation.current_cash_pct = 100 - sum(allocation.current_positions.values())
            allocation.total_portfolio_value = total_value
        
        # Voorgestelde allocatie (voor nu: zelfde als huidige)
        allocation.proposed_positions = allocation.current_positions.copy()
        allocation.proposed_cash_pct = allocation.current_cash_pct
        
        # Bereken diversificatiescore
        if allocation.current_positions:
            allocation.diversification_score = cls._calculate_diversification_score(allocation.current_positions)
        
        return allocation
    
    @classmethod
    def _calculate_diversification_score(cls, positions: dict[str, float]) -> float:
        """Berekent de diversificatiescore (0-100)."""
        if not positions:
            return 0.0
        
        # Een eenvoudige diversificatiescore: 100 - (max allocatie %)
        max_allocation = max(positions.values())
        return max(0, min(100, 100 - max_allocation))
    
    @classmethod
    def _build_stats(cls, opportunities: list[Opportunity], signals: list[Signal], conflicts: list[dict]) -> dict:
        """Bouwt statistieken voor de capital map."""
        return {
            'total_opportunities': len(opportunities),
            'total_signals': len(signals),
            'total_conflicts': len(conflicts),
            'opportunities_by_type': {
                t.value: sum(1 for o in opportunities if o.opportunity_type == t)
                for t in OpportunityType
            },
            'average_priority': sum(o.priority for o in opportunities) / len(opportunities) if opportunities else 0,
            'high_priority_count': sum(1 for o in opportunities if o.priority >= 8),
            'medium_priority_count': sum(1 for o in opportunities if 5 <= o.priority < 8),
            'low_priority_count': sum(1 for o in opportunities if o.priority < 5),
        }
