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
    "Boxed Lunch",
    "Box Lunch",
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
ROOM_SPECS = [
    {
        "canonical": "Executive Boardroom",
        "aliases": ("Executive Boardroom",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "Cardinal Ballroom",
        "aliases": ("Cardinal Ballroom", "Cardinal"),
        "numbers": set(),
        "letters": set(),
        "keywords": {"ballroom", "foyer"},
    },
    {
        "canonical": "Symphony",
        "aliases": ("Symphony",),
        "numbers": {str(value) for value in range(1, 8)},
        "letters": set(),
        "keywords": {"convention", "foyer", "ballroom"},
    },
    {
        "canonical": "Carolina",
        "aliases": ("Carolina",),
        "numbers": set(),
        "letters": {"A", "B", "C", "D", "E"},
        "keywords": {"foyer", "ballroom"},
    },
    {
        "canonical": "Governor's",
        "aliases": ("Governor's", "Governors"),
        "numbers": {str(value) for value in range(1, 7)},
        "letters": set(),
        "keywords": {"foyer", "ballroom"},
    },
    {
        "canonical": "Mecklenburg",
        "aliases": ("Mecklenburg",),
        "numbers": {str(value) for value in range(1, 5)},
        "letters": set(),
        "keywords": {"foyer", "ballroom"},
    },
    {
        "canonical": "LM PDR",
        "aliases": ("LM PDR",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "CJS",
        "aliases": ("CJS",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "Rooftop",
        "aliases": ("Rooftop",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "Lobby",
        "aliases": ("Lobby",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "CCSC",
        "aliases": ("CCSC",),
        "numbers": set(),
        "letters": set(),
        "keywords": set(),
    },
    {
        "canonical": "Convention/Carolina Ballroom Foyer",
        "aliases": ("Convention/Carolina",),
        "numbers": set(),
        "letters": set(),
        "keywords": {"ballroom", "foyer"},
    },
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
    room, gtd = _extract_room_and_gtd(remainder)
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

    if normalized_room:
        for entry in entries:
            if _normalize_time(entry.start) != normalized_start:
                continue
            if entry.room and normalized_room in entry.room.lower() and entry.function_name.lower() == normalized_function:
                return entry

        for entry in entries:
            if _normalize_time(entry.start) != normalized_start:
                continue
            if entry.room and normalized_room in entry.room.lower():
                return entry

    for entry in entries:
        if _normalize_time(entry.start) != normalized_start:
            continue
        if entry.function_name.lower() == normalized_function:
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


def _extract_room_and_gtd(value: str | None) -> tuple[str | None, int | None]:
    cleaned = _strip_room_value(value)
    if not cleaned:
        return None, None

    matched_without_gtd: tuple[str | None, int | None] | None = None
    for candidate in _candidate_room_values(cleaned):
        parsed_room, parsed_gtd = _parse_known_room_and_gtd(candidate)
        if parsed_room:
            if parsed_gtd is not None:
                return parsed_room, parsed_gtd
            if matched_without_gtd is None:
                matched_without_gtd = (parsed_room, parsed_gtd)
    if matched_without_gtd:
        return matched_without_gtd
    return _clean_room(cleaned, None), _extract_last_integer(cleaned)


def _candidate_room_values(value: str) -> list[str]:
    candidates = [value]
    if " - " in value:
        left, right = value.split(" - ", 1)
        if right:
            candidates.insert(0, right.strip())
        if left:
            candidates.append(left.strip())
    return candidates


def _strip_room_value(value: str | None) -> str | None:
    if not value:
        return None
    room = value
    room = re.sub(r"POST AS:\s*.+", "", room, flags=re.IGNORECASE)
    room = re.sub(r"\$\d[\d,.]*", "", room)
    room = " ".join(room.split()).strip(" -")
    return room or None


def _parse_known_room_and_gtd(value: str) -> tuple[str | None, int | None]:
    for spec in ROOM_SPECS:
        matched_alias = _match_room_alias(value, spec["aliases"])
        if not matched_alias:
            continue

        suffix = value[len(matched_alias) :].strip()
        room_parts = [spec["canonical"]]
        numeric_columns: list[int] = []
        previous_was_room_token = False

        for token in suffix.split():
            normalized = token.strip(",;").upper()
            lower_token = normalized.lower()
            if token == "&" and previous_was_room_token:
                room_parts.append("&")
                previous_was_room_token = False
                continue
            if normalized in spec["numbers"]:
                room_parts.append(normalized)
                previous_was_room_token = True
                continue
            if normalized in spec["letters"]:
                room_parts.append(normalized)
                previous_was_room_token = True
                continue
            if lower_token in spec["keywords"]:
                keyword = token.strip(",;").title()
                if keyword.lower() not in " ".join(room_parts).lower().split():
                    room_parts.append(keyword)
                previous_was_room_token = True
                continue
            if re.fullmatch(r"\d{1,4}", normalized):
                numeric_columns.append(int(normalized))
                previous_was_room_token = False
                continue
            break

        room = " ".join(room_parts).strip()
        return room or None, _infer_gtd_from_trailing_columns(numeric_columns)

    return None, None


def _match_room_alias(value: str, aliases: tuple[str, ...]) -> str | None:
    lowered = value.lower()
    for alias in sorted(aliases, key=len, reverse=True):
        alias_lower = alias.lower()
        if lowered == alias_lower or lowered.startswith(f"{alias_lower} "):
            return value[: len(alias)]
    return None


def _infer_gtd_from_trailing_columns(columns: list[int]) -> int | None:
    if not columns:
        return None
    if len(columns) == 1:
        return columns[0]
    if len(columns) == 2:
        return columns[0]
    if len(columns) == 3:
        return columns[1]
    return columns[-1]


def _clean_room(value: str | None, gtd: int | None) -> str | None:
    room = _strip_room_value(value)
    if not room:
        return None
    if gtd is not None:
        room = re.sub(rf"\b{gtd}\b", "", room).strip()
    room = " ".join(room.split()).strip(" -")
    return room or None
