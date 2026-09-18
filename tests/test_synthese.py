"""Tests voor Synthese-laag modules.

Test de nieuwe functionaliteit van de synthese-laag:
- capital_map.py: Capital Map bouwen
- decision_objects.py: Decision Objects genereren
- synthesis_cycle.py: Orchestratie
"""

import unittest
from datetime import datetime, timezone

from kompas.core.schema import (
    Position,
    WatchlistEntry,
    PortfolioSnapshot,
    PortfolioSummary,
)
from kompas.core.signal import Signal
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


class TestOpportunityBuilder(unittest.TestCase):
    """Test de OpportunityBuilder."""

    def test_build_opportunity_from_signal(self):
        """Test het bouwen van een opportunity uit een signaal."""
        signal = Signal(
            role="Stock watchers",
            subject="ASML",
            text="koop aanbeveling voor ASML na goede kwartaalcijfers",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="10%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
            related_positions=["ASML"],
        )
        
        opportunity = OpportunityBuilder.build_opportunity(signal)
        
        self.assertIsNotNone(opportunity)
        self.assertIsInstance(opportunity, Opportunity)
        self.assertEqual(opportunity.subject, "ASML")
        self.assertEqual(opportunity.opportunity_type, OpportunityType.BUY)
        self.assertGreater(opportunity.priority, 0)

    def test_opportunity_type_detection(self):
        """Test de detectie van opportunity types."""
        # Buy signaal
        buy_signal = Signal(
            role="Stock watchers",
            subject="Test",
            text="koop aanbeveling",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="5%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        opportunity = OpportunityBuilder.build_opportunity(buy_signal)
        self.assertEqual(opportunity.opportunity_type, OpportunityType.BUY)
        
        # Sell signaal
        sell_signal = Signal(
            role="Stock watchers",
            subject="Test",
            text="verkoop aanbeveling",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="5%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        opportunity = OpportunityBuilder.build_opportunity(sell_signal)
        self.assertEqual(opportunity.opportunity_type, OpportunityType.SELL)

    def test_priority_calculation(self):
        """Test de prioriteit berekening."""
        # Hoog vertrouwen, kort termijn
        high_priority_signal = Signal(
            role="Stock watchers",
            subject="Test",
            text="test",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="15%",
            timeframe_horizon="direct",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        opportunity = OpportunityBuilder.build_opportunity(high_priority_signal)
        self.assertEqual(opportunity.priority, 10)

    def test_risk_level_determination(self):
        """Test de risiconiveau bepaling."""
        # Speculatief vertrouwen = hoog risico
        speculatief_signal = Signal(
            role="Stock watchers",
            subject="Test",
            text="test",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="5%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="speculatief",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        opportunity = OpportunityBuilder.build_opportunity(speculatief_signal)
        self.assertEqual(opportunity.risk_level, RiskLevel.HIGH)
        
        # Hoog vertrouwen = laag risico
        hoog_signal = Signal(
            role="Stock watchers",
            subject="Test",
            text="test",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="5%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        opportunity = OpportunityBuilder.build_opportunity(hoog_signal)
        self.assertEqual(opportunity.risk_level, RiskLevel.LOW)


class TestCapitalMapBuilder(unittest.TestCase):
    """Test de CapitalMapBuilder."""

    def test_build_capital_map_empty(self):
        """Test het bouwen van een capital map met lege input."""
        capital_map = CapitalMapBuilder.build_capital_map(
            signals=[],
            portfolio=None,
        )
        
        self.assertIsNotNone(capital_map)
        self.assertIsInstance(capital_map, CapitalMap)
        self.assertEqual(len(capital_map.opportunities), 0)
        self.assertEqual(len(capital_map.conflicts), 0)

    def test_build_capital_map_with_signals(self):
        """Test het bouwen van een capital map met signalen."""
        signals = [
            Signal(
                role="Stock watchers",
                subject="ASML",
                text="ASML stijgt",
                source="https://example.com",
                source_tier="tier 1",
                magnitude="10%",
                timeframe_horizon="kort termijn",
                data_confidence="hoog",
                signal_confidence="hoog",
                observed_at=datetime.now(timezone.utc).isoformat(),
                related_positions=["ASML"],
            ),
            Signal(
                role="Trend viewers",
                subject="ASML",
                text="ASML daling verwacht",
                source="https://example.com",
                source_tier="tier 1",
                magnitude="5%",
                timeframe_horizon="middellange termijn",
                data_confidence="hoog",
                signal_confidence="hoog",
                observed_at=datetime.now(timezone.utc).isoformat(),
                related_positions=["ASML"],
            ),
        ]
        
        capital_map = CapitalMapBuilder.build_capital_map(signals=signals)
        
        self.assertEqual(len(capital_map.opportunities), 2)
        self.assertEqual(len(capital_map.conflicts), 1)  # Conflict op ASML
        self.assertEqual(capital_map.conflicts[0]['subject'], "ASML")

    def test_build_capital_map_with_portfolio(self):
        """Test het bouwen van een capital map met portfolio data."""
        portfolio = PortfolioSnapshot(
            positions=[
                Position(
                    name="ASML",
                    ticker="ASML",
                    exchange="Euronext Amsterdam",
                    type_effect="Aandelen",
                    currency="EUR",
                    qty=10,
                    cost_eur=1000,
                    value_eur=1100,
                    gain_eur=100,
                    gain_pct=10,
                ),
            ],
            watchlist=[],
            summary=PortfolioSummary(
                value_eur=1100,
                cost_eur=1000,
                gain_eur=100,
                gain_pct=10,
            ),
        )
        
        signals = [
            Signal(
                role="Stock watchers",
                subject="ASML",
                text="ASML stijgt",
                source="https://example.com",
                source_tier="tier 1",
                magnitude="10%",
                timeframe_horizon="kort termijn",
                data_confidence="hoog",
                signal_confidence="hoog",
                observed_at=datetime.now(timezone.utc).isoformat(),
                related_positions=["ASML"],
            ),
        ]
        
        capital_map = CapitalMapBuilder.build_capital_map(
            signals=signals,
            portfolio=portfolio,
        )
        
        self.assertEqual(len(capital_map.opportunities), 1)
        self.assertEqual(capital_map.allocation.total_portfolio_value, 1100)


class TestDecisionObjectBuilder(unittest.TestCase):
    """Test de DecisionObjectBuilder."""

    def test_build_decision_objects_empty(self):
        """Test het bouwen van decision objects met lege input."""
        capital_map = CapitalMapBuilder.build_capital_map(
            signals=[],
            portfolio=None,
        )
        
        result = DecisionObjectBuilder.build_decision_objects(
            capital_map=capital_map,
            portfolio=None,
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DecisionObjectCollection)
        self.assertEqual(len(result.decision_objects), 0)

    def test_build_decision_objects_with_portfolio(self):
        """Test het bouwen van decision objects met portfolio."""
        portfolio = PortfolioSnapshot(
            positions=[
                Position(
                    name="ASML",
                    ticker="ASML",
                    exchange="Euronext Amsterdam",
                    type_effect="Aandelen",
                    currency="EUR",
                    qty=10,
                    cost_eur=1000,
                    value_eur=1100,
                    gain_eur=100,
                    gain_pct=10,
                ),
            ],
            watchlist=[
                WatchlistEntry(
                    name="NVDA",
                    ticker="NVDA",
                    exchange="NASDAQ",
                    type_effect="Aandelen",
                    currency="USD",
                    set_date="2024-01-01",
                    reference_value_eur=100,
                    current_value_eur=120,
                    opportunity_gain_eur=20,
                    opportunity_gain_pct=20,
                ),
            ],
            summary=PortfolioSummary(
                value_eur=1100,
                cost_eur=1000,
                gain_eur=100,
                gain_pct=10,
            ),
        )
        
        signals = [
            Signal(
                role="Stock watchers",
                subject="ASML",
                text="ASML stijgt",
                source="https://example.com",
                source_tier="tier 1",
                magnitude="10%",
                timeframe_horizon="kort termijn",
                data_confidence="hoog",
                signal_confidence="hoog",
                observed_at=datetime.now(timezone.utc).isoformat(),
                related_positions=["ASML"],
            ),
        ]
        
        capital_map = CapitalMapBuilder.build_capital_map(
            signals=signals,
            portfolio=portfolio,
        )
        
        result = DecisionObjectBuilder.build_decision_objects(
            capital_map=capital_map,
            portfolio=portfolio,
        )
        
        # Moet 1 decision object voor ASML (positie) en 1 voor NVDA (watchlist) hebben
        self.assertEqual(len(result.decision_objects), 2)
        
        # Check ASML decision object
        asml_do = next((do for do in result.decision_objects if do.ticker == "ASML"), None)
        self.assertIsNotNone(asml_do)
        self.assertTrue(asml_do.is_position)
        self.assertEqual(asml_do.name, "ASML")

    def test_decision_action_determination(self):
        """Test de bepaling van decision acties."""
        portfolio = PortfolioSnapshot(
            positions=[
                Position(
                    name="ASML",
                    ticker="ASML",
                    exchange="",
                    type_effect="",
                    currency="EUR",
                    qty=10,
                    cost_eur=1000,
                    value_eur=1100,
                    gain_eur=100,
                    gain_pct=10,
                ),
            ],
            watchlist=[],
            summary=PortfolioSummary(value_eur=1100, cost_eur=1000, gain_eur=100, gain_pct=10),
        )
        
        # Sell opportunity met hoge prioriteit
        signals = [
            Signal(
                role="Stock watchers",
                subject="ASML",
                text="ASML daling verwacht, verkoop aanbevolen",
                source="https://example.com",
                source_tier="tier 1",
                magnitude="-15%",
                timeframe_horizon="kort termijn",
                data_confidence="hoog",
                signal_confidence="hoog",
                observed_at=datetime.now(timezone.utc).isoformat(),
                related_positions=["ASML"],
            ),
        ]
        
        capital_map = CapitalMapBuilder.build_capital_map(
            signals=signals,
            portfolio=portfolio,
        )
        
        result = DecisionObjectBuilder.build_decision_objects(
            capital_map=capital_map,
            portfolio=portfolio,
        )
        
        asml_do = next((do for do in result.decision_objects if do.ticker == "ASML"), None)
        self.assertIsNotNone(asml_do)
        self.assertEqual(asml_do.action, ActionType.SELL)


class TestSynthesisCycle(unittest.TestCase):
    """Test de SynthesisCycle."""

    def test_run_synthesis_cycle(self):
        """Test het uitvoeren van een complete synthese cyclus."""
        from kompas.pijler_a.cycle import PijlerACycleResult, RoleScanResult
        from kompas.pijler_b.cycle import CycleResult
        from kompas.core.schema import PortfolioSnapshot, Position, WatchlistEntry, PortfolioSummary, ReconciliationResult
        
        # Maak mock resultaten
        pijler_a_result = PijlerACycleResult(
            role_results={},
            publishable_signals=[
                Signal(
                    role="Stock watchers",
                    subject="ASML",
                    text="ASML stijgt",
                    source="https://example.com",
                    source_tier="tier 1",
                    magnitude="10%",
                    timeframe_horizon="kort termijn",
                    data_confidence="hoog",
                    signal_confidence="hoog",
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    related_positions=["ASML"],
                ),
            ],
            total_signals_scanned=1,
            total_signals_valid=1,
            total_signals_fresh=1,
            total_signals_suppressed=0,
            write_payloads=[],
            errors=[],
        )
        
        portfolio = PortfolioSnapshot(
            positions=[
                Position(
                    name="ASML",
                    ticker="ASML",
                    exchange="",
                    type_effect="",
                    currency="EUR",
                    qty=10,
                    cost_eur=1000,
                    value_eur=1100,
                    gain_eur=100,
                    gain_pct=10,
                ),
            ],
            watchlist=[],
            summary=PortfolioSummary(value_eur=1100, cost_eur=1000, gain_eur=100, gain_pct=10),
        )
        
        pijler_b_result = CycleResult(
            snapshot=portfolio,
            reconciliation=ReconciliationResult(
                ok=True,
                computed_value_eur=1100,
                computed_cost_eur=1000,
                computed_gain_eur=100,
                computed_gain_pct=10,
                sheet_value_eur=1100,
                sheet_cost_eur=1000,
                sheet_gain_eur=100,
                sheet_gain_pct=10,
                diffs={},
                watchlist_count=0,
            ),
            write_batch=[],
        )
        
        result = run_synthesis_cycle(
            pijler_a_result=pijler_a_result,
            pijler_b_result=pijler_b_result,
            cycle_id="test_cycle",
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SynthesisResult)
        self.assertIsNotNone(result.capital_map)
        self.assertIsNotNone(result.decision_objects)
        self.assertEqual(len(result.errors), 0)

    def test_synthesis_with_reconciliation_failure(self):
        """Test synthese met een mislukte reconciliatie."""
        from kompas.pijler_a.cycle import PijlerACycleResult
        from kompas.pijler_b.cycle import CycleResult
        from kompas.core.schema import PortfolioSnapshot, PortfolioSummary, ReconciliationResult
        
        pijler_a_result = PijlerACycleResult(
            role_results={},
            publishable_signals=[],
            total_signals_scanned=0,
            total_signals_valid=0,
            total_signals_fresh=0,
            total_signals_suppressed=0,
            write_payloads=[],
            errors=[],
        )
        
        pijler_b_result = CycleResult(
            snapshot=PortfolioSnapshot(
                positions=[],
                watchlist=[],
                summary=PortfolioSummary(value_eur=0, cost_eur=0, gain_eur=0, gain_pct=0),
            ),
            reconciliation=ReconciliationResult(
                ok=False,
                computed_value_eur=0,
                computed_cost_eur=0,
                computed_gain_eur=0,
                computed_gain_pct=0,
                sheet_value_eur=100,
                sheet_cost_eur=100,
                sheet_gain_eur=0,
                sheet_gain_pct=0,
                diffs={"value_eur": 100},
                watchlist_count=0,
            ),
            write_batch=[],
        )
        
        result = run_synthesis_cycle(
            pijler_a_result=pijler_a_result,
            pijler_b_result=pijler_b_result,
        )
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result.errors), 0)
        self.assertIsNone(result.capital_map)
        self.assertIsNone(result.decision_objects)


if __name__ == '__main__':
    unittest.main()
