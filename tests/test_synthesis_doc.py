import unittest

from kompas.core.synthesis import RedTeamChallenge, Synthesis
from kompas.db.kompas_db import synthesis_doc


def _valid_synthesis(**overrides) -> Synthesis:
    defaults = dict(
        subject="AMD",
        narrative="Fundamenteel en sectorbreed sterk, technisch overbought.",
        signal_ids=["amd-2026-09-22-stock-watchers", "amd-2026-09-22-technical-stock-watchers"],
        red_team=RedTeamChallenge(objection="Sentiment-gedreven rally, geen echte fundamentele trigger vandaag.", survives=True),
        observed_at="2026-09-22T09:00:00+00:00",
        related_watchlist=["AMD"],
    )
    defaults.update(overrides)
    return Synthesis(**defaults)


class TestSynthesisDoc(unittest.TestCase):
    def test_valid_synthesis_produces_a_path_and_fields(self):
        doc = synthesis_doc(_valid_synthesis())
        self.assertEqual(doc["path"], "synthesis/amd-2026-09-22")
        self.assertEqual(doc["signal_ids"], ["amd-2026-09-22-stock-watchers", "amd-2026-09-22-technical-stock-watchers"])
        self.assertEqual(doc["red_team"]["survives"], True)
        self.assertTrue(doc["relevant"])
        self.assertIsNone(doc["closed_reason"])

    def test_invalid_synthesis_raises_instead_of_producing_a_bad_doc(self):
        bad = _valid_synthesis(signal_ids=["only-one"])
        with self.assertRaises(ValueError):
            synthesis_doc(bad)

    def test_not_relevant_without_reason_also_raises(self):
        bad = _valid_synthesis(relevant=False)
        with self.assertRaises(ValueError):
            synthesis_doc(bad)


if __name__ == "__main__":
    unittest.main()
