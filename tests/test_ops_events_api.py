import json
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from ops_events_api import build_ops_import_payload, collect_unknown_items_report, upload_events_to_ops


STANDARD_EVENT = {
    "event_order": "528954",
    "quote": "M-TEST123",
    "date": "April 07, 2026",
    "organization": "Siemens Healthineers",
    "beo": {
        "type": "original",
        "revision_number": 0,
        "file_name": "sample.pdf",
        "page_start": 13,
        "page_end": 13,
    },
    "service": {
        "function": "Meeting",
        "category": "break",
        "subtype": "Meeting",
        "meal_period": "break",
        "time": {
            "start": "12:00 PM",
            "end": "5:00 PM",
        },
        "room": "Executive Boardroom",
        "gtd": 12,
        "menu_style": "",
    },
    "timeline": {
        "setup": "11:20 AM",
        "pickup_food": "11:10 AM",
        "service_start": "12:00 PM",
        "service_end": "5:00 PM",
        "clean_up": "5:40 PM",
    },
    "details": {
        "raw": "12:00 PM Meeting Executive Boardroom",
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
    "source_trace": {
        "page_ranges": ["13"],
        "text_snippets": ["12:00 PM Meeting Executive Boardroom"],
        "confidence": "high",
    },
}


class FakeResponse:
    def __init__(self, status: int, body: dict):
        self.status = status
        self._body = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OpsEventsApiTests(unittest.TestCase):
    def test_build_payload_normalizes_standard_event(self) -> None:
        payload = build_ops_import_payload(
            [STANDARD_EVENT],
            source_file=r"C:\imports\sample.pdf",
            job_id="job-123",
        )
        self.assertEqual(payload["source_system"], "beo_generator")
        self.assertEqual(payload["meta"]["job_id"], "job-123")
        self.assertEqual(payload["meta"]["source_file"], r"C:\imports\sample.pdf")
        event = payload["events"][0]
        self.assertEqual(event["status"], "on_time")
        self.assertEqual(event["date"], "2026-04-07")
        self.assertEqual(event["service"]["time"]["start"], "12:00")
        self.assertEqual(event["service"]["time"]["end"], "17:00")
        self.assertEqual(event["source_trace"]["generator"], "external-beo")
        self.assertEqual(event["source_trace"]["document_id"], "528954")
        self.assertEqual(event["source_trace"]["file_name"], "sample.pdf")
        self.assertEqual(event["quote"], "M-TEST123")
        self.assertEqual(event["identity"]["event_family_key"], "M-TEST123|528954|2026-04-07")
        self.assertTrue(event["identity"]["event_instance_key"].startswith("528954|"))
        self.assertLessEqual(len(event["identity"]["event_instance_key"]), 32)
        self.assertEqual(event["revision_context"]["beo_type"], "original")
        self.assertEqual(event["revision_context"]["revision_number"], 0)
        self.assertFalse(event["revision_context"]["is_revision"])
        self.assertEqual(event["beo_page_start"], 13)
        self.assertEqual(event["beo_page_end"], 13)
        self.assertEqual(event["beo"]["file_name"], "sample.pdf")
        self.assertEqual(
            event["revision_context"]["document_version_key"],
            "528954|original|0|sample.pdf",
        )

    @patch.dict(
        os.environ,
        {
            "OPS_EVENTS_API_BASE_URL": "https://ops.example.com",
            "OPS_EVENTS_API_TOKEN": "secret-token",
            "OPS_EVENTS_API_ENABLED": "true",
        },
        clear=False,
    )
    @patch("ops_events_api.request.urlopen")
    def test_upload_events_to_ops_posts_expected_payload(self, mocked_urlopen) -> None:
        mocked_urlopen.side_effect = [
            FakeResponse(
                201,
                {
                    "id": "beo-doc-123",
                    "file_name": "sample.pdf",
                    "file_url": "https://ops.example.com/files/sample.pdf",
                    "document_type": "original",
                    "revision_number": 0,
                },
            ),
            FakeResponse(202, {"result": "accepted"}),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
            result = upload_events_to_ops(
                [STANDARD_EVENT],
                source_file=str(pdf_path),
                job_id="job-456",
            )

        self.assertTrue(result.attempted)
        self.assertTrue(result.success)
        upload_req = mocked_urlopen.call_args_list[0].args[0]
        import_req = mocked_urlopen.call_args_list[1].args[0]
        import_body = json.loads(import_req.data.decode("utf-8"))
        upload_body = upload_req.data.decode("utf-8", errors="replace")
        self.assertEqual(upload_req.full_url, "https://ops.example.com/api/v1/beo-documents")
        self.assertEqual(import_req.full_url, "https://ops.example.com/api/v1/events/import")
        self.assertEqual(import_req.get_header("Authorization"), "Bearer secret-token")
        self.assertIn('name="document_type"', upload_body)
        self.assertIn("original", upload_body)
        self.assertIn('name="revision_number"', upload_body)
        self.assertIn('name="metadata[source_path]"', upload_body)
        self.assertIn('name="metadata[extractor_version]"', upload_body)
        self.assertIn('name="metadata[detected_label]"', upload_body)
        self.assertIn('name="metadata[original_filename]"', upload_body)
        self.assertIn("sample.pdf", upload_body)
        self.assertEqual(import_body["meta"]["job_id"], "job-456")
        self.assertEqual(import_body["events"][0]["service"]["time"]["start"], "12:00")
        self.assertEqual(import_body["events"][0]["beo_document_id"], "beo-doc-123")
        self.assertEqual(import_body["events"][0]["beo_page_start"], 13)
        self.assertEqual(import_body["events"][0]["beo"]["file_name"], "sample.pdf")
        self.assertTrue(import_body["events"][0]["identity"]["event_instance_key"].startswith("528954|"))

    def test_build_payload_sanitizes_bad_room_and_shortens_identity_key(self) -> None:
        broken_event = {
            **STANDARD_EVENT,
            "service": {
                **STANDARD_EVENT["service"],
                "room": "Steel Cut Carolina Ballroom 7:00 AM Breakfast Buffet The Uptown Assorted Danish, Croissants, Biscuits "
                "Strawberry + Apricot Jam Scrambled Eggs Applewood Smoked Thick Cut Bacon Rosemary Roasted Potatoes",
            },
            "details": {
                **STANDARD_EVENT["details"],
                "raw": "7:00 AM Breakfast Buffet Carolina Ballroom\nThe Uptown\nAssorted Danish, Croissants, Biscuits",
            },
        }
        payload = build_ops_import_payload([broken_event], source_file="broken.pdf")
        event = payload["events"][0]
        self.assertEqual(event["service"]["room"], "Carolina Ballroom")
        self.assertLessEqual(len(event["identity"]["event_instance_key"]), 32)

    def test_build_payload_derives_page_bounds_from_source_trace(self) -> None:
        event_without_explicit_pages = {
            **STANDARD_EVENT,
            "beo": {
                "type": "revision",
                "revision_number": 2,
            },
            "source_trace": {
                **STANDARD_EVENT["source_trace"],
                "page_ranges": ["3-4"],
            },
        }

        payload = build_ops_import_payload([event_without_explicit_pages], source_file="sample.pdf")

        event = payload["events"][0]
        self.assertEqual(event["beo_page_start"], 3)
        self.assertEqual(event["beo_page_end"], 4)
        self.assertEqual(event["beo"]["page_start"], 3)
        self.assertEqual(event["beo"]["page_end"], 4)
        self.assertEqual(event["beo"]["revision_number"], 2)

    def test_build_payload_backfills_missing_room_from_sibling_event(self) -> None:
        earlier_dinner = {
            **STANDARD_EVENT,
            "event_order": "531128",
            "date": "May 09, 2026",
            "organization": "CLTWS in House Account",
            "service": {
                **STANDARD_EVENT["service"],
                "function": "Dinner",
                "time": {"start": "7:00 PM", "end": None},
                "room": "Symphony Ballroom",
            },
        }
        later_dinner_missing_room = {
            **STANDARD_EVENT,
            "event_order": "531128",
            "date": "May 09, 2026",
            "organization": "CLTWS in House Account",
            "service": {
                **STANDARD_EVENT["service"],
                "function": "Dinner",
                "time": {"start": "8:00 PM", "end": None},
                "room": None,
            },
            "details": {
                **STANDARD_EVENT["details"],
                "raw": "8:00 PM Dinner\n(350) Chicken Tenders @ $8 Each",
            },
        }

        payload = build_ops_import_payload([earlier_dinner, later_dinner_missing_room], source_file="sample.pdf")

        self.assertEqual(payload["events"][1]["service"]["room"], "Symphony Ballroom")

    def test_upload_events_to_ops_skips_when_unknown_items_remain(self) -> None:
        unresolved_event = {
            **STANDARD_EVENT,
            "details": {
                **STANDARD_EVENT["details"],
                "menu_sections": [
                    {
                        "title": "Buffet",
                        "operational_split": {
                            "hot_kitchen_items": [],
                            "cold_kitchen_items": [],
                            "dietary_items": [],
                            "unknown_items": ["Mystery Item"],
                        },
                    }
                ],
            },
        }

        result = upload_events_to_ops([unresolved_event], source_file="sample.pdf", job_id="job-unknown")

        self.assertFalse(result.attempted)
        self.assertFalse(result.success)
        self.assertIn("Mystery Item", result.message)

    def test_collect_unknown_items_report_groups_occurrences(self) -> None:
        unresolved_event = {
            **STANDARD_EVENT,
            "service": {
                **STANDARD_EVENT["service"],
                "function": "Buffet Lunch",
                "room": "Grand Ballroom",
            },
            "details": {
                **STANDARD_EVENT["details"],
                "menu_sections": [
                    {
                        "title": "Buffet",
                        "type": "course",
                        "course_type": "other",
                        "items": [
                            {"name": "Mystery Item", "source_text": "Mystery Item @ $12"},
                        ],
                        "operational_split": {
                            "hot_kitchen_items": [],
                            "cold_kitchen_items": [],
                            "dietary_items": [],
                            "unknown_items": ["Mystery Item"],
                        },
                    }
                ],
            },
        }

        report = collect_unknown_items_report([unresolved_event])

        self.assertEqual(report["total_unique_unknown_items"], 1)
        self.assertIn("Mystery Item", report["items"])
        mystery = report["items"]["Mystery Item"]
        self.assertEqual(mystery["temperature_zone"], "unknown")
        self.assertIsNone(mystery["suggested_route"])
        self.assertEqual(
            mystery["occurrences"][0],
            {
                "event_order": "528954",
                "date": "April 07, 2026",
                "function": "Buffet Lunch",
                "room": "Grand Ballroom",
                "section_title": "Buffet",
                "section_type": "course",
                "course_type": "other",
                "source_text": "Mystery Item @ $12",
            },
        )

    @patch.dict(
        os.environ,
        {
            "OPS_EVENTS_API_BASE_URL": "https://ops.example.com",
            "OPS_EVENTS_API_TOKEN": "secret-token",
            "OPS_EVENTS_API_ENABLED": "true",
        },
        clear=False,
    )
    @patch("ops_events_api.request.urlopen")
    def test_upload_events_to_ops_handles_http_error(self, mocked_urlopen) -> None:
        mocked_urlopen.side_effect = [
            FakeResponse(
                201,
                {
                    "id": "beo-doc-123",
                    "file_name": "sample.pdf",
                    "file_url": "https://ops.example.com/files/sample.pdf",
                    "document_type": "original",
                    "revision_number": 0,
                },
            ),
            HTTPError(
                url="https://ops.example.com/api/v1/events/import",
                code=422,
                msg="unprocessable",
                hdrs=None,
                fp=BytesIO(b'{\"message\":\"invalid payload\"}'),
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
            result = upload_events_to_ops([STANDARD_EVENT], source_file=str(pdf_path), job_id="job-789")
        self.assertTrue(result.attempted)
        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.response_body["message"], "invalid payload")
        self.assertEqual(result.beo_document["id"], "beo-doc-123")
