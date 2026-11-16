import unittest

from kompas.core.scorecard import CallScore, PlaybookScore, call_ideas, call_verdict, validate_call_score
from kompas.db.kompas_db import call_score_doc, playbook_score_doc


def _cs(**o):
    d = dict(idea="2026-10-27t07-08-00z", subject="TotalEnergies", given_at="2026-10-27T07:08:00+00:00",
             horizon_days=7, change_pct=3.1, bench_change_pct=-0.4, prices="TTE 80,1 -> 82,6; IWDA ...",
             source="Euronext, iShares", scored_at="2026-11-16T09:00:00+00:00")
    d.update(o)
    return CallScore(**d)


class TestScorecard(unittest.TestCase):
    def test_verdict_against_iwda(self):
        self.assertEqual(call_verdict(3.1, -0.4), "beter")
        self.assertEqual(call_verdict(1.0, 0.0), "gelijk")
        self.assertEqual(call_verdict(-3.0, 0.0), "slechter")
        self.assertEqual(call_verdict(None, 0.0), "onbekend")

    def test_doc(self):
        doc = call_score_doc(_cs())
        self.assertEqual(doc["path"], "scorecard/call-2026-10-27t07-08-00z-7d")
        self.assertEqual(doc["verdict"], "beter")

    def test_known_score_needs_prices_and_source(self):
        self.assertFalse(validate_call_score(_cs(prices="", source="")).ok)
        self.assertTrue(validate_call_score(_cs(change_pct=None, prices="", source="")).ok)
        self.assertFalse(validate_call_score(_cs(horizon_days=10)).ok)

    def test_one_idea_per_run(self):
        calls = [{"subject": "TTE", "observed_at": "2026-11-03"}, {"subject": "SU", "observed_at": "2026-10-26"},
                 {"subject": "TTE", "observed_at": "2026-10-27"}, {"subject": "TTE", "observed_at": "2026-10-28"}]
        self.assertEqual([c["observed_at"] for c in call_ideas(calls)], ["2026-10-26", "2026-10-27"])

    def test_playbook_score(self):
        doc = playbook_score_doc(PlaybookScore("us_midterms", "Trump verliest", "uitgekomen", 3,
                                               "Huis naar de Democraten; Nasdaq-futures -2%", "CBS", "2026-11-16T09:00:00+00:00"))
        self.assertEqual(doc["path"], "scorecard/draaiboek-us_midterms")
        with self.assertRaises(ValueError):
            playbook_score_doc(PlaybookScore("x", "y", "misschien", 3, "z", "s", "t"))


if __name__ == "__main__":
    unittest.main()
