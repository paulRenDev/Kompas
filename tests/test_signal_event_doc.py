import unittest

from kompas.core.signal import Signal
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
        self.assertTrue(doc["relevant"])
        self.assertIsNone(doc["closed_reason"])

    def test_closed_signal_serializes_relevant_and_reason(self):
        sig = _valid_signal(relevant=False, closed_reason="Top afgerond, geen vervolg meer.")
        doc = signal_event_doc(sig)
        self.assertFalse(doc["relevant"])
        self.assertEqual(doc["closed_reason"], "Top afgerond, geen vervolg meer.")

    def test_invalid_signal_raises_instead_of_producing_a_bad_doc(self):
        bad = _valid_signal(source="sectorpers")
        with self.assertRaises(ValueError):
            signal_event_doc(bad)

    def test_not_relevant_without_reason_also_raises(self):
        bad = _valid_signal(relevant=False)
        with self.assertRaises(ValueError):
            signal_event_doc(bad)


if __name__ == "__main__":
    unittest.main()
