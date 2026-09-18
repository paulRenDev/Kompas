import unittest

from kompas.pijler_a.spotlight import (
    cross_specialist_subjects,
    events_with_conflict_notes,
    group_by_role,
    group_by_subject,
    single_role_events,
)


def _event(subject, role, observed_at="2026-09-18T09:00:00Z", **overrides):
    base = {"subject": subject, "role": role, "observed_at": observed_at, "text": "x"}
    base.update(overrides)
    return base


class TestGroupBySubject(unittest.TestCase):
    def test_groups_events_sharing_a_subject(self):
        events = [_event("ASML", "Stock watchers"), _event("ASML", "Technical stock watchers")]
        groups = group_by_subject(events)
        self.assertEqual(len(groups["ASML"]), 2)


class TestCrossSpecialistSubjects(unittest.TestCase):
    def test_single_role_subject_is_not_a_spotlight(self):
        events = [_event("Lanaken datacenter", "Sector specialist – Datacenter-infra")]
        self.assertEqual(cross_specialist_subjects(events), [])

    def test_two_distinct_roles_on_same_subject_is_a_spotlight(self):
        events = [
            _event("ASML", "Sector specialist – Defensie"),
            _event("ASML", "Sector specialist – Halfgeleiders"),
        ]
        self.assertEqual(cross_specialist_subjects(events), ["ASML"])

    def test_same_role_twice_is_not_a_spotlight(self):
        events = [
            _event("ASML", "Stock watchers", observed_at="2026-09-16T09:00:00Z"),
            _event("ASML", "Stock watchers", observed_at="2026-09-18T09:00:00Z"),
        ]
        self.assertEqual(cross_specialist_subjects(events), [])

    def test_most_recently_observed_spotlight_first(self):
        events = [
            _event("Oud onderwerp", "Rol A", observed_at="2026-09-10T09:00:00Z"),
            _event("Oud onderwerp", "Rol B", observed_at="2026-09-10T09:00:00Z"),
            _event("Nieuw onderwerp", "Rol A", observed_at="2026-09-18T09:00:00Z"),
            _event("Nieuw onderwerp", "Rol B", observed_at="2026-09-18T09:00:00Z"),
        ]
        self.assertEqual(cross_specialist_subjects(events), ["Nieuw onderwerp", "Oud onderwerp"])


class TestSingleRoleEvents(unittest.TestCase):
    def test_excludes_spotlight_subjects(self):
        events = [
            _event("ASML", "Sector specialist – Defensie"),
            _event("ASML", "Sector specialist – Halfgeleiders"),
            _event("Lanaken datacenter", "Sector specialist – Datacenter-infra"),
        ]
        result = single_role_events(events)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["subject"], "Lanaken datacenter")


class TestGroupByRole(unittest.TestCase):
    def test_groups_events_by_role(self):
        events = [_event("A", "Trend viewers"), _event("B", "Trend viewers"), _event("C", "Stock watchers")]
        groups = group_by_role(events)
        self.assertEqual(len(groups["Trend viewers"]), 2)
        self.assertEqual(len(groups["Stock watchers"]), 1)


class TestEventsWithConflictNotes(unittest.TestCase):
    def test_only_flagged_events_returned(self):
        events = [
            _event("ASML", "Technical stock watchers", conflict_note="Trendvolgend bearish maar RSI neutraal"),
            _event("Lanaken datacenter", "Sector specialist – Datacenter-infra"),
        ]
        result = events_with_conflict_notes(events)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["subject"], "ASML")

    def test_blank_conflict_note_is_not_flagged(self):
        events = [_event("ASML", "Stock watchers", conflict_note="   ")]
        self.assertEqual(events_with_conflict_notes(events), [])


if __name__ == "__main__":
    unittest.main()
