from __future__ import annotations

import re

from .schemas import AttendanceEntry, BeoDocument, EventCandidate


TIME_RANGE_RE = re.compile(r"^\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M\b", re.IGNORECASE)
TIME_ONLY_RE = re.compile(r"^\d{1,2}:\d{2}\s*[AP]M\b(?!\s*-\s*\d)", re.IGNORECASE)
KNOWN_FUNCTIONS = [
    "Continental Breakfast",
    "Breakfast Buffet",
    "Lunch Buffet",
    "Dinner Buffet",
    "Plated Lunch",
    "Plated Dinner",
    "Coffee Break",
    "Board Meeting",
    "General Session",
    "Full Day Beverage Break",
    "Half Day Beverage Break",
    "Reception",
    "Breakfast",
    "Lunch",
    "Dinner",
    "Breakout",
    "Break",
    "Meeting",
    "Registration",
    "Set Up",
    "Teardown",
    "Storage",
    "Office",
]


def detect_event_candidates(document: BeoDocument) -> list[EventCandidate]:
    annotated_lines = _annotated_lines(document)
    body_lines = _slice_between_markers(annotated_lines, "ATTENDANCE", "ROOM SETUP")
    attendance_entries = _parse_attendance_entries(body_lines)
    detail_blocks = _split_detail_blocks(body_lines)

    candidates: list[EventCandidate] = []
    for block_lines in detail_blocks:
        header = block_lines[0][1]
        start_match = TIME_ONLY_RE.match(header)
        if not start_match:
            continue
        start = start_match.group(0)
        header_body = header[len(start) :].strip()
        function_name, room = _extract_function_and_room(header_body)
        attendance = _match_attendance(attendance_entries, start, function_name, room)
        raw = "\n".join(text for _, text in block_lines)
        page_numbers = sorted({page_number for page_number, _ in block_lines})
        candidates.append(
            EventCandidate(
                start=start,
                end=attendance.end if attendance else None,
                function_name=function_name,
                room=attendance.room if attendance and attendance.room else room,
                gtd=attendance.gtd if attendance else None,
                raw=raw,
                page_numbers=page_numbers,
                attendance_match=attendance,
            )
        )
    return candidates


def _annotated_lines(document: BeoDocument) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for page in document.pages:
        for raw_line in page.text.splitlines():
            cleaned = " ".join(raw_line.split()).strip()
            if cleaned:
                lines.append((page.page_number, cleaned))
    return lines


def _slice_between_markers(
    lines: list[tuple[int, str]], start_marker: str, end_marker: str
) -> list[tuple[int, str]]:
    collecting = False
    collected: list[tuple[int, str]] = []
    for page_number, line in lines:
        if start_marker.lower() in line.lower():
            collecting = True
            continue
        if collecting and line.upper().startswith(end_marker):
            break
        if collecting:
            collected.append((page_number, line))
    return collected


def _parse_attendance_entries(lines: list[tuple[int, str]]) -> list[AttendanceEntry]:
    entries: list[AttendanceEntry] = []
    buffer: list[str] = []

    for _, line in lines:
        if line.upper().startswith("TIME FUNCTION"):
            continue
        if TIME_RANGE_RE.match(line):
            if buffer:
                parsed = _parse_attendance_chunk(buffer)
                if parsed:
                    entries.append(parsed)
            buffer = [line]
        elif TIME_ONLY_RE.match(line):
            break
        elif line.upper().startswith("POST AS:"):
            continue
        elif buffer:
            buffer.append(line)
    if buffer:
        parsed = _parse_attendance_chunk(buffer)
        if parsed:
            entries.append(parsed)
    return entries


def _parse_attendance_chunk(chunk: list[str]) -> AttendanceEntry | None:
    first = chunk[0]
    match = re.match(
        r"^(?P<start>\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(?P<end>\d{1,2}:\d{2}\s*[AP]M)\s+(?P<body>.+)$",
        first,
        re.IGNORECASE,
    )
    if not match:
        return None

    body = " ".join([match.group("body"), *chunk[1:]]).strip()
    body = re.sub(r"POST AS:\s*.+", "", body, flags=re.IGNORECASE).strip()
    function_name, remainder = _extract_function_and_room(body, return_remainder=True)
    gtd = _extract_last_integer(remainder)
    room = _clean_room(remainder, gtd)
    return AttendanceEntry(
        start=match.group("start"),
        end=match.group("end"),
        function_name=function_name,
        room=room,
        gtd=gtd,
        raw="\n".join(chunk),
    )


def _split_detail_blocks(lines: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    blocks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    detail_started = False

    for entry in lines:
        _, line = entry
        if TIME_ONLY_RE.match(line):
            detail_started = True
            if current:
                blocks.append(current)
            current = [entry]
            continue
        if detail_started and current:
            current.append(entry)
    if current:
        blocks.append(current)
    return blocks


def _extract_function_and_room(value: str, return_remainder: bool = False) -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    for function_name in KNOWN_FUNCTIONS:
        if text.lower().startswith(function_name.lower()):
            remainder = text[len(function_name) :].strip() or None
            return (function_name, remainder) if return_remainder else (function_name, remainder)
    parts = text.split(maxsplit=1)
    function_name = parts[0] if parts else "Unknown"
    remainder = parts[1] if len(parts) > 1 else None
    return (function_name, remainder) if return_remainder else (function_name, remainder)


def _match_attendance(
    entries: list[AttendanceEntry], start: str, function_name: str, room: str | None
) -> AttendanceEntry | None:
    normalized_start = _normalize_time(start)
    normalized_function = function_name.lower()
    normalized_room = (room or "").lower()

    for entry in entries:
        if _normalize_time(entry.start) != normalized_start:
            continue
        if entry.function_name.lower() == normalized_function:
            return entry

    for entry in entries:
        if _normalize_time(entry.start) != normalized_start:
            continue
        if normalized_room and entry.room and normalized_room in entry.room.lower():
            return entry

    for entry in entries:
        if _normalize_time(entry.start) == normalized_start:
            return entry
    return None


def _normalize_time(value: str) -> str:
    return value.upper().replace(".", "").replace(" ", "")


def _extract_last_integer(value: str | None) -> int | None:
    if not value:
        return None
    matches = re.findall(r"\b(\d{1,4})\b", value)
    if not matches:
        return None
    return int(matches[-1])


def _clean_room(value: str | None, gtd: int | None) -> str | None:
    if not value:
        return None
    room = value
    room = re.sub(r"POST AS:\s*.+", "", room, flags=re.IGNORECASE)
    room = re.sub(r"\$\d[\d,.]*", "", room)
    if gtd is not None:
        room = re.sub(rf"\b{gtd}\b", "", room).strip()
    room = " ".join(room.split()).strip(" -")
    return room or None
