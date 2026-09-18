import unittest

from kompas.pijler_a.freshness import find_prior_signals

EVENTS = [
    {"subject": "Uranium/Nucleair", "role": "Sector specialist – Uranium/Nucleair", "observed_at": "2026-09-16T09:00:00Z", "text": "oud"},
    {"subject": "Uranium/Nucleair", "role": "Sector specialist – Uranium/Nucleair", "observed_at": "2026-09-18T09:00:00Z", "text": "nieuw"},
    {"subject": "ASML", "role": "Technical stock watchers", "observed_at": "2026-09-17T09:00:00Z", "text": "technisch"},
]


class TestFindPriorSignals(unittest.TestCase):
    def test_no_events_is_always_fresh(self):
        self.assertEqual(find_prior_signals([], "Uranium/Nucleair"), [])

    def test_finds_matches_case_insensitive_most_recent_first(self):
        matches = find_prior_signals(EVENTS, "uranium/nucleair")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["text"], "nieuw")  # most recent first
        self.assertEqual(matches[1]["text"], "oud")

    def test_unrelated_subject_returns_nothing(self):
        self.assertEqual(find_prior_signals(EVENTS, "Cameco"), [])

    def test_role_filter_narrows_the_match(self):
        matches = find_prior_signals(EVENTS, "ASML", role="Technical stock watchers")
        self.assertEqual(len(matches), 1)
        matches_wrong_role = find_prior_signals(EVENTS, "ASML", role="Stock watchers")
        self.assertEqual(matches_wrong_role, [])


if __name__ == "__main__":
    unittest.main()
