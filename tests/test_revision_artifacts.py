import unittest

from revision_artifacts import build_revision_artifacts, resolve_events_output_path


BASE_EVENT = {
    "event_order": "922139",
    "quote": "M-VI2KJPN",
    "date": "April 12, 2026",
    "organization": "American College of Physicians Advisors",
    "beo": {
        "type": "original",
        "revision_number": 0,
    },
    "service": {
        "function": "Break",
        "category": "break",
        "subtype": "Break",
        "meal_period": "break",
        "time": {
            "start": "7:00 AM",
            "end": "5:30 PM",
        },
        "room": "Governor's 2 & 3",
        "gtd": 10,
        "menu_style": "Assorted Bags of",
    },
    "timeline": {
        "setup": "6:30 AM",
        "pickup_food": "6:10 AM",
        "service_start": "7:00 AM",
        "service_end": "5:30 PM",
        "clean_up": "6:10 PM",
    },
    "details": {
        "raw": "7:00 AM Break Governor's 2 & 3",
        "menu_sections": [],
        "menu_fingerprint": "fp-001",
    },
    "setup": {
        "breakdown_station": {},
        "service_equipment": [],
        "rule_trace": {},
    },
    "staffing": {},
    "notes": [],
    "tags": [],
    "source_trace": {},
}


class RevisionArtifactsTests(unittest.TestCase):
    def test_resolve_output_path_routes_revisions_to_subfolder(self) -> None:
        original_path = resolve_events_output_path(r"C:\imports\4.12.26 - 4.19.26 EOs.pdf")
        revision_path = resolve_events_output_path(r"C:\imports\4.12.26 - 4.19.26 EOs revised x2.pdf")
        popup_path = resolve_events_output_path(r"C:\imports\4.12.26 - 4.19.26 EOs popup x1.pdf")

        self.assertEqual(original_path, r"ready_to_print\json\4.12.26 - 4.19.26 EOs_events.json")
        self.assertEqual(revision_path, r"ready_to_print\json\revisions\4.12.26 - 4.19.26 EOs revised x2_events.json")
        self.assertEqual(popup_path, r"ready_to_print\json\revisions\4.12.26 - 4.19.26 EOs popup x1_events.json")

    def test_build_revision_artifacts_matches_revision_when_time_changes(self) -> None:
        morning_break = {
            **BASE_EVENT,
            "service": {
                **BASE_EVENT["service"],
                "time": {
                    "start": "10:00 AM",
                    "end": "10:45 AM",
                },
            },
            "details": {
                **BASE_EVENT["details"],
                "raw": "10:00 AM Break Governor's 2 & 3",
            },
        }
        afternoon_break = {
            **BASE_EVENT,
            "service": {
                **BASE_EVENT["service"],
                "time": {
                    "start": "2:15 PM",
                    "end": "2:45 PM",
                },
                "gtd": 175,
            },
            "details": {
                **BASE_EVENT["details"],
                "raw": "2:15 PM Break Governor's 2 & 3",
                "menu_fingerprint": "fp-002",
            },
        }
        baseline_events = [morning_break, afternoon_break]
        updated_event = {
            **afternoon_break,
            "beo": {
                "type": "revision",
                "revision_number": 2,
            },
            "service": {
                **afternoon_break["service"],
                "time": {
                    "start": "2:30 PM",
                    "end": "3:00 PM",
                },
                "room": "Carolina D",
                "gtd": 150,
            },
        }
        new_event = {
            **BASE_EVENT,
            "service": {
                **BASE_EVENT["service"],
                "function": "Reception",
                "subtype": "Reception",
                "time": {
                    "start": "6:00 PM",
                    "end": "8:00 PM",
                },
            },
            "details": {
                **BASE_EVENT["details"],
                "raw": "6:00 PM Reception Governor's 2 & 3",
                "menu_fingerprint": "fp-002",
            },
        }

        artifacts = build_revision_artifacts(
            [morning_break, updated_event, new_event],
            source_file=r"C:\imports\event revised x2.pdf",
            baseline_events=baseline_events,
            baseline_source_file=r"C:\imports\event original.pdf",
        )

        self.assertEqual(artifacts["summary"]["updated"], 1)
        self.assertEqual(artifacts["summary"]["inserted"], 1)
        self.assertEqual(artifacts["summary"]["superseded"], 0)
        updated_operation = artifacts["diff"]["updated"][0]
        self.assertIn("service", updated_operation["changed_fields"])
        self.assertIn("beo", updated_operation["changed_fields"])
        self.assertGreaterEqual(updated_operation["match_score"], 45)
        inserted_operation = artifacts["diff"]["inserted"][0]
        self.assertEqual(inserted_operation["event"]["service"]["function"], "Reception")

    def test_build_revision_artifacts_reports_superseded_when_instance_disappears(self) -> None:
        baseline_events = [BASE_EVENT]

        artifacts = build_revision_artifacts(
            [],
            source_file=r"C:\imports\event revision x3.pdf",
            baseline_events=baseline_events,
            baseline_source_file=r"C:\imports\event original.pdf",
        )

        self.assertEqual(artifacts["summary"]["superseded"], 1)
        self.assertEqual(artifacts["upsert_payload"]["operations"][0]["action"], "supersede")

    def test_build_revision_artifacts_treats_popup_as_insert_only(self) -> None:
        baseline_events = [BASE_EVENT]
        popup_event = {
            **BASE_EVENT,
            "beo": {
                "type": "popup",
                "revision_number": 1,
            },
            "service": {
                **BASE_EVENT["service"],
                "function": "Reception",
                "subtype": "Reception",
                "time": {
                    "start": "6:00 PM",
                    "end": "8:00 PM",
                },
            },
        }

        artifacts = build_revision_artifacts(
            [popup_event],
            source_file=r"C:\imports\event popup x1.pdf",
            baseline_events=baseline_events,
            baseline_source_file=r"C:\imports\event original.pdf",
        )

        self.assertEqual(artifacts["summary"]["inserted"], 1)
        self.assertEqual(artifacts["summary"]["updated"], 0)
        self.assertEqual(artifacts["summary"]["superseded"], 0)
