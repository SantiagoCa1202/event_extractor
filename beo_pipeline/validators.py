from __future__ import annotations


ALLOWED_CATEGORIES = {
    "buffet",
    "reception",
    "break",
    "plated",
    "station",
    "display",
    "beverage",
    "other_food_service",
}
ALLOWED_MEAL_PERIODS = {"breakfast", "lunch", "dinner", "break", "reception", "unknown"}


def validate_event_payload(event: dict) -> list[str]:
    warnings: list[str] = []
    service = event.get("service", {})
    if service.get("category") not in ALLOWED_CATEGORIES:
        warnings.append(f"Invalid service.category: {service.get('category')}")
    if service.get("meal_period") not in ALLOWED_MEAL_PERIODS:
        warnings.append(f"Invalid service.meal_period: {service.get('meal_period')}")
    if not event.get("details", {}).get("raw"):
        warnings.append("Missing details.raw")
    if not isinstance(event.get("details", {}).get("menu_sections", []), list):
        warnings.append("details.menu_sections must be a list")
    if not isinstance(event.get("notes", []), list):
        warnings.append("notes must be a list")
    return warnings
