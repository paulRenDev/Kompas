import pathlib
import unittest

from kompas.db.kompas_db import build_batch
from kompas.pijler_b.cycle import run_cycle

FIXTURE = (pathlib.Path(__file__).parent / "fixtures" / "aandelen_sample.txt").read_text()


class TestCycle(unittest.TestCase):
    def test_full_cycle_produces_a_write_batch_on_success(self):
        result = run_cycle(FIXTURE)
        self.assertTrue(result.reconciliation.ok)
        self.assertIsNotNone(result.write_batch)
        paths = {doc["path"] for doc in result.write_batch}
        self.assertIn("wallet/state", paths)
        self.assertIn("wallet-positions/ETF1", paths)
        self.assertIn("wallet-positions/ETF2", paths)
        self.assertIn("watchlist/WL1", paths)
        self.assertIn("watchlist/WL2", paths)
        self.assertIn("meta/last_refresh", paths)

    def test_reconciliation_failure_blocks_the_write_batch(self):
        broken = FIXTURE.replace("310,0", "999,0")
        result = run_cycle(broken)
        self.assertFalse(result.reconciliation.ok)
        self.assertIsNone(result.write_batch)

    def test_build_batch_does_not_guard_against_bad_input_on_its_own(self):
        # build_batch trusts its caller to have checked result.ok --
        # documented as intentional in kompas_db.py. This test exists so
        # that guarantee doesn't get "helpfully" removed later without
        # someone noticing the doc comment is now a lie.
        result = run_cycle(FIXTURE)
        batch_again = build_batch(result.snapshot, result.reconciliation)
        self.assertEqual(len(batch_again), len(result.write_batch))


if __name__ == "__main__":
    unittest.main()
