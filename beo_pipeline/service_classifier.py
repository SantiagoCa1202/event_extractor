from __future__ import annotations

from .schemas import MenuSection


def classify_service(function_name: str, raw_block: str, menu_sections: list[MenuSection]) -> dict[str, str]:
    text = f"{function_name}\n{raw_block}".lower()
    titles = " ".join(section.title.lower() for section in menu_sections)

    category = "other_food_service"
    if "plated" in text:
        category = "plated"
    elif "reception" in text:
        category = "reception"
    elif "coffee break" in text or "beverage break" in text or function_name.lower() == "break":
        category = "break"
    elif "buffet" in text:
        category = "buffet"
    elif "station" in text:
        category = "station"
    elif "display" in text:
        category = "display"
    elif _is_beverage_only(menu_sections):
        category = "beverage"

    meal_period = "unknown"
    if "breakfast" in text or "continental" in titles:
        meal_period = "breakfast"
    elif "lunch" in text:
        meal_period = "lunch"
    elif "dinner" in text:
        meal_period = "dinner"
    elif category == "break":
        meal_period = "break"
    elif category == "reception":
        meal_period = "reception"

    subtype = _derive_subtype(function_name, raw_block, menu_sections)

    return {
        "category": category,
        "meal_period": meal_period,
        "subtype": subtype,
    }


def _is_beverage_only(menu_sections: list[MenuSection]) -> bool:
    if not menu_sections:
        return False
    return all(section.course_type == "beverage" or section.type == "beverage" for section in menu_sections)


def _derive_subtype(function_name: str, raw_block: str, menu_sections: list[MenuSection]) -> str:
    candidates = [function_name.strip()]
    candidates.extend(section.title for section in menu_sections if section.title and section.title.lower() != "items")
    for candidate in candidates:
        if candidate:
            return candidate
    return (raw_block or "").splitlines()[0].strip() if raw_block else function_name
