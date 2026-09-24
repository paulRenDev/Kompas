import unittest

from kompas.core.capital_call import CapitalCall
from kompas.core.signal import CapitalView
from kompas.db.kompas_db import capital_call_doc


def _valid_call(**overrides) -> CapitalCall:
    defaults = dict(
        capital_view=CapitalView(
            action="wacht",
            reasoning="Geen van de vandaag afgewogen subjecten haalt de lat.",
            trigger="Heroverweeg bij een duidelijke koersdaling op een van de watchlist-namen.",
        ),
        observed_at="2026-09-24T16:15:00+00:00",
        considered=["MP Materials", "Taiwan-wapenpakket"],
    )
    defaults.update(overrides)
    return CapitalCall(**defaults)


class TestCapitalCallDoc(unittest.TestCase):
    def test_valid_call_produces_a_path_and_fields(self):
        doc = capital_call_doc(_valid_call())
        self.assertTrue(doc["path"].startswith("capital_calls/"))
        self.assertEqual(doc["capital_view"]["action"], "wacht")
        self.assertEqual(doc["considered"], ["MP Materials", "Taiwan-wapenpakket"])
        self.assertIsNone(doc["subject"])

    def test_invalid_call_raises_instead_of_producing_a_bad_doc(self):
        bad = _valid_call(considered=[])
        with self.assertRaises(ValueError):
            capital_call_doc(bad)


if __name__ == "__main__":
    unittest.main()
