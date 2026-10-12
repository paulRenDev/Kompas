import base64
import pathlib
import unittest

from kompas.pijler_b.cycle import run_cycle_csv
from kompas.pijler_b.export import decode_export

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "aandelen_live_sample.csv"


class TestDecodeExport(unittest.TestCase):
    def setUp(self):
        self.csv = FIXTURE.read_text(encoding="utf-8")
        self.b64 = base64.b64encode(self.csv.encode("utf-8")).decode("ascii")

    def test_clean_copy_roundtrips(self):
        d = decode_export(self.b64)
        self.assertEqual(d.text, self.csv)
        self.assertFalse(d.truncated)

    def test_stray_whitespace_is_harmless(self):
        messy = " ".join(self.b64[i:i + 60] for i in range(0, len(self.b64), 60)) + "\n"
        d = decode_export(messy)
        self.assertEqual(d.text, self.csv)
        self.assertFalse(d.truncated)

    def test_lost_tail_is_flagged_and_positions_still_reconcile(self):
        # lose the last ~15% of the copy: the watchlist end, not the positions
        cut = self.b64[: int(len(self.b64) * 0.85) - 1]
        d = decode_export(cut)
        self.assertTrue(d.truncated)
        full = run_cycle_csv(self.csv)
        short = run_cycle_csv(d.text, include_watchlist=False)
        self.assertTrue(short.reconciliation.ok)
        self.assertEqual(len(short.snapshot.positions), len(full.snapshot.positions))
        paths = [doc["path"] for doc in short.write_batch]
        self.assertFalse(any(p.startswith("watchlist/") for p in paths))
        self.assertTrue(any(p.startswith("wallet-positions/") for p in paths))


if __name__ == "__main__":
    unittest.main()
