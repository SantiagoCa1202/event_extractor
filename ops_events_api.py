from __future__ import annotations

import json
import logging
import os
import re
import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

import config  # noqa: F401  # Ensures .env files are loaded before reading os.environ.


logger = logging.getLogger(__name__)

DEFAULT_SOURCE_SYSTEM = "beo_generator"
DEFAULT_BEO_DOCUMENT_ENDPOINT = "/api/v1/beo-documents"
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
    beo_document: dict[str, Any] | None = None


@dataclass(slots=True)
class BeoDocumentUploadResult:
    attempted: bool
    success: bool
    status_code: int | None
    message: str
    document: dict[str, Any] | None = None
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
    allow_unresolved_unknowns: bool = False,
) -> OpsImportResult:
    job_id = job_id or str(uuid.uuid4())
    source_system = source_system or os.getenv("OPS_EVENTS_SOURCE_SYSTEM", DEFAULT_SOURCE_SYSTEM)
    enabled = _read_bool_env("OPS_EVENTS_API_ENABLED", default=True)
    if not enabled:
        return OpsImportResult(False, False, None, job_id, "OPS upload disabled by environment.")

    if not events:
        return OpsImportResult(False, False, None, job_id, "No events to upload.")

    unresolved_unknowns = _collect_unresolved_unknown_items(events)
    if unresolved_unknowns and not allow_unresolved_unknowns:
        return OpsImportResult(
            False,
            False,
            None,
            job_id,
            f"OPS upload skipped because unresolved unknown_items remain: {', '.join(unresolved_unknowns[:10])}",
        )

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

    beo_upload_result = _upload_beo_document_for_events(
        events,
        source_file=source_file,
        base_url=base_url,
        token=token,
        timeout_seconds=timeout_seconds,
    )
    if source_file and str(source_file).lower().endswith(".pdf") and not beo_upload_result.success:
        return OpsImportResult(
            beo_upload_result.attempted,
            False,
            beo_upload_result.status_code,
            job_id,
            f"OPS upload skipped because BEO document upload failed: {beo_upload_result.message}",
            beo_upload_result.response_body,
            beo_document=beo_upload_result.document,
        )

    payload = build_ops_import_payload(
        events,
        source_file=source_file,
        job_id=job_id,
        source_system=source_system,
        beo_document=beo_upload_result.document,
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
                beo_document=beo_upload_result.document,
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
            beo_document=beo_upload_result.document,
        )
    except error.URLError as exc:
        logger.error("OPS events import failed with network error. job_id=%s reason=%s", job_id, exc.reason)
        return OpsImportResult(
            True,
            False,
            None,
            job_id,
            f"OPS upload failed with network error: {exc.reason}",
            beo_document=beo_upload_result.document,
        )


