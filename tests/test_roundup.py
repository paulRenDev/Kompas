import unittest

from kompas.core.roundup import MAX_TEXT_CHARS, PortfolioRoundup, validate_roundup
from kompas.db.kompas_db import portfolio_roundup_doc


def _roundup(**overrides) -> PortfolioRoundup:
    defaults = dict(
        text="Kern stabiel, energiepaar lager op rentevrees.",
        observed_at="2026-09-28T16:45:00+00:00",
        value_eur=6875.8,
        gain_eur=114.91,
        gain_pct=1.7,
        day_change_eur=-34.17,
    )
    defaults.update(overrides)
    return PortfolioRoundup(**defaults)


class TestRoundup(unittest.TestCase):
    def test_valid_roundup_passes_and_is_keyed_by_date(self):
        self.assertTrue(validate_roundup(_roundup()).ok)
        doc = portfolio_roundup_doc(_roundup())
        self.assertEqual(doc["path"], "portfolio_roundups/2026-09-28")
        self.assertEqual(doc["day_change_eur"], -34.17)

    def test_empty_text_rejected(self):
        self.assertFalse(validate_roundup(_roundup(text="   ")).ok)

    def test_too_long_rejected(self):
        result = validate_roundup(_roundup(text="x" * (MAX_TEXT_CHARS + 1)))
        self.assertFalse(result.ok)
        self.assertTrue(any("max" in e for e in result.errors))

    def test_zero_value_rejected(self):
        with self.assertRaises(ValueError):
            portfolio_roundup_doc(_roundup(value_eur=0))


if __name__ == "__main__":
    unittest.main()
