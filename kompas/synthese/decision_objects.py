"""Synthese-laag - Decision Objects.

Genereert decision objects voor elke positie en watchlist-naam.

Een decision object:
- Bevat een concrete actie (BUY/SELL/HOLD/REBALANCE)
- Heeft een actiedrempel (prijsniveau)
- Wordt gegenereerd op basis van de capital map en portefeuille data
- Wordt nooit herhaald zonder nieuwe input

Belangrijke principes:
- Elke actieve positie krijgt een decision object per cyclus
- Elke watchlist-naam krijgt een decision object per cyclus
- Conflicten tussen signalen worden zichtbaar in het decision object
- De actiedrempel is gebaseerd op technisch/fundamenteel onderzoek
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from kompas.core.schema import Position, WatchlistEntry, PortfolioSnapshot
from kompas.synthese.capital_map import CapitalMap, Opportunity, OpportunityType, OpportunityBuilder


class ActionType(Enum):
    """Type actie voor een decision object."""
    BUY = "buy"             # Koop (nieuwe positie of bijkopen)
    SELL = "sell"           # Verkoop (winst nemen of verlies beperken)
    HOLD = "hold"           # Houden (geen actie)
    REBALANCE = "rebalance" # Herbalanceren (allocatie aanpassen)
    WATCH = "watch"         # Volgen (nog geen actie, maar in de gaten houden)


class DecisionConfidence(Enum):
    """Betrouwbaarheidsniveau van een decision."""
    HIGH = "high"           # Hoog vertrouwen (meerdere signalen, consistente data)
    MEDIUM = "medium"       # Gemiddeld vertrouwen
    LOW = "low"             # Laag vertrouwen (speculatief, tegenstrijdige signalen)


@dataclass
class DecisionObject:
    """Een decision object voor een specifieke positie of watchlist-naam."""
    
    # Identificatie
    id: str
    name: str
    ticker: str
    exchange: str = ""
    
    # Type
    is_position: bool = False  # True = actieve positie, False = watchlist
    is_watchlist: bool = False
    
    # Actie
    action: ActionType = ActionType.HOLD
    confidence: DecisionConfidence = DecisionConfidence.MEDIUM
    
    # Drempels
    action_threshold: float = 0.0  # Prijsniveau voor actie
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Context
    current_price: float = 0.0
    target_price: float = 0.0
    current_allocation_pct: float = 0.0
    target_allocation_pct: float = 0.0
    
    # Signal context
    related_opportunities: list[str] = field(default_factory=list)  # Opportunity IDs
    supporting_signals: list[str] = field(default_factory=list)  # Signal IDs
    conflicting_signals: list[str] = field(default_factory=list)  # Signal IDs
    
    # Financiele data (voor posities)
    cost_eur: float = 0.0
    value_eur: float = 0.0
    gain_eur: float = 0.0
    gain_pct: float = 0.0
    qty: int = 0
    
    # Metadata
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cycle_id: str = ""


@dataclass
class DecisionObjectCollection:
    """Collectie van decision objects."""
    
    decision_objects: list[DecisionObject] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cycle_id: str = ""
    
    # Statistieken
    stats: dict = field(default_factory=dict)


class DecisionObjectBuilder:
    """Bouwt decision objects uit een capital map en portfolio data."""
    
    # Weight factors voor actie bepaling
    PRIORITY_WEIGHT = 0.4
    CONFIDENCE_WEIGHT = 0.3
    IMPACT_WEIGHT = 0.3
    
    @classmethod
    def build_decision_objects(
        cls,
        capital_map: CapitalMap,
        portfolio: PortfolioSnapshot | None = None,
        cycle_id: str = "",
    ) -> DecisionObjectCollection:
        """Bouwt decision objects voor alle posities en watchlist-namen.
        
        Args:
            capital_map: De capital map met opportunities en conflicts
            portfolio: Portfolio snapshot met posities en watchlist
            cycle_id: ID van de huidige cyclus
            
        Returns:
            DecisionObjectCollection met alle decision objects
        """
        decision_objects = []
        
        if portfolio:
            # Maak decision objects voor actieve posities
            for pos in portfolio.positions:
                do = cls._build_decision_object_for_position(
                    pos, capital_map, portfolio, cycle_id
                )
                if do:
                    do.is_position = True
                    decision_objects.append(do)
            
            # Maak decision objects voor watchlist
            for wl in portfolio.watchlist:
                do = cls._build_decision_object_for_watchlist(
                    wl, capital_map, portfolio, cycle_id
                )
                if do:
                    do.is_watchlist = True
                    decision_objects.append(do)
        else:
            # Maak decision objects alleen voor opportunities
            for opp in capital_map.opportunities:
                do = cls._build_decision_object_from_opportunity(
                    opp, capital_map, cycle_id
                )
                if do:
                    decision_objects.append(do)
        
        # Bouw statistieken
        stats = cls._build_stats(decision_objects)
        
        return DecisionObjectCollection(
            decision_objects=decision_objects,
            cycle_id=cycle_id,
            stats=stats,
        )
    
    @classmethod
    def _build_decision_object_for_position(
        cls,
        position: Position,
        capital_map: CapitalMap,
        portfolio: PortfolioSnapshot,
        cycle_id: str,
    ) -> DecisionObject | None:
        """Bouwt een decision object voor een actieve positie."""
        # Zoek gerelateerde opportunities
        related_opps = [
            opp for opp in capital_map.opportunities
            if position.name in opp.related_positions or position.ticker in opp.related_positions
        ]
        
        # Zoek gerelateerde signalen
        supporting_signals = []
        conflicting_signals = []
        
        for signal in capital_map.signals:
            if position.name in signal.related_positions or position.ticker in signal.related_positions:
                # Bepaal of het signaal supporting of conflicting is
                opp_type = OpportunityBuilder._determine_opportunity_type(signal)
                if opp_type in [OpportunityType.BUY, OpportunityType.WATCH]:
                    supporting_signals.append(signal.subject)
                elif opp_type in [OpportunityType.SELL, OpportunityType.HEDGE]:
                    conflicting_signals.append(signal.subject)
        
        # Bepaal actie
        action, confidence, reason = cls._determine_action(
            related_opps, supporting_signals, conflicting_signals, position
        )
        
        # Bepaal drempels (voor nu: placeholder waarden)
        action_threshold = cls._calculate_action_threshold(position, related_opps)
        
        # Bouw het decision object
        do = DecisionObject(
            id=f"do_{position.ticker}_{cycle_id}",
            name=position.name,
            ticker=position.ticker,
            exchange=position.exchange,
            action=action,
            confidence=confidence,
            action_threshold=action_threshold,
            current_price=position.value_eur / position.qty if position.qty > 0 else 0.0,
            target_price=cls._calculate_target_price(position, related_opps),
            current_allocation_pct=cls._calculate_allocation_pct(position, portfolio),
            target_allocation_pct=position.gain_pct / 100,  # Placeholder
            related_opportunities=[opp.id for opp in related_opps],
            supporting_signals=supporting_signals,
            conflicting_signals=conflicting_signals,
            cost_eur=position.cost_eur,
            value_eur=position.value_eur,
            gain_eur=position.gain_eur,
            gain_pct=position.gain_pct,
            qty=position.qty,
            reason=reason,
            cycle_id=cycle_id,
        )
        
        return do
    
    @classmethod
    def _build_decision_object_for_watchlist(
        cls,
        watchlist_entry: WatchlistEntry,
        capital_map: CapitalMap,
        portfolio: PortfolioSnapshot,
        cycle_id: str,
    ) -> DecisionObject | None:
        """Bouwt een decision object voor een watchlist-naam."""
        # Zoek gerelateerde opportunities
        related_opps = [
            opp for opp in capital_map.opportunities
            if (watchlist_entry.name in opp.related_watchlist or 
                watchlist_entry.ticker in opp.related_watchlist)
        ]
        
        # Zoek gerelateerde signalen
        supporting_signals = []
        conflicting_signals = []
        
        for signal in capital_map.signals:
            if (watchlist_entry.name in signal.related_watchlist or 
                watchlist_entry.ticker in signal.related_watchlist):
                opp_type = OpportunityBuilder._determine_opportunity_type(signal)
                if opp_type in [OpportunityType.BUY, OpportunityType.WATCH]:
                    supporting_signals.append(signal.subject)
                elif opp_type in [OpportunityType.SELL, OpportunityType.HEDGE]:
                    conflicting_signals.append(signal.subject)
        
        # Bepaal actie
        action, confidence, reason = cls._determine_action(
            related_opps, supporting_signals, conflicting_signals, None, is_watchlist=True
        )
        
        # Bepaal drempels
        action_threshold = cls._calculate_action_threshold(watchlist_entry, related_opps)
        
        # Bouw het decision object
        do = DecisionObject(
            id=f"do_{watchlist_entry.ticker}_wl_{cycle_id}",
            name=watchlist_entry.name,
            ticker=watchlist_entry.ticker,
            exchange=watchlist_entry.exchange,
            action=action,
            confidence=confidence,
            action_threshold=action_threshold,
            current_price=watchlist_entry.current_value_eur,
            target_price=cls._calculate_target_price(watchlist_entry, related_opps),
            current_allocation_pct=0.0,  # Watchlist heeft geen allocatie
            target_allocation_pct=0.0,
            related_opportunities=[opp.id for opp in related_opps],
            supporting_signals=supporting_signals,
            conflicting_signals=conflicting_signals,
            reason=reason,
            cycle_id=cycle_id,
        )
        
        return do
    
    @classmethod
    def _build_decision_object_from_opportunity(
        cls,
        opportunity: Opportunity,
        capital_map: CapitalMap,
        cycle_id: str,
    ) -> DecisionObject | None:
        """Bouwt een decision object direct uit een opportunity."""
        # Bepaal actie gebaseerd op opportunity type
        action_map = {
            OpportunityType.BUY: ActionType.BUY,
            OpportunityType.SELL: ActionType.SELL,
            OpportunityType.HOLD: ActionType.HOLD,
            OpportunityType.WATCH: ActionType.WATCH,
            OpportunityType.HEDGE: ActionType.HEDGE,
        }
        
        action = action_map.get(opportunity.opportunity_type, ActionType.WATCH)
        
        # Bepaal confidence
        confidence_map = {
            "hoog": DecisionConfidence.HIGH,
            "voorlopig": DecisionConfidence.MEDIUM,
            "speculatief": DecisionConfidence.LOW,
        }
        confidence = confidence_map.get(opportunity.confidence, DecisionConfidence.MEDIUM)
        
        do = DecisionObject(
            id=f"do_{opportunity.subject}_{cycle_id}",
            name=opportunity.subject,
            ticker=opportunity.subject,  # Gebruik subject als ticker
            action=action,
            confidence=confidence,
            action_threshold=opportunity.action_threshold,
            reason=opportunity.recommended_action,
            related_opportunities=[opportunity.id],
            cycle_id=cycle_id,
        )
        
        return do
    
    @classmethod
    def _determine_action(
        cls,
        related_opps: list[Opportunity],
        supporting_signals: list[str],
        conflicting_signals: list[str],
        position: Position | None = None,
        is_watchlist: bool = False,
    ) -> tuple[ActionType, DecisionConfidence, str]:
        """Bepaalt de actie, confidence en reden voor een decision object."""
        # Tel het gewicht van elke actie type
        buy_weight = 0
        sell_weight = 0
        hold_weight = 0
        hedge_weight = 0
        
        for opp in related_opps:
            weight = opp.priority * (1 if opp.confidence == "hoog" else 0.5)
            if opp.opportunity_type == OpportunityType.BUY:
                buy_weight += weight
            elif opp.opportunity_type == OpportunityType.SELL:
                sell_weight += weight
            elif opp.opportunity_type == OpportunityType.HOLD:
                hold_weight += weight
            elif opp.opportunity_type == OpportunityType.HEDGE:
                hedge_weight += weight
        
        # Bepaal de hoogste gewicht
        max_weight = max(buy_weight, sell_weight, hold_weight, hedge_weight)
        
        # Bepaal actie
        if max_weight == 0:
            action = ActionType.HOLD
            reason = "Geen relevante signalen"
        elif max_weight == buy_weight:
            action = ActionType.BUY
            reason = f"Koop signaal met gewicht {buy_weight:.1f}"
        elif max_weight == sell_weight:
            action = ActionType.SELL
            reason = f"Verkoop signaal met gewicht {sell_weight:.1f}"
        elif max_weight == hedge_weight:
            action = ActionType.HEDGE
            reason = f"Hedge signaal met gewicht {hedge_weight:.1f}"
        else:
            action = ActionType.HOLD
            reason = "Gemengde signalen, geen duidelijke actie"
        
        # Bepaal confidence
        total_signals = len(supporting_signals) + len(conflicting_signals)
        if total_signals == 0:
            confidence = DecisionConfidence.LOW
        elif len(conflicting_signals) == 0:
            confidence = DecisionConfidence.HIGH
        elif len(supporting_signals) > len(conflicting_signals):
            confidence = DecisionConfidence.MEDIUM
        else:
            confidence = DecisionConfidence.LOW
        
        # Voeg conflict informatie toe aan reason
        if len(conflicting_signals) > 0 and len(supporting_signals) > 0:
            reason += f" (conflict: {len(conflicting_signals)} tegen {len(supporting_signals)})"
        
        # Voor watchlist: standaard WATCH als geen sterke signalen
        if is_watchlist and action == ActionType.HOLD and max_weight < 5:
            action = ActionType.WATCH
            reason = "Watchlist: volgen tot sterker signaal"
        
        return action, confidence, reason
    
    @classmethod
    def _calculate_action_threshold(
        cls,
        item: Position | WatchlistEntry,
        related_opps: list[Opportunity],
    ) -> float:
        """Berekent de actiedrempel prijs."""
        # Voor nu: gebruik de current price als basis
        if isinstance(item, Position):
            current_price = item.value_eur / item.qty if item.qty > 0 else 0.0
        else:
            current_price = item.current_value_eur
        
        # Voeg een buffer toe gebaseerd op de gemiddelde opportunity prioriteit
        if related_opps:
            avg_priority = sum(o.priority for o in related_opps) / len(related_opps)
            # Hoogere prioriteit = grotere buffer
            buffer_pct = avg_priority / 100
            return current_price * (1 + buffer_pct)
        
        return current_price
    
    @classmethod
    def _calculate_target_price(
        cls,
        item: Position | WatchlistEntry,
        related_opps: list[Opportunity],
    ) -> float:
        """Berekent de target prijs."""
        if isinstance(item, Position):
            current_price = item.value_eur / item.qty if item.qty > 0 else 0.0
        else:
            current_price = item.current_value_eur
        
        # Gebruik de gemiddelde estimated impact
        if related_opps:
            avg_impact_pct = sum(o.estimated_impact_pct for o in related_opps) / len(related_opps)
            return current_price * (1 + avg_impact_pct / 100)
        
        return current_price
    
    @classmethod
    def _calculate_allocation_pct(
        cls,
        position: Position,
        portfolio: PortfolioSnapshot,
    ) -> float:
        """Berekent de huidige allocatie percentage."""
        if portfolio.summary.value_eur > 0:
            return (position.value_eur / portfolio.summary.value_eur) * 100
        return 0.0
    
    @classmethod
    def _build_stats(cls, decision_objects: list[DecisionObject]) -> dict:
        """Bouwt statistieken voor de decision object collectie."""
        return {
            'total_decision_objects': len(decision_objects),
            'by_action': {
                a.value: sum(1 for do in decision_objects if do.action == a)
                for a in ActionType
            },
            'by_confidence': {
                c.value: sum(1 for do in decision_objects if do.confidence == c)
                for c in DecisionConfidence
            },
            'positions_with_action': sum(
                1 for do in decision_objects 
                if do.is_position and do.action != ActionType.HOLD
            ),
            'watchlist_with_action': sum(
                1 for do in decision_objects 
                if do.is_watchlist and do.action != ActionType.WATCH
            ),
        }
