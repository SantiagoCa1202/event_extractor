import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ops_events_api import OpsImportResult

from save_json import save_json


EVENT_WITH_UNKNOWN = {
    "event_order": "528954",
    "quote": "M-TEST123",
    "date": "April 07, 2026",
    "organization": "Siemens Healthineers",
    "beo": {
        "type": "original",
        "revision_number": 0,
    },
    "service": {
        "function": "Buffet Lunch",
        "category": "lunch",
        "subtype": "Buffet",
        "meal_period": "lunch",
        "time": {
            "start": "12:00 PM",
            "end": "1:00 PM",
        },
        "room": "Grand Ballroom",
        "gtd": 12,
        "menu_style": "",
    },
    "timeline": {},
    "details": {
        "raw": "12:00 PM Buffet Lunch Grand Ballroom",
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
                    "non_kitchen_items": [],
                    "unknown_items": ["Mystery Item"],
                },
            }
        ],
        "menu_fingerprint": "fp-001",
    },
    "setup": {},
    "staffing": {},
    "notes": [],
    "tags": [],
    "source_trace": {
        "confidence": "high",
    },
}


class SaveJsonTests(unittest.TestCase):
    @patch("builtins.input", return_value="y")
    @patch("save_json.upload_events_to_ops")
    def test_save_json_writes_unknown_items_review_file(self, mocked_upload, _mocked_input) -> None:
        mocked_upload.return_value = OpsImportResult(False, False, None, "job-unknown", "blocked")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "events.json"

            save_json([EVENT_WITH_UNKNOWN], str(output_path), source_file="sample.pdf", upload_to_ops=True)

            review_path = Path(temp_dir) / "unknown_items" / "events_unknown_items.json"
            self.assertTrue(review_path.exists())
            payload = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["total_unique_unknown_items"], 1)
            self.assertIn("Mystery Item", payload["items"])
            self.assertEqual(payload["items"]["Mystery Item"]["temperature_zone"], "unknown")
            mocked_upload.assert_not_called()

    @patch("builtins.input", return_value="n")
    @patch("save_json.upload_events_to_ops")
    def test_save_json_continues_upload_when_user_declines_review(self, mocked_upload, _mocked_input) -> None:
        mocked_upload.return_value = OpsImportResult(
            True,
            True,
            202,
            "job-continue",
            "completed",
            beo_document={
                "id": 15,
                "document_type": "revision",
                "revision_number": 2,
            },
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "events.json"

            save_json([EVENT_WITH_UNKNOWN], str(output_path), source_file="sample.pdf", upload_to_ops=True)

            mocked_upload.assert_called_once()
            self.assertTrue(mocked_upload.call_args.kwargs["allow_unresolved_unknowns"])
            logs_dir = Path(temp_dir) / "logs"
            log_path = next(logs_dir.glob("events_*.log"))
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("BEO document linked. id=15", log_text)
            self.assertIn("revision_number=2", log_text)


if __name__ == "__main__":
    unittest.main()
