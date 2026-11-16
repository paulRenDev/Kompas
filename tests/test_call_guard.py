import unittest

from kompas.core.call_guard import CallGuard, guard_errors, playbook_blocks, prior_attempts

FED = {"key": "fed_verhoogt_harder", "status": "naderend",
       "protect": [{"action": "mijd", "what": "NUCL", "why": "rente"}], "opportunity": []}
CALLS = [{"subject": "NUCL — VanEck", "observed_at": "2026-09-28T16:16:00+00:00"},
         {"subject": "IWDA", "observed_at": "2026-09-30T17:25:00+00:00"},
         {"subject": "NUCL — VanEck", "observed_at": "2026-10-04T07:40:00+00:00"},
         {"subject": "WIRE", "observed_at": "2026-10-05T07:40:00+00:00"},
         {"subject": "VanEck Uranium (NUCL, Parijs)", "observed_at": "2026-11-08T07:05:00+00:00"},
         {"subject": "ENR", "observed_at": "2026-11-11T07:15:00+00:00"}]


def _g(**o):
    d = dict(ticker="NUCL", is_fund=True, dip_call=True, floor_days=0, floor_source="",
             thesis_share=0.55, look_through="uranium 55%; de rest zijn reactorbouwers op AI-sentiment (factsheet 30/9)")
    d.update(o)
    return CallGuard(**d)


class TestCallGuard(unittest.TestCase):
    def test_playbook_mijd_blocks(self):
        self.assertEqual(playbook_blocks("NUCL", [FED]), ["fed_verhoogt_harder"])
        self.assertEqual(playbook_blocks("IWDA", [FED]), [])
        self.assertEqual(playbook_blocks("NUCL", [dict(FED, status="voorbij")]), [])

    def test_nucl_on_13_11_would_have_been_stopped(self):
        errs = guard_errors(_g(), [FED], CALLS, "2026-11-13")
        self.assertTrue(any("mijd" in e for e in errs))
        self.assertTrue(any("vallend mes" in e for e in errs))
        self.assertTrue(any("scorekaart" in e for e in errs))

    def test_floor_or_resolved_cause_clears_the_knife(self):
        self.assertFalse(any("vallend mes" in e for e in guard_errors(_g(floor_days=5, floor_source="Mila, dagchart"), [], [], "2026-11-13")))
        self.assertFalse(any("vallend mes" in e for e in guard_errors(_g(drop_reason_resolved="Key Lake herstart, Cameco 1/12"), [], [], "2026-11-13")))

    def test_fund_needs_look_through(self):
        self.assertTrue(guard_errors(_g(dip_call=False, thesis_share=None, look_through=""), [], [], "2026-11-13"))
        self.assertFalse(guard_errors(_g(dip_call=False), [], [], "2026-11-13"))

    def test_prior_attempts_excludes_the_running_idea(self):
        # 13/11, a new NUCL idea: 28/9, 4/10 and 8/11 came before it.
        self.assertEqual(len(prior_attempts("NUCL", CALLS, "2026-11-13")), 3)
        # 9/11, while the 8/11 idea is still the running one: only 28/9 and 4/10.
        self.assertEqual(prior_attempts("NUCL", CALLS[:5], "2026-11-09"),
                         ["2026-09-28T16:16:00+00:00", "2026-10-04T07:40:00+00:00"])


if __name__ == "__main__":
    unittest.main()
