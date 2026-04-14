from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from beo_pipeline.beo_parser import infer_beo_type
from ops_events_api import build_ops_import_payload

MATCH_THRESHOLD = 45


def resolve_events_output_path(
    pdf_path: str,
    output_path: str | None = None,
    *,
    beo_type_override: str | None = None,
) -> str:
    if output_path:
        return output_path
    beo_type, _revision_number = infer_beo_type(pdf_path)
    if beo_type_override:
        beo_type = beo_type_override
    source = Path(pdf_path)
    if beo_type == "original":
        return str(Path("ready_to_print") / "json" / f"{source.stem}_events.json")
    return str(Path("ready_to_print") / "json" / "revisions" / f"{source.stem}_events.json")


def load_events_json(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of events in {path}")
    return [item for item in data if isinstance(item, dict)]


def build_revision_artifacts(
    current_events: list[dict[str, Any]],
    *,
    source_file: str,
    baseline_events: list[dict[str, Any]] | None = None,
    baseline_source_file: str | None = None,
    beo_type_override: str | None = None,
) -> dict[str, Any]:
    current_payload = build_ops_import_payload(current_events, source_file=source_file)
    baseline_payload = build_ops_import_payload(baseline_events or [], source_file=baseline_source_file)
    beo_type, _revision_number = infer_beo_type(source_file)
    if beo_type_override:
        beo_type = beo_type_override

    current_grouped = _group_events(current_payload["events"])
    baseline_grouped = _group_events(baseline_payload["events"])

    unchanged: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    superseded: list[dict[str, Any]] = []

    for group_key, current_group in current_grouped.items():
        baseline_group = baseline_grouped.get(group_key, [])
        match_result = _match_group(current_group, baseline_group, beo_type=beo_type)
        unchanged.extend(match_result["unchanged"])
        inserts.extend(match_result["inserted"])
        updates.extend(match_result["updated"])
        superseded.extend(match_result["superseded"])

    for group_key, baseline_group in baseline_grouped.items():
        if group_key in current_grouped or beo_type == "popup":
            continue
        for baseline_event in baseline_group:
            superseded.append(_build_superseded_operation(baseline_event))

    return {
        "meta": {
            "source_file": source_file,
            "baseline_source_file": baseline_source_file,
            "beo_type": beo_type,
            "current_event_count": len(current_payload["events"]),
            "baseline_event_count": len(baseline_payload["events"]),
        },
        "summary": {
            "inserted": len(inserts),
            "updated": len(updates),
            "unchanged": len(unchanged),
            "superseded": len(superseded),
        },
        "diff": {
            "inserted": inserts,
            "updated": updates,
            "unchanged": unchanged,
            "superseded": superseded,
        },
        "upsert_payload": {
            "source_system": current_payload["source_system"],
            "meta": current_payload["meta"],
            "operations": [*inserts, *updates, *superseded],
        },
    }


def save_revision_artifacts(
    artifacts: dict[str, Any],
    *,
    output_events_path: str,
) -> tuple[str, str]:
    output_dir = Path(output_events_path).parent
    output_stem = Path(output_events_path).stem
    diff_path = output_dir / f"{output_stem}_revision_diff.json"
    upsert_path = output_dir / f"{output_stem}_upsert_payload.json"
    _write_json(diff_path, {"meta": artifacts["meta"], "summary": artifacts["summary"], "diff": artifacts["diff"]})
    _write_json(upsert_path, artifacts["upsert_payload"])
    return str(diff_path), str(upsert_path)


def _group_events(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        identity = event.get("identity", {}) if isinstance(event.get("identity"), dict) else {}
        group_key = str(identity.get("event_family_key") or "").strip()
        grouped.setdefault(group_key, []).append(event)
    return grouped


def _match_group(
    current_group: list[dict[str, Any]],
    baseline_group: list[dict[str, Any]],
    *,
    beo_type: str,
) -> dict[str, list[dict[str, Any]]]:
    unused_baseline = list(baseline_group)
    unchanged: list[dict[str, Any]] = []
    inserted: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []

    for current_event in current_group:
        if beo_type == "popup":
            inserted.append(_build_insert_operation(current_event))
            continue

        best_match, match_score = _find_best_match(current_event, unused_baseline)
        if best_match is None or match_score < MATCH_THRESHOLD:
            inserted.append(_build_insert_operation(current_event))
            continue

        unused_baseline.remove(best_match)
        changed_fields = _diff_event_fields(best_match, current_event)
        if changed_fields:
            updated.append(
                {
                    "action": "update",
                    "match_strategy": "function_similarity",
                    "match_score": match_score,
                    "event_family_key": current_event["identity"]["event_family_key"],
                    "previous_event": best_match,
                    "event": current_event,
                    "changed_fields": changed_fields,
                }
            )
        else:
            unchanged.append(
                {
                    "action": "unchanged",
                    "match_strategy": "function_similarity",
                    "match_score": match_score,
                    "event_family_key": current_event["identity"]["event_family_key"],
                    "event": current_event,
                }
            )

    superseded = [] if beo_type == "popup" else [_build_superseded_operation(event) for event in unused_baseline]
    return {
        "unchanged": unchanged,
        "inserted": inserted,
        "updated": updated,
        "superseded": superseded,
    }


def _build_insert_operation(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": "insert",
        "event_family_key": event["identity"]["event_family_key"],
        "event": event,
    }


def _build_superseded_operation(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": "supersede",
        "event_family_key": event["identity"]["event_family_key"],
        "previous_event": event,
    }


def _find_best_match(
    current_event: dict[str, Any],
    baseline_events: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, int]:
    best_event: dict[str, Any] | None = None
    best_score = -1
    for baseline_event in baseline_events:
        score = _score_match(current_event, baseline_event)
        if score > best_score:
            best_event = baseline_event
            best_score = score
    return best_event, best_score


def _score_match(current_event: dict[str, Any], baseline_event: dict[str, Any]) -> int:
    current_service = current_event.get("service", {}) if isinstance(current_event.get("service"), dict) else {}
    baseline_service = baseline_event.get("service", {}) if isinstance(baseline_event.get("service"), dict) else {}

    current_function = _normalize_token(current_service.get("function"))
    baseline_function = _normalize_token(baseline_service.get("function"))
    if not current_function or current_function != baseline_function:
        return -1

    score = 60
    current_start = _minutes(current_service.get("time", {}).get("start"))
    baseline_start = _minutes(baseline_service.get("time", {}).get("start"))
    if current_start is not None and baseline_start is not None:
        diff = abs(current_start - baseline_start)
        if diff <= 15:
            score += 25
        elif diff <= 60:
            score += 12

    if _normalize_token(current_service.get("room")) and _normalize_token(current_service.get("room")) == _normalize_token(
        baseline_service.get("room")
    ):
        score += 10

    current_fp = _normalize_token(_menu_fingerprint(current_event))
    baseline_fp = _normalize_token(_menu_fingerprint(baseline_event))
    if current_fp and current_fp == baseline_fp:
        score += 10

    current_gtd = current_service.get("gtd")
    baseline_gtd = baseline_service.get("gtd")
    if isinstance(current_gtd, int) and isinstance(baseline_gtd, int):
        if current_gtd == baseline_gtd:
            score += 5
        elif abs(current_gtd - baseline_gtd) <= 25:
            score += 2

    return score


def _diff_event_fields(previous_event: dict[str, Any], current_event: dict[str, Any]) -> list[str]:
    changed_fields: list[str] = []
    for field_name in [
        "quote",
        "organization",
        "service",
        "timeline",
        "details",
        "setup",
        "staffing",
        "notes",
        "tags",
        "beo",
    ]:
        if previous_event.get(field_name) != current_event.get(field_name):
            changed_fields.append(field_name)
    return changed_fields


def _menu_fingerprint(event: dict[str, Any]) -> str | None:
    details = event.get("details", {}) if isinstance(event.get("details"), dict) else {}
    return details.get("menu_fingerprint")


def _minutes(value: Any) -> int | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return None


def _normalize_token(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False)
