import json
import os
from datetime import datetime
from pathlib import Path

from ops_events_api import collect_unknown_items_report, upload_events_to_ops
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
    log_lines: list[str] = []
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    log_lines.append(f"JSON guardado en: {os.path.abspath(output_path)}")
    allow_upload_with_inconsistencies = False
    findings: list[tuple[str, str]] = []
    unknown_items_report: dict = {"items": {}, "total_unique_unknown_items": 0}

    if isinstance(data, list):
        findings = _collect_review_findings(data)
        log_lines.extend(_build_review_summary_lines_from_findings(findings))
        unknown_items_report = collect_unknown_items_report(data)
        unknown_items_path = _write_unknown_items_review(output_path, unknown_items_report, output_path)
        if unknown_items_path:
            log_lines.append(f"Unknown items saved to: {os.path.abspath(unknown_items_path)}")
            log_lines.append("OPS upload is blocked until those items are classified and the BEO is run again.")
        if upload_to_ops and _has_inconsistencies(findings, unknown_items_report):
            allow_upload_with_inconsistencies = _confirm_inconsistency_upload(findings, unknown_items_report)
            if allow_upload_with_inconsistencies:
                log_lines.append("User chose to continue the OPS upload despite detected inconsistencies.")
            else:
                log_lines.append("User chose to review inconsistencies before uploading to OPS. Upload canceled.")

    if revision_artifacts is not None:
        diff_path, upsert_path = save_revision_artifacts(revision_artifacts, output_events_path=output_path)
        log_lines.append(f"Revision diff guardado en: {os.path.abspath(diff_path)}")
        log_lines.append(f"Upsert payload guardado en: {os.path.abspath(upsert_path)}")

    if upload_to_ops and isinstance(data, list):
        if _has_inconsistencies(findings, unknown_items_report) and not allow_upload_with_inconsistencies:
            log_lines.append("OPS upload skipped. reason=User chose to review inconsistencies before uploading.")
            print("Inconsistencies were found. Database upload was stopped for review.")
        else:
            result = upload_events_to_ops(
                data,
                source_file=source_file or output_path,
                allow_unresolved_unknowns=allow_upload_with_inconsistencies,
            )
            if result.beo_document:
                document = result.beo_document
                log_lines.append(
                    "BEO document linked. "
                    f"id={document.get('id')} "
                    f"type={document.get('document_type') or document.get('type')} "
                    f"revision_number={document.get('revision_number')} "
                    f"events={len(data)}"
                )
            if not result.attempted:
                log_lines.append(f"OPS upload omitido. job_id={result.job_id} motivo={result.message}")
            elif result.success:
                log_lines.append(f"OPS upload completado. job_id={result.job_id} status={result.status_code}")
            else:
                log_lines.append(f"OPS upload fallo. job_id={result.job_id} detalle={result.message}")

    log_path = _write_run_log(output_path, log_lines)
    print(f"Proceso completado. JSON: {os.path.abspath(output_path)}")
    print(f"Log guardado en: {os.path.abspath(log_path)}")


def _build_review_summary_lines(events: list[dict]) -> list[str]:
    return _build_review_summary_lines_from_findings(_collect_review_findings(events))


def _collect_review_findings(events: list[dict]) -> list[tuple[str, str]]:
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
    return findings


def _build_review_summary_lines_from_findings(findings: list[tuple[str, str]]) -> list[str]:
    lines: list[str] = []
    if not findings:
        lines.append("Revision review: sin alertas automaticas.")
        return lines

    lines.append("Revision review:")
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
        lines.append(f"  {finding_type}: {len(matching)}")
        for label in matching[:3]:
            lines.append(f"    - {label}")
    return lines


def _write_run_log(output_path: str, lines: list[str]) -> str:
    output = Path(output_path)
    log_dir = output.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"{output.stem}_{timestamp}.log"
    with open(log_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).strip())
        handle.write("\n")
    return str(log_path)


def _write_unknown_items_review(output_path: str, report: dict, source_events_path: str) -> str | None:
    if not report["items"]:
        return None

    output = Path(output_path)
    review_dir = output.parent / "unknown_items"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{output.stem}_unknown_items.json"
    payload = {
        "source_events_file": str(Path(source_events_path).resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **report,
    }
    with open(review_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False)
        handle.write("\n")
    return str(review_path)


def _has_inconsistencies(findings: list[tuple[str, str]], unknown_items_report: dict) -> bool:
    return bool(findings or unknown_items_report.get("items"))


def _confirm_inconsistency_upload(findings: list[tuple[str, str]], unknown_items_report: dict) -> bool:
    unknown_count = int(unknown_items_report.get("total_unique_unknown_items") or 0)
    finding_count = len(findings)
    print(
        "Inconsistencies were found. "
        f"unknown_items={unknown_count}, alerts={finding_count}. "
        "Do you want to review them? (y/n): ",
        end="",
    )
    while True:
        answer = input().strip().lower()
        if answer == "y":
            return False
        if answer == "n":
            print("Continuing with the data upload as-is.")
            return True
        print("Invalid response. Type 'y' or 'n': ", end="")


def _event_label(event: dict) -> str:
    service = event.get("service", {}) if isinstance(event.get("service"), dict) else {}
    time_data = service.get("time", {}) if isinstance(service.get("time"), dict) else {}
    event_order = event.get("event_order") or "?"
    function = service.get("function") or "Unknown"
    start = time_data.get("start") or "?"
    room = service.get("room") or "no-room"
    return f"EO {event_order} | {start} | {function} | {room}"
