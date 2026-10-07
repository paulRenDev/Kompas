import unittest

from kompas.core.capital_call import CapitalCall, validate_capital_call
from kompas.core.signal import CapitalView


def _valid_call(**overrides) -> CapitalCall:
    defaults = dict(
        capital_view=CapitalView(
            action="wacht",
            reasoning="Geen van de vandaag afgewogen subjecten haalt de lat.",
            trigger="Heroverweeg bij een duidelijke koersdaling op een van de watchlist-namen.",
        ),
        observed_at="2026-09-24T16:15:00+00:00",
        considered=["MP Materials", "Taiwan-wapenpakket", "Elia energie-eiland"],
    )
    defaults.update(overrides)
    return CapitalCall(**defaults)


class TestValidateCapitalCall(unittest.TestCase):
    def test_well_formed_wacht_call_passes(self):
        result = validate_capital_call(_valid_call())
        self.assertTrue(result.ok, msg=result.errors)

    def test_wacht_needs_no_subject(self):
        call = _valid_call()
        self.assertIsNone(call.subject)
        self.assertTrue(validate_capital_call(call).ok)

    def test_empty_considered_rejected(self):
        result = validate_capital_call(_valid_call(considered=[]))
        self.assertFalse(result.ok)
        self.assertTrue(any("considered" in e for e in result.errors))

    def test_bad_action_rejected(self):
        result = validate_capital_call(_valid_call(
            capital_view=CapitalView(action="sell_everything", reasoning="x", trigger="y"),
        ))
        self.assertFalse(result.ok)
        self.assertTrue(any("capital_view.action" in e for e in result.errors))

    def test_empty_trigger_rejected(self):
        result = validate_capital_call(_valid_call(
            capital_view=CapitalView(action="wacht", reasoning="x", trigger="  "),
        ))
        self.assertFalse(result.ok)
        self.assertTrue(any("capital_view.trigger ontbreekt" in e for e in result.errors))

    def test_nieuwe_positie_without_subject_rejected(self):
        result = validate_capital_call(_valid_call(
            capital_view=CapitalView(action="nieuwe_positie", reasoning="x", trigger="y"),
            subject=None,
        ))
        self.assertFalse(result.ok)
        self.assertTrue(any("subject" in e for e in result.errors))

    def test_nieuwe_positie_with_subject_passes(self):
        result = validate_capital_call(_valid_call(
            capital_view=CapitalView(action="nieuwe_positie", reasoning="x", trigger="y"),
            subject="MP Materials",
        ))
        self.assertTrue(result.ok, msg=result.errors)



def _buy(subject, reasoning="Koper via de mijnen."):
    return _valid_call(
        capital_view=CapitalView(action="nieuwe_positie", reasoning=reasoning, trigger="Vervalt bij een akkoord."),
        subject=subject,
    )


class TestUntradable(unittest.TestCase):
    def test_untradable_subject_rejected(self):
        result = validate_capital_call(_buy("COPX — Global X Copper Miners UCITS ETF"))
        self.assertFalse(result.ok)
        self.assertTrue(any("niet verhandelbaar" in e for e in result.errors))

    def test_untradable_isin_in_reasoning_rejected(self):
        self.assertFalse(validate_capital_call(_buy("Koper", "Via IE0003Z9E2Y3.")).ok)

    def test_tradable_alternative_passes_even_if_it_mentions_copx_ticker(self):
        call = _buy("COPM — iShares Copper Miners UCITS ETF", "In plaats van COPX, die je niet kunt kopen.")
        self.assertTrue(validate_capital_call(call).ok)


if __name__ == "__main__":
    unittest.main()
