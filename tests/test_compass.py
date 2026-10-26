import unittest

from kompas.core.compass import THEMES, CompassReading, ThemeStance, validate_compass
from kompas.db.kompas_db import compass_doc


def _reading(**o):
    d = dict(stances=[ThemeStance(k, "neutraal", "reden", "bubbelmonitor 25/10") for k in THEMES],
             note="Eerste meting.", observed_at="2026-10-26T12:00:00+00:00")
    d.update(o)
    return CompassReading(**d)


class TestCompass(unittest.TestCase):
    def test_valid_reading_serializes_in_theme_order(self):
        doc = compass_doc(_reading())
        self.assertEqual(doc["path"], "compass/2026-10-26")
        self.assertEqual([t["key"] for t in doc["themes"]], list(THEMES))

    def test_every_theme_needed(self):
        self.assertFalse(validate_compass(_reading(stances=_reading().stances[:-1])).ok)

    def test_stance_needs_reason_and_source(self):
        bad = [ThemeStance(k, "positief", "", "") for k in THEMES]
        self.assertFalse(validate_compass(_reading(stances=bad)).ok)

    def test_unknown_stance_rejected(self):
        bad = [ThemeStance(k, "euforisch", "r", "s") for k in THEMES]
        self.assertFalse(validate_compass(_reading(stances=bad)).ok)


if __name__ == "__main__":
    unittest.main()
