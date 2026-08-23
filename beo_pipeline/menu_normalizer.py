from __future__ import annotations

import hashlib
import re

from .schemas import MenuItem


PRICE_SUFFIX_RE = re.compile(r"\s*@\s*\$[\d.,]+(?:\s+per\s+\w+|\s+each)?", re.IGNORECASE)
LEADING_QTY_RE = re.compile(r"^\((\d+)\)\s+(.+)$")
MANUAL_MULTI_ITEM_LINES = {
    "herb marinated chicken breast, garlic & cajun shrimp": [
        "Herb Marinated Chicken Breast",
        "Garlic & Cajun Shrimp",
    ],
    "breakfast pastries, croissants & mini biscuits with strawberry and apricot": [
        "Breakfast Pastries",
        "Croissants",
        "Mini Biscuits",
        "Strawberry",
        "Apricot",
    ],
    "cavatappi carbonara- chicken": [
        "Cavatappi Carbonara",
        "Chicken",
    ],
    "vegetarian penne a la vodka- grilled chicken": [
        "Vegetarian Penne a la Vodka",
        "Grilled Chicken",
    ],
}


def normalize_item_line(line: str) -> list[MenuItem]:
    cleaned = " ".join((line or "").replace("•", " ").replace("â€¢", " ").replace("**", " ").split()).strip(" -")
    if not cleaned:
        return []

    quantity = None
    unit = None
    notes = None

    qty_match = LEADING_QTY_RE.match(cleaned)
    if qty_match:
        quantity = int(qty_match.group(1))
        cleaned = qty_match.group(2).strip()

    cleaned = _strip_service_prefix(cleaned)
    if "per dozen" in cleaned.lower():
        unit = "dozen"
    elif "per gallon" in cleaned.lower():
        unit = "gallon"
    elif re.search(r"\beach\b", cleaned, re.IGNORECASE):
        unit = "each"

    no_price = PRICE_SUFFIX_RE.sub("", cleaned).strip()
    no_price = _normalize_special_cases(no_price)
    if no_price.lower() == "caluiflower":
        no_price = "Cauliflower"
    if "charged on consumption" in no_price.lower():
        notes = "Charged on consumption"
        no_price = re.sub(r"(?i)charged on consumption", "", no_price).strip(", ")

    if no_price.lower() in MANUAL_MULTI_ITEM_LINES:
        return [
            MenuItem(name=name, quantity=None, unit=None, notes=notes, source_text=line)
            for name in MANUAL_MULTI_ITEM_LINES[no_price.lower()]
        ]

    if _should_keep_whole(no_price):
        return [MenuItem(name=no_price, quantity=quantity, unit=unit, notes=notes, source_text=line)]

    parts = []
    for part in re.split(r",|(?<!\w)&(?!\w)|\+", no_price):
        normalized_part = _normalize_special_cases(part.strip(" ."))
        if not normalized_part:
            continue
        parts.extend(MANUAL_MULTI_ITEM_LINES.get(normalized_part.lower(), [normalized_part]))
    if len(parts) <= 1:
        return [MenuItem(name=no_price, quantity=quantity, unit=unit, notes=notes, source_text=line)]
    return [MenuItem(name=part, quantity=None, unit=None, notes=notes, source_text=line) for part in parts]


def normalize_title(value: str) -> str:
    return " ".join((value or "").split()).strip(" -")


def build_menu_fingerprint(items: list[str]) -> str:
    normalized = sorted(_normalize_for_fingerprint(item) for item in items if item)
    payload = "|".join(normalized)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest() if payload else ""


def _normalize_for_fingerprint(value: str) -> str:
    value = re.sub(r"[^a-z0-9\s]+", " ", value.lower())
    return " ".join(value.split())


def _should_keep_whole(value: str) -> bool:
    lower = value.lower()
    preserve_whole_phrases = (
        "garlic & chili broccolini",
        "creamy mac & cheese",
        "mac & cheese",
        "mac & cheese bites",
        "macaroni & cheese bites",
        "garlic & cajun shrimp",
        "butternut squash ravioli - brown butter, pecans, crispy sage",
        "spinach, mushroom, onion, garlic cream sauce",
        "grilled beef coulotte, chimichurri, chipotle aioli",
        "corn & black bean salad",
        "badass bobs pretzels with whole grain mustard",
        "hazel nut crunch cake & brule cheesecake",
        "pimento cheese & pickled shrimp bruschetta crostini",
        "herb goat cheese & tomato jam on crostini",
        "herb goat cheese & tomato jam on crostini passed",
        "assorted granola, protein and breakfast bars",
    )
    if lower in preserve_whole_phrases:
        return True
    guarded_tokens = (
        " with ",
        " on table",
        " offered ",
        " preset ",
        " choice of ",
        "types at",
        " sandwich - ",
        "half and half",
        "served after opening speech",
    )
    if any(token in lower for token in guarded_tokens):
        return True
    if " - " in lower and any(
        token in lower
        for token in (
            "egg patty",
            "american cheese",
            "cheddar cheese",
            "smoked ham",
            "smoked bacon",
            "turkey sausage",
            "pork sage sausage",
        )
    ):
        return True
    return False


def _strip_service_prefix(value: str) -> str:
    return re.sub(r"^\((passed|displayed)\)\s*", "", value, flags=re.IGNORECASE).strip()


def _normalize_special_cases(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"^(?:and\s+)", "", normalized, flags=re.IGNORECASE).strip()
    normalized = re.sub(r"\s+-\s+meck\s*1\s*&\s*2$", "", normalized, flags=re.IGNORECASE).strip()

    lower = normalized.lower()
    replacements = {
        "buffalo sauce on side": "Buffalo Sauce",
        "protein and power bars": "Protein and Breakfast Bars",
        "assorted granola, protein and power bars": "Assorted Granola, Protein and Breakfast Bars",
        "rolls & butter": "Rolls with Butter",
        "assorted rolls & butter": "Assorted Rolls with Butter",
        "macaroni & cheese bites": "Mac & Cheese Bites",
        "mac & cheese bites": "Mac & Cheese Bites",
    }
    return replacements.get(lower, normalized)
