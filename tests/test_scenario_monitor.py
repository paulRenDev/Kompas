import unittest

from kompas.core.scenario_monitor import (HEDGE_CAP, SCENARIOS, ScenarioReading, ScenarioSnapshot, any_acute,
                                          hedge_room_eur, hedge_share, validate_scenarios)
from kompas.db.kompas_db import scenario_snapshot_doc


def _snap(statuses=None, **o):
    statuses = statuses or {}
    d = dict(readings=[ScenarioReading(k, statuses.get(k, "laag"), "feit", "bron") for k in SCENARIOS],
             note="Niets veranderd.", observed_at="2026-10-12T16:30:00+00:00")
    d.update(o)
    return ScenarioSnapshot(**d)


class TestScenarios(unittest.TestCase):
    def test_valid_snapshot_serializes_in_order(self):
        doc = scenario_snapshot_doc(_snap({"olie_geopolitiek": "stijgend"}))
        self.assertEqual(doc["path"], "scenario_monitor/2026-10-12")
        self.assertEqual([s["key"] for s in doc["scenarios"]], list(SCENARIOS))
        self.assertFalse(doc["any_acute"])

    def test_acute_detected(self):
        self.assertTrue(any_acute(_snap({"vertrouwen_vs": "acuut"})))

    def test_status_without_source_rejected(self):
        bad = [ScenarioReading(k, "stijgend", "voelt eng", "") for k in SCENARIOS]
        self.assertFalse(validate_scenarios(_snap(readings=bad)).ok)

    def test_eurozone_debt_is_watched(self):
        self.assertIn("eurozone_schuld", SCENARIOS)
        self.assertFalse(validate_scenarios(_snap(readings=[r for r in _snap().readings if r.key != "eurozone_schuld"])).ok)

    def test_missing_scenario_rejected(self):
        self.assertFalse(validate_scenarios(_snap(readings=_snap().readings[:-1])).ok)


class TestHedgeCap(unittest.TestCase):
    def test_room_fills_exactly_to_the_cap(self):
        wallet = {"IWDA": 7000.0, "GOLD": 0.0}
        room = hedge_room_eur(wallet)
        after = dict(wallet, GOLD=room)
        self.assertAlmostEqual(hedge_share(after), HEDGE_CAP, places=4)

    def test_no_room_above_the_cap(self):
        self.assertEqual(hedge_room_eur({"IWDA": 1000.0, "GOLD": 500.0}), 0.0)

    def test_cash_reserve_counts_as_insurance(self):
        self.assertLess(hedge_room_eur({"IWDA": 7000.0}, cash_reserve_eur=500.0), hedge_room_eur({"IWDA": 7000.0}))


if __name__ == "__main__":
    unittest.main()
