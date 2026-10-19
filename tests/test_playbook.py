import unittest

from kompas.core.playbook import (MAX_LIVE, MAX_SHIFT, Move, Playbook, live_count, max_shift_eur,
                                  validate_playbook)
from kompas.core.sell_proposal import Leg, SellProposal, validate_sell_proposal
from kompas.db.kompas_db import playbook_doc, sell_proposal_doc


def _pb(**o):
    d = dict(key="us_midterms", what_if="Trump verliest House en Senaat", when="3/11/2026",
             status="naderend", status_reason="Democraten favoriet voor het Huis", source="Decision Desk HQ 18/10",
             watch=["uitslag 3/11"], protect=[Move("houd", "IWDA", "verdeelde regering")],
             opportunity=[Move("koop", "IWDA", "met nieuw geld bij een dip")], shift_max=0.10,
             undo="terug als de markt de uitslag verteerd heeft", updated_at="2026-10-19T12:00:00+00:00",
             scenario_links=["vertrouwen_vs"])
    d.update(o)
    return Playbook(**d)


WALLET = {"IWDA": 4000.0, "IWVL": 850.0, "GOLD": 450.0, "NUCL": 700.0}


class TestPlaybook(unittest.TestCase):
    def test_valid_playbook_serializes(self):
        doc = playbook_doc(_pb())
        self.assertEqual(doc["path"], "playbooks/us_midterms")
        self.assertEqual(doc["protect"][0]["what"], "IWDA")

    def test_needs_both_protection_and_opportunity(self):
        self.assertFalse(validate_playbook(_pb(protect=[])).ok)
        self.assertFalse(validate_playbook(_pb(opportunity=[])).ok)

    def test_shift_capped(self):
        self.assertFalse(validate_playbook(_pb(shift_max=MAX_SHIFT + 0.01)).ok)

    def test_untradable_instrument_rejected(self):
        self.assertFalse(validate_playbook(_pb(opportunity=[Move("koop", "PPFB", "goud")])).ok)

    def test_unknown_scenario_rejected(self):
        self.assertFalse(validate_playbook(_pb(scenario_links=["marsinvasie"])).ok)

    def test_only_active_playbooks_may_move_money(self):
        self.assertEqual(max_shift_eur(_pb(), WALLET), 0.0)
        self.assertAlmostEqual(max_shift_eur(_pb(status="actief"), WALLET), 0.10 * sum(WALLET.values()))

    def test_live_count_ignores_finished(self):
        self.assertEqual(live_count([_pb(), _pb(key="x", status="voorbij")]), 1)
        self.assertGreater(MAX_LIVE, 0)


class TestPlaybookSale(unittest.TestCase):
    def _sale(self, amount, **o):
        d = dict(source="draaiboek", sell=[Leg("IWDA", amount)], buy=[Leg("GOLD", amount)],
                 reasoning="feit", costs="beurstaks", undo="terug", observed_at="2026-11-04T17:00:00+00:00",
                 signal_refs=["us-midterms-2026-11-04"], playbook="us_midterms")
        d.update(o)
        return SellProposal(**d)

    def test_within_cap_ok(self):
        self.assertTrue(validate_sell_proposal(self._sale(500.0), WALLET).ok)
        self.assertEqual(sell_proposal_doc(self._sale(500.0), WALLET)["playbook"], "us_midterms")

    def test_above_cap_rejected(self):
        self.assertFalse(validate_sell_proposal(self._sale(MAX_SHIFT * sum(WALLET.values()) + 50), WALLET).ok)

    def test_needs_playbook_and_signal(self):
        self.assertFalse(validate_sell_proposal(self._sale(500.0, playbook=""), WALLET).ok)
        self.assertFalse(validate_sell_proposal(self._sale(500.0, signal_refs=[]), WALLET).ok)


if __name__ == "__main__":
    unittest.main()
