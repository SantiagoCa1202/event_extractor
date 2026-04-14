from __future__ import annotations

import re

from .food_service_filter import is_food_service_function
from .menu_extractor import derive_menu_style, extract_menu_sections
from .menu_normalizer import build_menu_fingerprint
from .production_router import annotate_menu_sections_with_production
from .schemas import BeoDocument, EventCandidate, SourceTrace, Staffing, to_dict
from .service_classifier import classify_service
from .setup_rules import evaluate_setup
from .timeline_rules import build_timeline
from .traceability import format_page_ranges, infer_confidence, summarize_snippets
from .validators import validate_event_payload


def build_event_object(document: BeoDocument, candidate: EventCandidate) -> dict | None:
    menu_sections = extract_menu_sections(candidate.raw)
    menu_item_count = sum(len(section.items) for section in menu_sections)
    item_names = [item.name for section in menu_sections for item in section.items]
    is_food, filter_reasons = is_food_service_function(
        candidate.function_name,
        candidate.raw,
        menu_item_count,
        item_names,
    )
    if not is_food:
        return None

    service_info = classify_service(candidate.function_name, candidate.raw, menu_sections)
    menu_style = derive_menu_style(candidate.raw, menu_sections)
    if service_info["category"] == "plated":
        menu_style = None
    menu_sections_payload = annotate_menu_sections_with_production([to_dict(section) for section in menu_sections])
    setup = evaluate_setup(service_info["category"], candidate.room, candidate.gtd)
    staffing = _extract_staffing(candidate.raw)
    confidence = infer_confidence(candidate.attendance_match is not None, menu_item_count, len(filter_reasons))
    notes = list(filter_reasons)

    for decision in setup["rule_trace"]["pending"]:
        notes.append(f"pending_rule:{decision.target}:{decision.reason}")

    event = {
        "event_order": document.event_order,
        "quote": document.quote,
        "date": document.date,
        "organization": document.organization,
        "beo": {
            "type": document.beo_type,
            "revision_number": document.revision_number,
        },
        "service": {
            "function": candidate.function_name,
            "category": service_info["category"],
            "subtype": service_info["subtype"],
            "meal_period": service_info["meal_period"],
            "time": {
                "start": candidate.start,
                "end": candidate.end,
            },
            "room": candidate.room,
            "gtd": candidate.gtd,
            "menu_style": menu_style,
        },
        "timeline": build_timeline(candidate.start, candidate.end),
        "details": {
            "raw": candidate.raw,
            "menu_sections": menu_sections_payload,
            "menu_fingerprint": build_menu_fingerprint(
                [item.name for section in menu_sections for item in section.items]
            ),
        },
        "setup": {
            "breakdown_station": to_dict(setup["breakdown_station"]),
            "service_equipment": [to_dict(item) for item in setup["service_equipment"]],
            "rule_trace": {
                key: [to_dict(decision) for decision in decisions]
                for key, decisions in setup["rule_trace"].items()
            },
        },
        "staffing": to_dict(staffing),
        "notes": notes,
        "tags": _build_tags(candidate, service_info),
        "source_trace": to_dict(
            SourceTrace(
                page_ranges=format_page_ranges(candidate.page_numbers),
                text_snippets=summarize_snippets(candidate.raw),
                confidence=confidence,
            )
        ),
    }

    event["notes"].extend(validate_event_payload(event))
    return event


def _extract_staffing(raw_block: str) -> Staffing:
    staffing = Staffing()
    patterns = {
        "bartenders": r"\((\d+)\)\s*Bartender",
        "servers": r"\((\d+)\)\s*Server",
        "chefs": r"\((\d+)\)\s*Chef",
        "attendants": r"\((\d+)\)\s*Attendant",
    }
    for field_name, pattern in patterns.items():
        match = re.search(pattern, raw_block, re.IGNORECASE)
        if match:
            setattr(staffing, field_name, int(match.group(1)))
    return staffing


def _build_tags(candidate: EventCandidate, service_info: dict[str, str]) -> list[str]:
    tags = [service_info["category"], service_info["meal_period"]]
    if candidate.attendance_match is None:
        tags.append("unmatched_attendance")
    if candidate.gtd is None:
        tags.append("missing_gtd")
    return sorted(set(tag for tag in tags if tag and tag != "unknown"))
