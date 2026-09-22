import unittest

from kompas.core.signal import CapitalView
from kompas.core.synthesis import RedTeamChallenge, Synthesis, validate_synthesis


def _valid_synthesis(**overrides) -> Synthesis:
    defaults = dict(
        subject="AMD",
        narrative="Naomi en de sectorspecialist zien een reele groeistory; Mila ziet overbought terrein.",
        signal_ids=["amd-2026-09-22-stock-watchers", "amd-2026-09-22-technical-stock-watchers"],
        red_team=RedTeamChallenge(objection="De rally kan sentiment-gedreven zijn, niet fundamenteel.", survives=True),
        capital_view=CapitalView(action="wacht", reasoning="Sterk verhaal, dure entry.", trigger="Heroverweeg bij een correctie."),
        observed_at="2026-09-22T09:00:00+00:00",
    )
    defaults.update(overrides)
    return Synthesis(**defaults)


class TestValidateSynthesis(unittest.TestCase):
    def test_well_formed_synthesis_passes(self):
        result = validate_synthesis(_valid_synthesis())
        self.assertTrue(result.ok, msg=result.errors)

    def test_empty_narrative_rejected(self):
        result = validate_synthesis(_valid_synthesis(narrative="  "))
        self.assertFalse(result.ok)
        self.assertIn("narrative ontbreekt", result.errors)

    def test_fewer_than_two_signal_ids_rejected(self):
        result = validate_synthesis(_valid_synthesis(signal_ids=["only-one"]))
        self.assertFalse(result.ok)
        self.assertTrue(any("minstens 2" in e for e in result.errors))

    def test_empty_red_team_objection_rejected(self):
        result = validate_synthesis(_valid_synthesis(red_team=RedTeamChallenge(objection="  ", survives=True)))
        self.assertFalse(result.ok)
        self.assertTrue(any("red_team.objection" in e for e in result.errors))

    def test_verhoog_bestaand_requires_a_real_position_tag(self):
        result = validate_synthesis(_valid_synthesis(
            capital_view=CapitalView(action="verhoog_bestaand", reasoning="x", trigger="y"),
            related_positions=[],
            related_watchlist=["AMD"],
        ))
        self.assertFalse(result.ok)
        self.assertTrue(any("verhoog_bestaand" in e for e in result.errors))

    def test_verhoog_bestaand_with_a_real_position_tag_passes(self):
        result = validate_synthesis(_valid_synthesis(
            capital_view=CapitalView(action="verhoog_bestaand", reasoning="x", trigger="y"),
            related_positions=["NUCL"],
        ))
        self.assertTrue(result.ok, msg=result.errors)

    def test_default_related_lists_are_independent_empty_lists(self):
        a = _valid_synthesis()
        b = _valid_synthesis()
        self.assertEqual(a.related_positions, [])
        a.related_positions.append("SHOULD_NOT_LEAK")
        self.assertEqual(b.related_positions, [])


if __name__ == "__main__":
    unittest.main()
