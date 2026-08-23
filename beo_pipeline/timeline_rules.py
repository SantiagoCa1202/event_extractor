from __future__ import annotations

import re
from datetime import datetime, timedelta


SETUP_OFFSET_MINUTES = 30
PICKUP_FOOD_OFFSET_MINUTES = 50
CLEAN_UP_OFFSET_MINUTES = 40
TIME_FORMAT = "%I:%M %p"


def build_timeline(start: str | None, end: str | None) -> dict:
    return {
        "setup": _offset_time(start, SETUP_OFFSET_MINUTES),
        "pickup_food": _offset_time(start, PICKUP_FOOD_OFFSET_MINUTES),
        "service_start": start,
        "service_end": end,
        "clean_up": _offset_time_after(end, CLEAN_UP_OFFSET_MINUTES),
    }


def _offset_time(value: str | None, minutes_before: int) -> str | None:
    if not value:
        return None
    parsed = _parse_time(value)
    adjusted = parsed - timedelta(minutes=minutes_before)
    return adjusted.strftime("%I:%M %p").lstrip("0")


def _offset_time_after(value: str | None, minutes_after: int) -> str | None:
    if not value:
        return None
    parsed = _parse_time(value)
    adjusted = parsed + timedelta(minutes=minutes_after)
    return adjusted.strftime("%I:%M %p").lstrip("0")


def _parse_time(value: str) -> datetime:
    normalized = re.sub(r"\s+", " ", value.strip())
    normalized = re.sub(r"(?i)\b(a|p)\.?m\.?\b", lambda match: f"{match.group(1).upper()}M", normalized)
    normalized = re.sub(r"(?i)(\d)(AM|PM)\b", r"\1 \2", normalized)
    return datetime.strptime(normalized, TIME_FORMAT)
