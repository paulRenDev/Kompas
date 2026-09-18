import pathlib
import unittest
from dataclasses import replace

from kompas.pijler_b.parser import parse_aandelen_dump
from kompas.pijler_b.reconcile import reconcile

FIXTURE = (pathlib.Path(__file__).parent / "fixtures" / "aandelen_sample.txt").read_text()


class TestReconcile(unittest.TestCase):
    def test_happy_path_reconciles(self):
        snapshot = parse_aandelen_dump(FIXTURE)
        result = reconcile(snapshot)
        self.assertTrue(result.ok, msg=f"expected reconciliation to pass, diffs={result.diffs}")
        self.assertEqual(result.computed_value_eur, 310.0)
        self.assertEqual(result.computed_cost_eur, 300.0)
        self.assertEqual(result.computed_gain_eur, 10.0)
        self.assertEqual(result.watchlist_count, 2)

    def test_discrepancy_is_never_silently_accepted(self):
        # Simulate the sheet's summary row disagreeing with the positions
        # (e.g. a stale cache, a manual edit, a parsing bug elsewhere) --
        # this must come back ok=False, never a best-effort average.
        snapshot = parse_aandelen_dump(FIXTURE)
        bad_summary = replace(snapshot.summary, value_eur=snapshot.summary.value_eur + 50)
        bad_snapshot = replace(snapshot, summary=bad_summary)
        result = reconcile(bad_snapshot)
        self.assertFalse(result.ok)
        self.assertAlmostEqual(result.diffs["value_eur"], -50.0, places=2)

    def test_tolerance_absorbs_only_rounding_not_real_gaps(self):
        snapshot = parse_aandelen_dump(FIXTURE)
        tiny_off = replace(snapshot.summary, value_eur=snapshot.summary.value_eur + 0.05)
        ok_snapshot = replace(snapshot, summary=tiny_off)
        self.assertTrue(reconcile(ok_snapshot).ok)

        too_far = replace(snapshot.summary, value_eur=snapshot.summary.value_eur + 0.50)
        bad_snapshot = replace(snapshot, summary=too_far)
        self.assertFalse(reconcile(bad_snapshot).ok)


if __name__ == "__main__":
    unittest.main()