def build_ops_import_payload(
    events: list[dict[str, Any]],
    *,
    source_file: str | None = None,
    job_id: str | None = None,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
    beo_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_job_id = job_id or str(uuid.uuid4())
    return {
        "source_system": source_system,
        "meta": {
            "job_id": resolved_job_id,
            "source_file": source_file,
        },
        "events": [
            _normalize_event_for_ops(event, source_file=source_file, beo_document=beo_document)
            for event in events
        ],
    }


def _normalize_event_for_ops(
    event: dict[str, Any],
    *,
    source_file: str | None = None,
    beo_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if "service" in event and "beo" in event:
        return _normalize_standard_event(event, source_file=source_file, beo_document=beo_document)
    return _normalize_legacy_event(event, source_file=source_file, beo_document=beo_document)


def _normalize_standard_event(
    event: dict[str, Any],
    *,
    source_file: str | None = None,
    beo_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(event)
    normalized["status"] = DEFAULT_EVENT_STATUS
    normalized["quote"] = event.get("quote")
    normalized["date"] = _normalize_date(event.get("date"))

    service = dict(event.get("service") or {})
    time_data = dict(service.get("time") or {})
    sanitized_room = _sanitize_room(service.get("room"), raw_text=(event.get("details") or {}).get("raw"))
    service["time"] = {
        "start": _normalize_time(time_data.get("start")),
        "end": _normalize_time(time_data.get("end")),
    }
    service["room"] = sanitized_room
    normalized["service"] = service

    source_trace = dict(event.get("source_trace") or {})
    source_trace.setdefault("generator", "external-beo")
    source_trace.setdefault("document_id", event.get("event_order"))
    source_trace.setdefault("file_name", Path(source_file).name if source_file else None)
    normalized["source_trace"] = source_trace
    _attach_beo_document_reference(normalized, source_file=source_file, beo_document=beo_document)
    normalized["identity"] = _build_identity(normalized)
    normalized["revision_context"] = _build_revision_context(normalized, source_file=source_file)
    return normalized


def _normalize_legacy_event(
    event: dict[str, Any],
    *,
    source_file: str | None = None,
    beo_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_details = event.get("details", {}) if isinstance(event.get("details"), dict) else {}
    normalized = {
        "event_order": str(event.get("event_order") or ""),
        "quote": event.get("quote"),
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
            "room": _sanitize_room(event.get("room"), raw_text=raw_details.get("raw", "")),
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
    _attach_beo_document_reference(normalized, source_file=source_file, beo_document=beo_document)
    normalized["identity"] = _build_identity(normalized)
    normalized["revision_context"] = _build_revision_context(normalized, source_file=source_file)
    return normalized


def _upload_beo_document_for_events(
    events: list[dict[str, Any]],
    *,
    source_file: str | None,
    base_url: str,
    token: str,
    timeout_seconds: int,
) -> BeoDocumentUploadResult:
    if not source_file:
        return BeoDocumentUploadResult(False, True, None, "BEO document upload skipped because source_file is missing.")
    source_path = Path(source_file)
    if source_path.suffix.lower() != ".pdf":
        return BeoDocumentUploadResult(False, True, None, "BEO document upload skipped because source_file is not a PDF.")
    if not source_path.exists():
        return BeoDocumentUploadResult(False, False, None, f"BEO PDF not found at {source_file}.")

    document_type, revision_number = _extract_beo_upload_metadata(events, source_file=source_file)
    if document_type not in {"original", "revision", "popup"}:
        return BeoDocumentUploadResult(False, False, None, f"Invalid BEO document_type: {document_type!r}.")
    if revision_number < 0:
        return BeoDocumentUploadResult(False, False, None, f"Invalid BEO revision_number: {revision_number}.")

    return upload_beo_document(
        source_file,
        document_type=document_type,
        revision_number=revision_number,
        metadata=_build_beo_upload_metadata(
            source_path,
            document_type=document_type,
            revision_number=revision_number,
        ),
        base_url=base_url,
        token=token,
        timeout_seconds=timeout_seconds,
    )


def upload_beo_document(
    pdf_path: str,
    *,
    document_type: str,
    revision_number: int,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
    base_url: str | None = None,
    token: str | None = None,
    timeout_seconds: int | None = None,
) -> BeoDocumentUploadResult:
    resolved_base_url = (base_url or os.getenv("OPS_EVENTS_API_BASE_URL", "")).strip()
    resolved_token = (token or os.getenv("OPS_EVENTS_API_TOKEN", "")).strip()
    resolved_timeout = timeout_seconds or _read_int_env("OPS_EVENTS_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    source_path = Path(pdf_path)

    if source_path.suffix.lower() != ".pdf":
        return BeoDocumentUploadResult(False, False, None, "BEO document upload requires a PDF file.")
    if not resolved_base_url or not resolved_token:
        return BeoDocumentUploadResult(False, False, None, "BEO document upload skipped because base URL or token is missing.")
    if not source_path.exists():
        return BeoDocumentUploadResult(False, False, None, f"BEO PDF not found at {pdf_path}.")

    body, content_type = _build_beo_upload_request_body(
        source_path,
        document_type=document_type,
        revision_number=revision_number,
        status=status,
        metadata=metadata,
    )
    headers = {
        "Authorization": f"Bearer {resolved_token}",
        "Content-Type": content_type,
        "Accept": "application/json",
    }
    url = f"{resolved_base_url.rstrip('/')}{DEFAULT_BEO_DOCUMENT_ENDPOINT}"
    req = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=resolved_timeout) as response:
            raw_body = response.read().decode("utf-8")
            parsed_body = _decode_json_body(raw_body)
            document = parsed_body if isinstance(parsed_body, dict) else None
            logger.info(
                "BEO document upload succeeded. file=%s document_id=%s type=%s revision_number=%s status=%s",
                source_path.name,
                document.get("id") if isinstance(document, dict) else None,
                document_type,
                revision_number,
                response.status,
            )
            return BeoDocumentUploadResult(
                True,
                200 <= response.status < 300,
                response.status,
                "BEO document upload completed.",
                document=document,
                response_body=parsed_body,
            )
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        parsed_body = _decode_json_body(raw_body)
        logger.error(
            "BEO document upload failed with HTTP error. file=%s type=%s revision_number=%s status=%s body=%s",
            source_path.name,
            document_type,
            revision_number,
            exc.code,
            raw_body,
        )
        return BeoDocumentUploadResult(
            True,
            False,
            exc.code,
            f"BEO document upload failed with HTTP {exc.code}.",
            response_body=parsed_body,
        )
    except error.URLError as exc:
        logger.error(
            "BEO document upload failed with network error. file=%s type=%s revision_number=%s reason=%s",
            source_path.name,
            document_type,
            revision_number,
            exc.reason,
        )
        return BeoDocumentUploadResult(
            True,
            False,
            None,
            f"BEO document upload failed with network error: {exc.reason}",
        )


def _build_beo_upload_request_body(
    source_path: Path,
    *,
    document_type: str,
    revision_number: int,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    line_break = b"\r\n"
    chunks: list[bytes] = []

    def add_text_field(name: str, value: str) -> None:
        chunks.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"),
                b"",
                value.encode("utf-8"),
            ]
        )

    def add_file_field(name: str, path: Path) -> None:
        chunks.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"'.encode("utf-8"),
                b"Content-Type: application/pdf",
                b"",
                path.read_bytes(),
            ]
        )

    add_text_field("document_type", document_type)
    add_text_field("revision_number", str(revision_number))
    if status:
        add_text_field("status", status)
    if metadata:
        for key, value in metadata.items():
            if value is None:
                continue
            add_text_field(f"metadata[{key}]", str(value))
    add_file_field("file", source_path)
    chunks.append(f"--{boundary}--".encode("utf-8"))
    chunks.append(b"")
    return line_break.join(chunks), f"multipart/form-data; boundary={boundary}"


def _extract_beo_upload_metadata(events: list[dict[str, Any]], *, source_file: str | None) -> tuple[str, int]:
    if events:
        beo = events[0].get("beo") if isinstance(events[0].get("beo"), dict) else {}
        beo_type = str(beo.get("type") or "").strip().lower()
        revision_number = _coerce_int(beo.get("revision_number"))
        if beo_type:
            return beo_type, revision_number
    return _infer_beo_metadata_from_file_name(source_file)


def _build_beo_upload_metadata(
    source_path: Path,
    *,
    document_type: str,
    revision_number: int,
) -> dict[str, Any]:
    detected_label = document_type if revision_number <= 0 else f"{document_type} {revision_number}"
    extractor_version = os.getenv("OPS_EVENTS_EXTRACTOR_VERSION", "event_extractor")
    return {
        "source_path": str(source_path.resolve()),
        "extractor_version": extractor_version,
        "detected_label": detected_label,
        "original_filename": source_path.name,
    }


def _infer_beo_metadata_from_file_name(source_file: str | None) -> tuple[str, int]:
    file_name = Path(source_file).name.lower() if source_file else ""
    if "popup" in file_name or "pop-up" in file_name:
        return "popup", _extract_revision_number_from_text(file_name)
    if "revision" in file_name or "revised" in file_name or "revisions" in file_name:
        return "revision", _extract_revision_number_from_text(file_name)
    return "original", 0


def _extract_revision_number_from_text(value: str) -> int:
    match = re.search(r"(?:rev(?:ision)?\D*)(\d+)", value, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _attach_beo_document_reference(
    event: dict[str, Any],
    *,
    source_file: str | None,
    beo_document: dict[str, Any] | None,
) -> None:
    beo = dict(event.get("beo") or {})
    page_start, page_end = _extract_page_bounds(event, beo=beo)
    document_id = beo_document.get("id") if isinstance(beo_document, dict) else None
    file_name = (
        beo.get("file_name")
        or (beo_document.get("file_name") if isinstance(beo_document, dict) else None)
        or (Path(source_file).name if source_file else None)
    )
    revision_number = _coerce_int(beo.get("revision_number"))
    document_type = str(beo.get("type") or "original").strip().lower() or "original"

    if document_id is not None:
        event["beo_document_id"] = document_id
    event["beo_page_start"] = page_start
    if page_end is not None:
        event["beo_page_end"] = page_end

    beo["type"] = document_type
    beo["revision_number"] = revision_number
    beo["file_name"] = file_name
    beo["page_start"] = page_start
    if page_end is not None:
        beo["page_end"] = page_end
    event["beo"] = beo


def _extract_page_bounds(event: dict[str, Any], *, beo: dict[str, Any] | None = None) -> tuple[int | None, int | None]:
    resolved_beo = beo if isinstance(beo, dict) else {}
    explicit_start = _coerce_optional_int(resolved_beo.get("page_start") or event.get("beo_page_start"))
    explicit_end = _coerce_optional_int(resolved_beo.get("page_end") or event.get("beo_page_end"))
    if explicit_start is not None:
        return explicit_start, explicit_end if explicit_end is not None else explicit_start

    source_trace = event.get("source_trace") if isinstance(event.get("source_trace"), dict) else {}
    page_ranges = source_trace.get("page_ranges") if isinstance(source_trace.get("page_ranges"), list) else []
    pages: list[int] = []
    for page_range in page_ranges:
        text = str(page_range or "").strip()
        if not text:
            continue
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", text)
        if not match:
            continue
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        pages.extend(range(start, end + 1))
    if not pages:
        return None, None
    return min(pages), max(pages)


def _coerce_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _build_identity(event: dict[str, Any]) -> dict[str, str | None]:
    service = event.get("service", {}) if isinstance(event.get("service"), dict) else {}
    time_data = service.get("time", {}) if isinstance(service.get("time"), dict) else {}
    event_order = str(event.get("event_order") or "").strip()
    quote = str(event.get("quote") or "").strip()
    normalized_date = _normalize_token(event.get("date"))
    normalized_start = _normalize_token(time_data.get("start"))
    normalized_room = _normalize_token(service.get("room"))
    normalized_function = _normalize_token(service.get("function"))

    family_key = "|".join(part for part in [quote, event_order, normalized_date] if part) or None
    identity_source = "|".join(
        [
            quote,
            event_order,
            normalized_date,
            normalized_start,
            normalized_room,
            normalized_function,
        ]
    )
    instance_key = f"{event_order}|{hashlib.sha1(identity_source.encode('utf-8')).hexdigest()[:20]}" if event_order else hashlib.sha1(
        identity_source.encode("utf-8")
    ).hexdigest()[:20]
    return {
        "event_family_key": family_key,
        "event_instance_key": instance_key,
    }


def _build_revision_context(event: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    beo = event.get("beo", {}) if isinstance(event.get("beo"), dict) else {}
    beo_type = str(beo.get("type") or "original").strip().lower()
    revision_number = _coerce_int(beo.get("revision_number"))
    file_name = Path(source_file).name if source_file else None
    document_version_key = "|".join(
        [
            str(event.get("event_order") or "").strip(),
            beo_type,
            str(revision_number),
            file_name or "",
        ]
    )
    return {
        "beo_type": beo_type,
        "revision_number": revision_number,
        "is_revision": beo_type != "original" or revision_number > 0,
        "document_version_key": document_version_key,
        "revision_source": "pdf" if file_name else "unknown",
        "supersedes_strategy": "latest_revision_wins_per_event_instance",
    }


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _sanitize_room(value: Any, *, raw_text: str | None = None) -> str | None:
    room = " ".join(str(value or "").split()).strip()
    if room and not _looks_like_bad_room(room) and len(room) <= 180:
        return room

    inferred = _infer_room_from_raw(raw_text or "")
    if inferred and len(inferred) <= 180:
        return inferred

    if room:
        cleaned = _strip_room_noise(room)
        if cleaned and not _looks_like_bad_room(cleaned) and len(cleaned) <= 180:
            return cleaned
    return None


def _looks_like_bad_room(value: str) -> bool:
    lower = value.lower()
    if len(value) > 180:
        return True
    suspicious_markers = [
        "event order page",
        "marriott proprietary",
        "organization:",
        "function day/date:",
        "phone:(",
        "based on ",
        "choice of ",
        "dessert:",
        "tractor iced tea",
        "starbucks",
        "assorted ",
        "scrambled eggs",
        "roasted ",
    ]
    return any(marker in lower for marker in suspicious_markers)


def _strip_room_noise(value: str) -> str | None:
    room = re.split(
        r"(?i)\b(?:event order page|marriott proprietary|organization:|function day/date:|phone:\(|based on |choice of |dessert:|tractor iced tea|starbucks|assorted )",
        value,
        maxsplit=1,
    )[0]
    room = " ".join(room.split()).strip(" -")
    return room or None


def _infer_room_from_raw(raw_text: str) -> str | None:
    lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) > 1:
        second_line = lines[1]
        if " - " in second_line:
            candidate = second_line.split(" - ", 1)[-1].strip()
            if candidate:
                return candidate
    first_line = lines[0]
    first_line = re.sub(r"^\d{1,2}:\d{2}\s*[AP]M\s+", "", first_line, flags=re.IGNORECASE).strip()
    parts = first_line.split()
    known_functions = [
        "continental breakfast",
        "breakfast buffet",
        "lunch buffet",
        "dinner buffet",
        "plated lunch",
        "plated dinner",
        "coffee break",
        "general session",
        "reception",
        "breakfast",
        "lunch",
        "dinner",
        "breakout",
        "break",
        "meeting",
        "registration",
        "office",
        "storage",
        "set up",
    ]
    lower = first_line.lower()
    for function_name in known_functions:
        if lower.startswith(function_name):
            candidate = first_line[len(function_name) :].strip(" -")
            return candidate or None
    return None


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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


def collect_unknown_items_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    items: dict[str, dict[str, Any]] = {}
    for event in events:
        event_order = str(event.get("event_order") or "").strip() or None
        date = event.get("date")
        service = event.get("service") if isinstance(event.get("service"), dict) else {}
        function = service.get("function") if isinstance(service, dict) else None
        room = service.get("room") if isinstance(service, dict) else None
        details = event.get("details") if isinstance(event.get("details"), dict) else {}
        menu_sections = details.get("menu_sections") if isinstance(details, dict) else []
        if not isinstance(menu_sections, list):
            continue
        for section in menu_sections:
            if not isinstance(section, dict):
                continue
            operational_split = section.get("operational_split")
            if not isinstance(operational_split, dict):
                continue
            section_unknowns = operational_split.get("unknown_items")
            if not isinstance(section_unknowns, list):
                continue

            section_items = section.get("items") if isinstance(section.get("items"), list) else []
            item_lookup: dict[str, list[dict[str, Any]]] = {}
            for item in section_items:
                if not isinstance(item, dict):
                    continue
                item_name = str(item.get("name") or "").strip()
                if not item_name:
                    continue
                item_lookup.setdefault(item_name, []).append(item)

            for raw_item in section_unknowns:
                item_name = str(raw_item or "").strip()
                if not item_name:
                    continue

                entry = items.setdefault(
                    item_name,
                    {
                        "temperature_zone": "unknown",
                        "suggested_route": None,
                        "occurrences": [],
                    },
                )
                matches = item_lookup.get(item_name) or [{}]
                for matched_item in matches:
                    occurrence = {
                        "event_order": event_order,
                        "date": date,
                        "function": function,
                        "room": room,
                        "section_title": section.get("title"),
                        "section_type": section.get("type"),
                        "course_type": section.get("course_type"),
                        "source_text": matched_item.get("source_text") if isinstance(matched_item, dict) else None,
                    }
                    if occurrence not in entry["occurrences"]:
                        entry["occurrences"].append(occurrence)

    return {
        "total_unique_unknown_items": len(items),
        "items": dict(sorted(items.items())),
    }


def _collect_unresolved_unknown_items(events: list[dict[str, Any]]) -> list[str]:
    unknowns_report = collect_unknown_items_report(events)
    return sorted(unknowns_report["items"].keys())
