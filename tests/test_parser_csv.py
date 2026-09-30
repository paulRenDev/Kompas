import pathlib
import unittest

from kompas.db.kompas_db import build_batch, stale_position_doc_ids
from kompas.pijler_b.cycle import run_cycle_csv
from kompas.pijler_b.parser import parse_aandelen_csv

FIXTURE = (pathlib.Path(__file__).parent / "fixtures" / "aandelen_live_sample.csv").read_text(encoding="utf-8")


class TestParseAandelenCsv(unittest.TestCase):
    def setUp(self):
        self.snapshot = parse_aandelen_csv(FIXTURE)

    def test_summary_from_labelled_row_not_the_decoy_below_it(self):
        s = self.snapshot.summary
        self.assertEqual((s.value_eur, s.cost_eur, s.gain_eur, s.gain_pct), (350.0, 330.0, 20.0, 6.06))

    def test_snapshot_delta_cell_is_not_read_as_day_change(self):
        # The fifth summary cell is the change vs. the sheet's snapshot row,
        # not today's move -- it once got labelled "vandaag" by mistake.
        self.assertFalse(hasattr(self.snapshot.summary, "day_change_eur"))

    def test_positions_with_day_change_and_negative_euro(self):
        core, stpl = self.snapshot.positions
        self.assertEqual((core.ticker, core.qty, core.value_eur, core.day_change_pct), ("CORE", 2.0, 230.0, -0.24))
        self.assertEqual((stpl.gain_eur, stpl.gain_pct, stpl.day_change_pct), (-10.0, -7.69, 1.5))

    def test_ampersand_needs_no_unescaping_in_csv(self):
        self.assertEqual(self.snapshot.positions[1].name, "Sample S&P Staples ETF - ME-DIRECT")

    def test_watchlist_kept_separate_from_positions(self):
        self.assertEqual([w.ticker for w in self.snapshot.watchlist], ["WL1"])
        self.assertNotIn("WL1", [p.ticker for p in self.snapshot.positions])


class TestCsvCycle(unittest.TestCase):
    def test_reconciles_and_builds_weights(self):
        result = run_cycle_csv(FIXTURE)
        self.assertTrue(result.reconciliation.ok, result.reconciliation.diffs)
        docs = {d["path"]: d for d in result.write_batch}
        self.assertEqual(docs["wallet-positions/CORE-AMS"]["weight_pct"], 65.71)
        self.assertEqual(docs["wallet-positions/STPL-EPA"]["day_change_pct"], 1.5)
        # 230 at -0,24% and 120 at +1,50% -> -0,55 + 1,77
        self.assertEqual(docs["wallet/state"]["day_change_eur"], 1.22)
        self.assertNotIn("wallet/targets", docs)

    def test_purchases_since_previous_refresh_are_recorded(self):
        result = run_cycle_csv(FIXTURE, previous_qty={"CORE-AMS": 2.0, "STPL-EPA": 7.0, "SOLD-EPA": 4.0},
                               previous_refreshed_at="2026-09-29T16:49:18+00:00")
        meta = {d["path"]: d for d in result.write_batch}["meta/last_refresh"]
        by_id = {c["doc_id"]: c for c in meta["changes"]}
        self.assertEqual(by_id["STPL-EPA"]["delta"], 3.0)
        self.assertEqual(by_id["SOLD-EPA"]["after"], 0.0)
        self.assertNotIn("CORE-AMS", by_id)
        self.assertEqual(meta["previous_refreshed_at"], "2026-09-29T16:49:18+00:00")

    def test_stale_position_ids_names_sold_positions_only(self):
        snapshot = parse_aandelen_csv(FIXTURE)
        stale = stale_position_doc_ids(["CORE-AMS", "STPL-EPA", "SOLD-EPA"], snapshot)
        self.assertEqual(stale, ["SOLD-EPA"])


if __name__ == "__main__":
    unittest.main()
