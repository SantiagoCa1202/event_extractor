import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from ops_events_api import build_ops_import_payload, upload_events_to_ops


STANDARD_EVENT = {
    "event_order": "528954",
    "quote": "M-TEST123",
    "date": "April 07, 2026",
    "organization": "Siemens Healthineers",
    "beo": {
        "type": "original",
        "revision_number": 0,
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
        mocked_urlopen.return_value = FakeResponse(202, {"result": "accepted"})
        result = upload_events_to_ops(
            [STANDARD_EVENT],
            source_file=r"C:\imports\sample.pdf",
            job_id="job-456",
        )

        self.assertTrue(result.attempted)
        self.assertTrue(result.success)
        req = mocked_urlopen.call_args.args[0]
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(req.full_url, "https://ops.example.com/api/v1/events/import")
        self.assertEqual(req.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(body["meta"]["job_id"], "job-456")
        self.assertEqual(body["events"][0]["service"]["time"]["start"], "12:00")
        self.assertTrue(body["events"][0]["identity"]["event_instance_key"].startswith("528954|"))

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
        mocked_urlopen.side_effect = HTTPError(
            url="https://ops.example.com/api/v1/events/import",
            code=422,
            msg="unprocessable",
            hdrs=None,
            fp=BytesIO(b'{\"message\":\"invalid payload\"}'),
        )
        result = upload_events_to_ops([STANDARD_EVENT], source_file="sample.pdf", job_id="job-789")
        self.assertTrue(result.attempted)
        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.response_body["message"], "invalid payload")
