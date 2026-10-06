import unittest

from kompas.db.kompas_db import cycle_a_doc


class TestCycleADoc(unittest.TestCase):
    def test_empty_cycle_is_still_recorded(self):
        doc = cycle_a_doc("2026-10-06T07:16:00+00:00", "morning", 0, 0, True, "geen nieuw materieel signaal")
        self.assertEqual(doc["path"], "meta/last_cycle_a")
        self.assertEqual(doc["pijler"], "A")
        self.assertEqual(doc["signals_written"], 0)
        self.assertTrue(doc["call_written"])

    def test_unknown_run_rejected(self):
        with self.assertRaises(ValueError):
            cycle_a_doc("2026-10-06T07:16:00+00:00", "noon", 1, 0, False)


if __name__ == "__main__":
    unittest.main()
