import unittest

from kompas.core.bubble_monitor import INDICATORS, BubbleReading, IndicatorReading, level, validate_bubble_reading
from kompas.db.kompas_db import bubble_reading_doc


def _reading(statuses=None, **overrides):
    statuses = statuses or {}
    defaults = dict(
        readings=[IndicatorReading(k, statuses.get(k, "groen"), "feit met cijfer", "bron") for k in INDICATORS],
        note="Niets veranderd.",
        observed_at="2026-10-09T16:30:00+00:00",
    )
    defaults.update(overrides)
    return BubbleReading(**defaults)


class TestLevel(unittest.TestCase):
    def test_all_green_is_calm(self):
        self.assertEqual(level(_reading()), "rustig")

    def test_one_red_means_watch(self):
        self.assertEqual(level(_reading({"rente": "rood"})), "opletten")

    def test_three_oranges_mean_watch(self):
        self.assertEqual(level(_reading({"rente": "oranje", "krediet": "oranje", "breedte": "oranje"})), "opletten")

    def test_three_reds_mean_alarm(self):
        self.assertEqual(level(_reading({"rente": "rood", "krediet": "rood", "capex": "rood"})), "alarm")


class TestValidate(unittest.TestCase):
    def test_valid_reading_serializes_in_fixed_order(self):
        doc = bubble_reading_doc(_reading({"rente": "rood"}))
        self.assertEqual(doc["path"], "bubble_monitor/2026-10-09")
        self.assertEqual([i["key"] for i in doc["indicators"]], list(INDICATORS))
        self.assertEqual(doc["level"], "opletten")

    def test_missing_indicator_rejected(self):
        r = _reading()
        self.assertFalse(validate_bubble_reading(_reading(readings=r.readings[:-1])).ok)

    def test_status_without_source_rejected(self):
        bad = [IndicatorReading(k, "oranje", "voelt duur", "") for k in INDICATORS]
        self.assertFalse(validate_bubble_reading(_reading(readings=bad)).ok)

    def test_unknown_needs_no_source(self):
        ok = [IndicatorReading(k, "onbekend", "geen cijfer gevonden", "") for k in INDICATORS]
        self.assertTrue(validate_bubble_reading(_reading(readings=ok)).ok)

    def test_invalid_reading_is_not_written(self):
        with self.assertRaises(ValueError):
            bubble_reading_doc(_reading(note=" "))


if __name__ == "__main__":
    unittest.main()
