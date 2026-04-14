from __future__ import annotations

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
    parsed = datetime.strptime(value, TIME_FORMAT)
    adjusted = parsed - timedelta(minutes=minutes_before)
    return adjusted.strftime("%I:%M %p").lstrip("0")


def _offset_time_after(value: str | None, minutes_after: int) -> str | None:
    if not value:
        return None
    parsed = datetime.strptime(value, TIME_FORMAT)
    adjusted = parsed + timedelta(minutes=minutes_after)
    return adjusted.strftime("%I:%M %p").lstrip("0")
