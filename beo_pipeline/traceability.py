from __future__ import annotations

from itertools import groupby


def format_page_ranges(page_numbers: list[int]) -> list[str]:
    if not page_numbers:
        return []
    sorted_pages = sorted(set(page_numbers))
    ranges: list[str] = []
    for _, group in groupby(enumerate(sorted_pages), lambda item: item[1] - item[0]):
        values = [value for _, value in group]
        ranges.append(f"{values[0]}-{values[-1]}" if len(values) > 1 else str(values[0]))
    return ranges


def summarize_snippets(raw_text: str, max_snippets: int = 4) -> list[str]:
    snippets: list[str] = []
    for line in raw_text.splitlines():
        cleaned = " ".join(line.split()).strip()
        if cleaned and cleaned not in snippets:
            snippets.append(cleaned[:240])
        if len(snippets) >= max_snippets:
            break
    return snippets


def infer_confidence(has_attendance_match: bool, menu_item_count: int, reason_count: int) -> str:
    if has_attendance_match and menu_item_count >= 3:
        return "high"
    if menu_item_count >= 1 or reason_count >= 2:
        return "medium"
    return "low"
