import pathlib
import unittest

from kompas.pijler_b.parser import ParseError, parse_aandelen_dump, parse_number

FIXTURE = (pathlib.Path(__file__).parent / "fixtures" / "aandelen_sample.txt").read_text()


class TestParseNumber(unittest.TestCase):
    def test_plain_euro_amount(self):
        self.assertEqual(parse_number("€ 420,13"), 420.13)

    def test_thousands_separator(self):
        self.assertEqual(parse_number("5.846,0"), 5846.0)

    def test_backslash_escaped_negative(self):
        self.assertEqual(parse_number("\\-€ 55,47"), -55.47)

    def test_percentage(self):
        self.assertEqual(parse_number("1,99%"), 1.99)

    def test_negative_percentage(self):
        self.assertEqual(parse_number("\\-0,14"), -0.14)

    def test_empty_is_none(self):
        self.assertIsNone(parse_number(""))
        self.assertIsNone(parse_number("   "))


class TestParseAandelenDump(unittest.TestCase):
    def setUp(self):
        self.snapshot = parse_aandelen_dump(FIXTURE)

    def test_summary_uses_the_correctly_labelled_row_not_the_decoy(self):
        # The fixture deliberately includes a second, plausible-looking
        # totals-shaped row (999,99 / 888,88 / ... / 12,50%) positioned
        # right after the position rows -- exactly where the real sheet's
        # decoy sat when a human (me) grabbed it by mistake. If the parser
        # ever regresses to picking rows by position instead of by header
        # match, these assertions catch it immediately.
        self.assertEqual(self.snapshot.summary.value_eur, 310.0)
        self.assertEqual(self.snapshot.summary.cost_eur, 300.0)
        self.assertEqual(self.snapshot.summary.gain_eur, 10.0)
        self.assertEqual(self.snapshot.summary.gain_pct, 3.33)

    def test_positions_parsed_and_detail_block_ignored(self):
        # "PORTEFEUILLE DETAIL" further down has its own header
        # (Ticker/ACTIVE/SomethingElse) and must never be read as more
        # position rows.
        self.assertEqual(len(self.snapshot.positions), 2)
        p1, p2 = self.snapshot.positions
        self.assertEqual(p1.ticker, "ETF1")
        self.assertEqual(p1.cost_eur, 100.0)
        self.assertEqual(p1.value_eur, 120.0)
        self.assertEqual(p2.ticker, "ETF2")
        self.assertEqual(p2.gain_eur, -10.0)
        self.assertEqual(p2.gain_pct, -5.0)

    def test_escaped_ampersand_cleaned_in_name(self):
        self.assertIn("Sample World S&P Test ETF - ME-DIRECT", [p.name for p in self.snapshot.positions])

    def test_watchlist_parsed_with_opportunity_cost_semantics(self):
        # setDate/totSetValueEUR must never be confused with
        # purchaseDate/totPurValueEUR -- that mix-up happened for real
        # against the live sheet before this parser existed.
        self.assertEqual(len(self.snapshot.watchlist), 2)
        w1, w2 = self.snapshot.watchlist
        self.assertEqual(w1.ticker, "WL1")
        self.assertEqual(w1.set_date, "01-01-2026")
        self.assertEqual(w1.reference_value_eur, 50.0)
        self.assertEqual(w1.opportunity_gain_pct, 20.0)
        self.assertEqual(w2.ticker, "WL2")
        self.assertEqual(w2.opportunity_gain_eur, -8.0)

    def test_missing_header_raises_parse_error_not_silent_wrong_data(self):
        with self.assertRaises(ParseError):
            parse_aandelen_dump("no headers in here at all\njust text\n")


if __name__ == "__main__":
    unittest.main()
