import unittest

from kompas.core.sell_proposal import DERISK_PLAN, Leg, SellProposal, derisk_legs, validate_sell_proposal
from kompas.db.kompas_db import sell_proposal_doc

WALLET = {"IWDA": 4065.0, "IWVL": 862.0, "NUCL": 772.0}


def _p(**o):
    sell, buy = derisk_legs(WALLET)
    d = dict(source="plan", sell=sell, buy=buy, reasoning="Monitor op alarm.", costs="Beurstaks 0,12% per kant.",
             undo=DERISK_PLAN["re_entry"], observed_at="2026-11-02T16:30:00+00:00")
    d.update(o)
    return SellProposal(**d)


class TestDerisk(unittest.TestCase):
    def test_plan_moves_a_third_of_iwda_half_value_half_gold(self):
        sell, buy = derisk_legs(WALLET)
        self.assertEqual(sell, [Leg("IWDA", 1355.0)])
        self.assertEqual({l.ticker: l.amount_eur for l in buy}, {"IWVL": 677.5, "PPFB": 677.5})

    def test_valid_plan_proposal_serializes(self):
        doc = sell_proposal_doc(_p(), WALLET)
        self.assertEqual(doc["path"], "sell_proposals/2026-11-02")


class TestValidate(unittest.TestCase):
    def test_cannot_sell_more_than_held(self):
        self.assertFalse(validate_sell_proposal(_p(sell=[Leg("IWDA", 5000.0)], buy=[]), WALLET).ok)

    def test_cannot_buy_more_than_sold(self):
        self.assertFalse(validate_sell_proposal(_p(buy=[Leg("IWVL", 2000.0)]), WALLET).ok)

    def test_costs_must_be_named(self):
        self.assertFalse(validate_sell_proposal(_p(costs=" "), WALLET).ok)

    def test_broken_thesis_needs_a_signal(self):
        p = _p(source="these_breuk", sell=[Leg("NUCL", 300.0)], buy=[])
        self.assertFalse(validate_sell_proposal(p, WALLET).ok)
        self.assertTrue(validate_sell_proposal(_p(source="these_breuk", sell=[Leg("NUCL", 300.0)], buy=[],
                                                  signal_refs=["kazatomprom-..."]), WALLET).ok)


if __name__ == "__main__":
    unittest.main()
