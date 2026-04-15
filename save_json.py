import json
import os

from ops_events_api import upload_events_to_ops
from revision_artifacts import save_revision_artifacts


def save_json(
    data,
    output_path: str,
    source_file: str | None = None,
    upload_to_ops: bool = True,
    revision_artifacts: dict | None = None,
):
    """Guarda un objeto Python como archivo JSON con formato legible."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"JSON guardado en: {os.path.abspath(output_path)}")
    if isinstance(data, list):
        _print_review_summary(data)

    if revision_artifacts is not None:
        diff_path, upsert_path = save_revision_artifacts(revision_artifacts, output_events_path=output_path)
        print(f"Revision diff guardado en: {os.path.abspath(diff_path)}")
        print(f"Upsert payload guardado en: {os.path.abspath(upsert_path)}")

    if upload_to_ops and isinstance(data, list):
        result = upload_events_to_ops(data, source_file=source_file or output_path)
        if not result.attempted:
            print(f"OPS upload omitido. job_id={result.job_id} motivo={result.message}")
        elif result.success:
            print(f"OPS upload completado. job_id={result.job_id} status={result.status_code}")
        else:
            print(f"OPS upload fallo. job_id={result.job_id} detalle={result.message}")


def _print_review_summary(events: list[dict]) -> None:
    findings: list[tuple[str, str]] = []
    for event in events:
        label = _event_label(event)
        service = event.get("service", {}) if isinstance(event.get("service"), dict) else {}
        source_trace = event.get("source_trace", {}) if isinstance(event.get("source_trace"), dict) else {}
        notes = event.get("notes", []) if isinstance(event.get("notes"), list) else []
        tags = event.get("tags", []) if isinstance(event.get("tags"), list) else []

        if not service.get("room"):
            findings.append(("missing_room", label))
        if service.get("gtd") is None:
            findings.append(("missing_gtd", label))
        if source_trace.get("confidence") == "low":
            findings.append(("low_confidence", label))
        if "unmatched_attendance" in tags:
            findings.append(("unmatched_attendance", label))
        if any(str(note).startswith("pending_rule:") for note in notes):
            findings.append(("pending_rule", label))
        if any("Invalid " in str(note) or "Missing details.raw" in str(note) for note in notes):
            findings.append(("validation_warning", label))

    if not findings:
        print("Revision review: sin alertas automaticas.")
        return

    print("Revision review:")
    for finding_type in [
        "missing_room",
        "missing_gtd",
        "unmatched_attendance",
        "low_confidence",
        "pending_rule",
        "validation_warning",
    ]:
        matching = [label for current_type, label in findings if current_type == finding_type]
        if not matching:
            continue
        print(f"  {finding_type}: {len(matching)}")
        for label in matching[:3]:
            print(f"    - {label}")


def _event_label(event: dict) -> str:
    service = event.get("service", {}) if isinstance(event.get("service"), dict) else {}
    time_data = service.get("time", {}) if isinstance(service.get("time"), dict) else {}
    event_order = event.get("event_order") or "?"
    function = service.get("function") or "Unknown"
    start = time_data.get("start") or "?"
    room = service.get("room") or "no-room"
    return f"EO {event_order} | {start} | {function} | {room}"
