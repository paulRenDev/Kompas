import unittest

from kompas.core.synthesis import RedTeamChallenge, Synthesis, validate_synthesis


def _valid_synthesis(**overrides) -> Synthesis:
    defaults = dict(
        subject="AMD",
        narrative="Naomi en de sectorspecialist zien een reele groeistory; Mila ziet overbought terrein.",
        signal_ids=["amd-2026-09-22-stock-watchers", "amd-2026-09-22-technical-stock-watchers"],
        red_team=RedTeamChallenge(objection="De rally kan sentiment-gedreven zijn, niet fundamenteel.", survives=True),
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

    def test_relevant_by_default(self):
        s = _valid_synthesis()
        self.assertTrue(s.relevant)
        self.assertIsNone(s.closed_reason)

    def test_not_relevant_without_closed_reason_rejected(self):
        result = validate_synthesis(_valid_synthesis(relevant=False))
        self.assertFalse(result.ok)
        self.assertTrue(any("closed_reason" in e for e in result.errors))

    def test_not_relevant_with_closed_reason_passes(self):
        result = validate_synthesis(_valid_synthesis(relevant=False, closed_reason="Top afgerond."))
        self.assertTrue(result.ok, msg=result.errors)

    def test_default_related_lists_are_independent_empty_lists(self):
        a = _valid_synthesis()
        b = _valid_synthesis()
        self.assertEqual(a.related_positions, [])
        a.related_positions.append("SHOULD_NOT_LEAK")
        self.assertEqual(b.related_positions, [])


if __name__ == "__main__":
    unittest.main()
