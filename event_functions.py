import re


_FUNCTION_VARIANTS = [
    "Cocktail Reception",
    "Reception",
    "Breakfast Buffet",
    "Continental Breakfast",
    "Breakfast",
    "Lunch Buffet",
    "Plated Lunch",
    "Lunch",
    "Dinner Buffet",
    "Plated Dinner",
    "Dinner",
    "Coffee Break",
    "Continuous Break",
    "Break",
    "Menu Tasting",
    # Funciones no estandar que a veces traen comida
    "Meeting",
    "Team Meeting",
    "Board Meeting",
    "Breakout",
    "Breakout Session",
    "General Session",
    "Session",
    "Workshop",
    "Seminar",
    "Training",
    "Conference",
    "Forum",
    "Summit",
]

EVENT_FUNCTION_REGEX_FRAGMENT = "(?:" + "|".join(v.replace(" ", r"\s+") for v in _FUNCTION_VARIANTS) + ")"
FUNCTION_KEYWORDS = {variant.lower() for variant in _FUNCTION_VARIANTS}

_NORMALIZED_CANONICAL = {
    "cocktail reception": "Cocktail Reception",
    "reception": "Reception",
    "breakfast buffet": "Breakfast Buffet",
    "continental breakfast": "Breakfast Buffet",
    "breakfast": "Breakfast",
    "lunch buffet": "Lunch Buffet",
    "plated lunch": "Plated Lunch",
    "lunch": "Lunch",
    "dinner buffet": "Dinner Buffet",
    "plated dinner": "Plated Dinner",
    "dinner": "Dinner",
    "coffee break": "Coffee Break",
    "continuous break": "Break",
    "break": "Break",
    "menu tasting": "Menu Tasting",
    "meeting": "Meeting",
    "team meeting": "Meeting",
    "board meeting": "Meeting",
    "breakout": "Breakout",
    "breakout session": "Breakout",
    "general session": "Session",
    "session": "Session",
    "workshop": "Workshop",
    "seminar": "Session",
    "training": "Session",
    "conference": "Session",
    "forum": "Session",
    "summit": "Session",
}

_FUNCTION_FAMILY = {
    "Cocktail Reception": "reception",
    "Reception": "reception",
    "Breakfast Buffet": "breakfast",
    "Breakfast": "breakfast",
    "Lunch Buffet": "lunch",
    "Plated Lunch": "lunch",
    "Lunch": "lunch",
    "Dinner Buffet": "dinner",
    "Plated Dinner": "dinner",
    "Dinner": "dinner",
    "Coffee Break": "break",
    "Break": "break",
    "Menu Tasting": "menu_tasting",
    "Meeting": "conditional",
    "Breakout": "conditional",
    "Session": "conditional",
    "Workshop": "conditional",
}

_CONDITIONAL_FUNCTIONS = {"Meeting", "Breakout", "Session", "Workshop"}


def normalize_function_name(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", (value or "").strip()).lower()
    return _NORMALIZED_CANONICAL.get(cleaned, cleaned.title())


def function_family(value: str) -> str:
    normalized = normalize_function_name(value)
    return _FUNCTION_FAMILY.get(normalized, normalized.lower())


def same_event_function(a: str, b: str) -> bool:
    na = normalize_function_name(a)
    nb = normalize_function_name(b)
    return na == nb or function_family(na) == function_family(nb)


def requires_food_validation(value: str) -> bool:
    return normalize_function_name(value) in _CONDITIONAL_FUNCTIONS
