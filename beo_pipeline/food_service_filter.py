from __future__ import annotations

import re


NEGATIVE_PATTERNS = (
    r"no food or beverage required at this time",
    r"no food required",
    r"no beverage required",
    r"group to visit .+ from \d{1,2}:\d{2}\s*[ap]m",
    r"group will order drinks .+ on own",
    r"group will have one tab for all guests",
    r"group to go off.?site for dinner",
    r"settle bill by credit card at event conclusion",
    r"setlle bill by credit card at event conclusion",
    r"should inclemement weather cause reception to be moved",
    r"please reserve semi.?private space",
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

NON_QUALIFYING_BEVERAGE_TERMS = {
    "water station",
    "bottled water",
    "assorted pepsi products",
    "assorted pepsi sodas",
    "soft drinks",
    "pepsi sodas",
    "pepsi products",
}

QUALIFYING_BEVERAGE_TERMS = {
    "coffee",
    "tea",
    "bar",
    "wine",
    "beer",
    "bourbon",
    "cocktail",
}


def is_food_service_function(
    function_name: str,
    raw_block: str,
    menu_item_count: int = 0,
    item_names: list[str] | None = None,
) -> tuple[bool, list[str]]:
    text = (raw_block or "").lower()
    reasons: list[str] = []
    normalized_items = [item.lower() for item in (item_names or []) if item]

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

    if reasons and _is_non_qualifying_beverage_only(text, normalized_items):
        return False, ["excluded_non_food_beverage_service"]

    return bool(reasons), reasons


def _is_non_qualifying_beverage_only(text: str, item_names: list[str]) -> bool:
    searchable = [text, *item_names]
    has_excluded = any(any(term in value for term in NON_QUALIFYING_BEVERAGE_TERMS) for value in searchable)
    has_qualifying = any(any(term in value for term in QUALIFYING_BEVERAGE_TERMS) for value in searchable)

    if not has_excluded:
        return False

    food_terms_without_excluded = [
        term
        for term in FOOD_SERVICE_TERMS
        if term not in NON_QUALIFYING_BEVERAGE_TERMS and term not in {"beverage", "station", "water station", "soda"}
    ]
    has_other_food_signal = any(any(term in value for term in food_terms_without_excluded) for value in searchable)
    return not has_qualifying and not has_other_food_signal
