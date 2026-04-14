from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

import config  # noqa: F401  # Ensures .env files are loaded before reading os.environ.


logger = logging.getLogger(__name__)

DEFAULT_SOURCE_SYSTEM = "beo_generator"
DEFAULT_IMPORT_ENDPOINT = "/api/v1/events/import"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_EVENT_STATUS = "on_time"


@dataclass(slots=True)
class OpsImportResult:
    attempted: bool
    success: bool
    status_code: int | None
    job_id: str
    message: str
    response_body: Any = None


def upload_events_to_ops(
    events: list[dict[str, Any]],
    *,
    source_file: str | None = None,
    job_id: str | None = None,
    base_url: str | None = None,
    token: str | None = None,
    timeout_seconds: int | None = None,
    source_system: str | None = None,
) -> OpsImportResult:
    job_id = job_id or str(uuid.uuid4())
    source_system = source_system or os.getenv("OPS_EVENTS_SOURCE_SYSTEM", DEFAULT_SOURCE_SYSTEM)
    enabled = _read_bool_env("OPS_EVENTS_API_ENABLED", default=True)
    if not enabled:
        return OpsImportResult(False, False, None, job_id, "OPS upload disabled by environment.")

    if not events:
        return OpsImportResult(False, False, None, job_id, "No events to upload.")

    base_url = (base_url or os.getenv("OPS_EVENTS_API_BASE_URL", "")).strip()
    token = (token or os.getenv("OPS_EVENTS_API_TOKEN", "")).strip()
    timeout_seconds = timeout_seconds or _read_int_env(
        "OPS_EVENTS_API_TIMEOUT_SECONDS",
        DEFAULT_TIMEOUT_SECONDS,
    )

    if not base_url or not token:
        return OpsImportResult(
            False,
            False,
            None,
            job_id,
            "OPS upload skipped because base URL or token is missing.",
        )

    payload = build_ops_import_payload(
        events,
        source_file=source_file,
        job_id=job_id,
        source_system=source_system,
    )
    url = f"{base_url.rstrip('/')}{DEFAULT_IMPORT_ENDPOINT}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
            parsed_body = _decode_json_body(raw_body)
            logger.info(
                "OPS events import succeeded. job_id=%s status=%s events=%s",
                job_id,
                response.status,
                len(payload["events"]),
            )
            return OpsImportResult(
                True,
                200 <= response.status < 300,
                response.status,
                job_id,
                "OPS upload completed.",
                parsed_body,
            )
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        parsed_body = _decode_json_body(raw_body)
        logger.error(
            "OPS events import failed with HTTP error. job_id=%s status=%s body=%s",
            job_id,
            exc.code,
            raw_body,
        )
        return OpsImportResult(
            True,
            False,
            exc.code,
            job_id,
            f"OPS upload failed with HTTP {exc.code}.",
            parsed_body,
        )
    except error.URLError as exc:
        logger.error("OPS events import failed with network error. job_id=%s reason=%s", job_id, exc.reason)
        return OpsImportResult(
            True,
            False,
            None,
            job_id,
            f"OPS upload failed with network error: {exc.reason}",
        )


def build_ops_import_payload(
    events: list[dict[str, Any]],
    *,
    source_file: str | None = None,
    job_id: str | None = None,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
) -> dict[str, Any]:
    resolved_job_id = job_id or str(uuid.uuid4())
    return {
        "source_system": source_system,
        "meta": {
            "job_id": resolved_job_id,
            "source_file": source_file,
        },
        "events": [_normalize_event_for_ops(event, source_file=source_file) for event in events],
    }


def _normalize_event_for_ops(event: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    if "service" in event and "beo" in event:
        return _normalize_standard_event(event, source_file=source_file)
    return _normalize_legacy_event(event, source_file=source_file)


def _normalize_standard_event(event: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    normalized = dict(event)
    normalized["status"] = DEFAULT_EVENT_STATUS
    normalized["date"] = _normalize_date(event.get("date"))

    service = dict(event.get("service") or {})
    time_data = dict(service.get("time") or {})
    service["time"] = {
        "start": _normalize_time(time_data.get("start")),
        "end": _normalize_time(time_data.get("end")),
    }
    normalized["service"] = service

    source_trace = dict(event.get("source_trace") or {})
    source_trace.setdefault("generator", "external-beo")
    source_trace.setdefault("document_id", event.get("event_order"))
    source_trace.setdefault("file_name", Path(source_file).name if source_file else None)
    normalized["source_trace"] = source_trace
    return normalized


def _normalize_legacy_event(event: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    raw_details = event.get("details", {}) if isinstance(event.get("details"), dict) else {}
    return {
        "event_order": str(event.get("event_order") or ""),
        "status": DEFAULT_EVENT_STATUS,
        "date": _normalize_date(event.get("date")),
        "organization": event.get("organization"),
        "beo": {
            "type": "original",
            "revision_number": 0,
        },
        "service": {
            "function": event.get("function"),
            "category": None,
            "subtype": None,
            "meal_period": None,
            "time": {
                "start": _normalize_time(event.get("time")),
                "end": None,
            },
            "room": event.get("room"),
            "gtd": event.get("gtd"),
            "menu_style": event.get("menu_style"),
        },
        "timeline": {
            "pickup_food": _normalize_time(event.get("pickup_food")),
            "clean_up": _normalize_time(event.get("lift_time")),
        },
        "details": {
            "raw": raw_details.get("raw", ""),
            "menu_sections": raw_details.get("menu_sections", []),
            "menu_fingerprint": raw_details.get("menu_fingerprint"),
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
            "generator": "external-beo",
            "document_id": event.get("event_order"),
            "file_name": Path(source_file).name if source_file else None,
        },
    }


def _normalize_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def _normalize_time(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return text


def _decode_json_body(raw_body: str) -> Any:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body


def _read_bool_env(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
