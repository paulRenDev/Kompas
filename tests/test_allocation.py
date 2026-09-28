import unittest

from kompas.core.allocation import AllocationView, Sleeve, sleeve_status, validate_allocation
from kompas.core.synthesis import RedTeamChallenge
from kompas.db.kompas_db import allocation_view_doc


def _view(**overrides) -> AllocationView:
    defaults = dict(
        sleeves=[
            Sleeve("Kern", 55, 60, ["CORE"], "Goedkoopste spreiding."),
            Sleeve("Energietransitie", 15, 20, ["NUC", "CLN"], "Structureel thema."),
            Sleeve("Defensief", 20, 30, ["STPL"], "Demping."),
        ],
        narrative="Kern met twee kantelingen.",
        red_team=RedTeamChallenge(objection="Energie is renteonder gevoelig.", survives=True),
        trigger="Heroverweeg bij een nieuwe positie.",
        observed_at="2026-09-28T19:00:00+00:00",
    )
    defaults.update(overrides)
    return AllocationView(**defaults)


class TestValidateAllocation(unittest.TestCase):
    def test_valid_view_passes_and_serializes(self):
        self.assertTrue(validate_allocation(_view()).ok)
        doc = allocation_view_doc(_view())
        self.assertEqual(doc["path"], "allocation_views/2026-09-28")
        self.assertEqual(doc["sleeves"][1]["holdings"], ["NUC", "CLN"])

    def test_ranges_that_cannot_reach_100_rejected(self):
        view = _view(sleeves=[Sleeve("Kern", 40, 50, ["CORE"], "x"), Sleeve("Rest", 10, 20, ["B"], "y")])
        self.assertFalse(validate_allocation(view).ok)

    def test_ticker_in_two_sleeves_rejected(self):
        view = _view(sleeves=[Sleeve("A", 50, 60, ["X"], "x"), Sleeve("B", 40, 50, ["X"], "y")])
        self.assertTrue(any("twee sleeves" in e for e in validate_allocation(view).errors))

    def test_empty_red_team_rejected(self):
        with self.assertRaises(ValueError):
            allocation_view_doc(_view(red_team=RedTeamChallenge(objection=" ", survives=True)))

    def test_minimum_without_holdings_rejected(self):
        view = _view(sleeves=[Sleeve("Kern", 90, 100, ["CORE"], "x"), Sleeve("EM", 5, 10, [], "y")])
        self.assertFalse(validate_allocation(view).ok)


class TestSleeveStatus(unittest.TestCase):
    def test_weights_status_and_unassigned(self):
        values = {"CORE": 580.0, "NUC": 75.0, "CLN": 70.0, "STPL": 250.0, "NEW": 25.0}
        status, unassigned = sleeve_status(_view(), values)
        by_name = {s.name: s for s in status}
        self.assertEqual(by_name["Kern"].weight_pct, 58.0)
        self.assertEqual(by_name["Kern"].status, "binnen")
        self.assertEqual(by_name["Energietransitie"].weight_pct, 14.5)
        self.assertEqual(by_name["Energietransitie"].status, "onder")
        self.assertEqual(by_name["Defensief"].status, "binnen")
        self.assertEqual(unassigned, ["NEW"])


if __name__ == "__main__":
    unittest.main()
