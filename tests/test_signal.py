import unittest

from kompas.core.signal import CapitalView, Signal, validate_signal


def _base_signal(**overrides) -> Signal:
    defaults = dict(
        role="Sector specialist – Uranium/Nucleair",
        subject="Uranium/Nucleair",
        text="Capex-cyclus versnelt volgens twee onafhankelijke bronnen.",
        source='World Nuclear News, "Utilities accelerate reactor life extensions" (18 sep 2026)',
        source_tier="tier 1",
        magnitude="Raakt CCJ (watchlist), geschat 5-10% van sector-capex-budget herschikt",
        timeframe_horizon="Zichtbaar in Q4-cijfers 2026",
        data_confidence="hoog",
        signal_confidence="voorlopig",
        observed_at="2026-09-18T09:00:00+00:00",
    )
    defaults.update(overrides)
    return Signal(**defaults)


class TestValidateSignal(unittest.TestCase):
    def test_well_formed_signal_passes(self):
        result = validate_signal(_base_signal())
        self.assertTrue(result.ok, msg=result.errors)
        self.assertEqual(result.errors, [])

    def test_category_only_source_rejected(self):
        result = validate_signal(_base_signal(source="sectorpers"))
        self.assertFalse(result.ok)
        self.assertTrue(any("categorie" in e for e in result.errors))

    def test_empty_magnitude_rejected(self):
        result = validate_signal(_base_signal(magnitude=""))
        self.assertFalse(result.ok)
        self.assertIn("omvang ontbreekt", result.errors)

    def test_invalid_signal_confidence_rejected(self):
        result = validate_signal(_base_signal(signal_confidence="zeker"))
        self.assertFalse(result.ok)
        self.assertTrue(any("signaalbetrouwbaarheid" in e for e in result.errors))

    def test_technical_signal_requires_chart_timeframe(self):
        sig = _base_signal(role="Technical stock watchers", chart_timeframe=None)
        result = validate_signal(sig, is_technical=True)
        self.assertFalse(result.ok)
        self.assertTrue(any("timeframe" in e for e in result.errors))

    def test_technical_signal_with_timeframe_passes(self):
        sig = _base_signal(role="Technical stock watchers", chart_timeframe="dag")
        result = validate_signal(sig, is_technical=True)
        self.assertTrue(result.ok, msg=result.errors)

    def test_non_technical_signal_does_not_need_chart_timeframe(self):
        result = validate_signal(_base_signal(chart_timeframe=None), is_technical=False)
        self.assertTrue(result.ok, msg=result.errors)

    def test_no_capital_view_is_fine(self):
        result = validate_signal(_base_signal(capital_view=None))
        self.assertTrue(result.ok, msg=result.errors)

    def test_valid_capital_view_passes(self):
        sig = _base_signal(
            capital_view=CapitalView(
                action="wacht", reasoning="Te vroeg, wacht op bevestiging.",
                trigger="Heroverweeg bij de volgende kwartaalcijfers.",
            )
        )
        result = validate_signal(sig)
        self.assertTrue(result.ok, msg=result.errors)

    def test_capital_view_bad_action_rejected(self):
        sig = _base_signal(capital_view=CapitalView(action="sell_everything", reasoning="x", trigger="y"))
        result = validate_signal(sig)
        self.assertFalse(result.ok)
        self.assertTrue(any("capital_view.action" in e for e in result.errors))

    def test_capital_view_empty_reasoning_rejected(self):
        sig = _base_signal(capital_view=CapitalView(action="wacht", reasoning="   ", trigger="y"))
        result = validate_signal(sig)
        self.assertFalse(result.ok)
        self.assertIn("capital_view.reasoning ontbreekt", result.errors)

    def test_capital_view_empty_trigger_rejected(self):
        sig = _base_signal(capital_view=CapitalView(action="wacht", reasoning="Te vroeg.", trigger="   "))
        result = validate_signal(sig)
        self.assertFalse(result.ok)
        self.assertTrue(any("capital_view.trigger ontbreekt" in e for e in result.errors))

    def test_verhoog_bestaand_requires_a_real_position_tag(self):
        sig = _base_signal(
            capital_view=CapitalView(action="verhoog_bestaand", reasoning="Sterk signaal.", trigger="y"),
            related_positions=[],
            related_watchlist=["CCJ"],
        )
        result = validate_signal(sig)
        self.assertFalse(result.ok)
        self.assertTrue(any("verhoog_bestaand" in e for e in result.errors))

    def test_verhoog_bestaand_with_a_real_position_tag_passes(self):
        sig = _base_signal(
            capital_view=CapitalView(action="verhoog_bestaand", reasoning="Sterk signaal.", trigger="y"),
            related_positions=["NUCL"],
        )
        result = validate_signal(sig)
        self.assertTrue(result.ok, msg=result.errors)

    def test_nieuwe_positie_on_a_speculative_signal_is_rejected(self):
        sig = _base_signal(
            capital_view=CapitalView(action="nieuwe_positie", reasoning="Veelbelovend.", trigger="y"),
            signal_confidence="speculatief",
        )
        result = validate_signal(sig)
        self.assertFalse(result.ok)
        self.assertTrue(any("nieuwe_positie" in e for e in result.errors))

    def test_nieuwe_positie_on_a_voorlopig_signal_passes(self):
        sig = _base_signal(
            capital_view=CapitalView(action="nieuwe_positie", reasoning="Veelbelovend.", trigger="y"),
            signal_confidence="voorlopig",
        )
        result = validate_signal(sig)
        self.assertTrue(result.ok, msg=result.errors)


if __name__ == "__main__":
    unittest.main()
