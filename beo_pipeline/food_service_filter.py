from __future__ import annotations

import re


NEGATIVE_PATTERNS = (
    r"no food or beverage required at this time",
    r"no food required",
    r"no beverage required",
)

FOOD_SERVICE_TERMS = {
    "breakfast",
    "lunch",
    "dinner",
    "buffet",
    "plated",
    "reception",
    "coffee",
    "tea",
    "beverage",
    "bar",
    "water station",
    "soda",
    "juice",
    "display",
    "station",
    "hors",
    "dessert",
    "snack",
    "granola",
    "chips",
    "pastries",
    "fruit",
    "cheese",
    "charcuterie",
    "salmon",
    "chicken",
    "tenderloin",
    "beef",
    "pork",
    "coffee break",
    "iced tea",
    "bottled water",
}

FUNCTION_HINT_TERMS = {
    "break",
    "breakfast buffet",
    "lunch buffet",
    "plated lunch",
    "plated dinner",
    "reception",
    "coffee break",
    "continental breakfast",
    "breakfast",
    "lunch",
    "dinner",
}


def is_food_service_function(function_name: str, raw_block: str, menu_item_count: int = 0) -> tuple[bool, list[str]]:
    text = (raw_block or "").lower()
    reasons: list[str] = []

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text):
            return False, [f"negative_phrase:{pattern}"]

    normalized_name = (function_name or "").strip().lower()
    if normalized_name in FUNCTION_HINT_TERMS:
        reasons.append(f"function_hint:{normalized_name}")

    matched_terms = sorted(term for term in FOOD_SERVICE_TERMS if term in text)
    if matched_terms:
        reasons.append(f"food_terms:{', '.join(matched_terms[:6])}")

    if menu_item_count > 0:
        reasons.append(f"menu_items:{menu_item_count}")

    return bool(reasons), reasons
