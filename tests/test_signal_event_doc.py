import unittest

from kompas.core.signal import CapitalView, Signal
from kompas.db.kompas_db import signal_event_doc


def _valid_signal(**overrides) -> Signal:
    defaults = dict(
        role="Sector specialist – Uranium/Nucleair",
        subject="Uranium/Nucleair",
        text="Capex-cyclus versnelt.",
        source='World Nuclear News, "..." (18 sep 2026)',
        source_tier="tier 1",
        magnitude="Raakt CCJ, 5-10% van sector-capex",
        timeframe_horizon="Q4 2026",
        data_confidence="hoog",
        signal_confidence="voorlopig",
        observed_at="2026-09-18T09:00:00+00:00",
        related_watchlist=["CCJ"],
    )
    defaults.update(overrides)
    return Signal(**defaults)


class TestSignalEventDoc(unittest.TestCase):
    def test_valid_signal_produces_a_path_and_fields(self):
        doc = signal_event_doc(_valid_signal())
        self.assertTrue(doc["path"].startswith("events/uranium-nucleair-2026-09-18-"))
        self.assertEqual(doc["related_watchlist"], ["CCJ"])
        self.assertEqual(doc["related_positions"], [])
        self.assertIsNone(doc["capital_view"])

    def test_capital_view_serializes_as_a_plain_dict(self):
        sig = _valid_signal(capital_view=CapitalView(action="wacht", reasoning="Te vroeg.", trigger="Bij Q4-cijfers."))
        doc = signal_event_doc(sig)
        self.assertEqual(
            doc["capital_view"],
            {"action": "wacht", "reasoning": "Te vroeg.", "trigger": "Bij Q4-cijfers."},
        )

    def test_invalid_signal_raises_instead_of_producing_a_bad_doc(self):
        bad = _valid_signal(source="sectorpers")
        with self.assertRaises(ValueError):
            signal_event_doc(bad)

    def test_invalid_capital_view_also_raises(self):
        bad = _valid_signal(capital_view=CapitalView(action="verhoog_bestaand", reasoning="x", trigger="y"))
        with self.assertRaises(ValueError):
            signal_event_doc(bad)

    def test_capital_view_without_trigger_also_raises(self):
        bad = _valid_signal(capital_view=CapitalView(action="wacht", reasoning="x", trigger=""))
        with self.assertRaises(ValueError):
            signal_event_doc(bad)


if __name__ == "__main__":
    unittest.main()
