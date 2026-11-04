import unittest

from kompas.core.briefing import (
    BriefItem, Briefing, PulseItem, call_is_stale, call_streak, edition_for_hour, validate_briefing,
)
from kompas.db.kompas_db import briefing_doc


def _b(**o):
    d = dict(edition="ochtend", headline="De Democraten winnen het Huis; de futures zakken.",
             items=[BriefItem("gebeurd", "Huis naar de Democraten.", "CBS News 4/11"),
                    BriefItem("vandaag", "Let op de opening in New York om 15.30.", "draaiboek us_midterms")],
             observed_at="2026-11-04T08:30:00+00:00",
             pulse=[PulseItem("VS 10-jaarsrente", "4,906%", "-6 bp", "Reuters 4/11", "4/11 ochtend")])
    d.update(o)
    return Briefing(**d)


def _call(subject, at):
    return {"subject": subject, "observed_at": at}


class TestBriefing(unittest.TestCase):
    def test_doc_path_and_fields(self):
        doc = briefing_doc(_b())
        self.assertEqual(doc["path"], "briefing/2026-11-04-ochtend")
        self.assertEqual(doc["pulse"][0]["change"], "-6 bp")

    def test_needs_a_vandaag_item(self):
        items = [BriefItem("gebeurd", "a", "b"), BriefItem("betekent", "c", "d")]
        self.assertFalse(validate_briefing(_b(items=items)).ok)

    def test_item_and_pulse_need_a_source(self):
        self.assertFalse(validate_briefing(_b(items=[BriefItem("gebeurd", "a", ""), BriefItem("vandaag", "b", "c")])).ok)
        self.assertFalse(validate_briefing(_b(pulse=[PulseItem("Brent", "115", "", "", "")])).ok)

    def test_headline_bounds(self):
        self.assertFalse(validate_briefing(_b(headline=" ")).ok)
        self.assertFalse(validate_briefing(_b(headline="x" * 200)).ok)

    def test_bad_doc_raises(self):
        with self.assertRaises(ValueError):
            briefing_doc(_b(edition="nacht"))

    def test_edition_for_hour(self):
        self.assertEqual([edition_for_hour(h) for h in (7, 11, 16)], ["ochtend", "middag", "avond"])

    def test_call_streak_counts_calendar_days(self):
        calls = [_call("TTE", "2026-11-04T07:40:00Z"), _call("TTE", "2026-10-28T07:10:00Z"),
                 _call("TTE", "2026-10-27T07:08:00Z"), _call("SU", "2026-10-26T16:55:00Z")]
        self.assertEqual(call_streak(calls), ("TTE", 9, "2026-10-27T07:08:00Z"))
        self.assertTrue(call_is_stale(calls))

    def test_fresh_pick_is_day_one(self):
        calls = [_call("SU", "2026-11-04T07:40:00Z"), _call("TTE", "2026-11-03T07:10:00Z")]
        self.assertEqual(call_streak(calls)[1], 1)
        self.assertFalse(call_is_stale(calls))
        self.assertEqual(call_streak([]), ("", 0, ""))


if __name__ == "__main__":
    unittest.main()
