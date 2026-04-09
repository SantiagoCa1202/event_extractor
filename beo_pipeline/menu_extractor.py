from __future__ import annotations

import re

from .menu_normalizer import normalize_item_line, normalize_title
from .schemas import MenuItem, MenuSection


NOISE_PATTERNS = (
    r"^event order page #",
    r"^sheraton charlotte hotel event order #",
    r"^\d+\s+south mcdowell street",
    r"^phone:\(",
    r"^function day/date:",
    r"^organization:",
    r"^date printed:",
    r"^billing address:",
    r"^customer:",
    r"^in-house contact:",
    r"^managers:",
    r"^marriott proprietary",
    r"^charged on consumption",
    r"^based on ",
    r"^\$\d",
    r"^post as:",
    r"^special$",
    r"^arrangements$",
    r"^room setup",
    r"^\(.+\)$",
)

TITLE_HINTS = ("display", "station", "bar", "buffet", "continental", "break", "table")
SNACK_HINTS = ("granola bar", "chips", "candy bar", "protein bar", "pastries", "whole fruit", "lemon bars", "cookies", "popcorn", "pretzels")
BEVERAGE_HINTS = ("coffee", "tea", "juice", "water", "pepsi", "soda", "iced tea", "wine", "beer", "bourbon", "scotch")
FOOD_BAR_HINTS = ("mac n' cheese", "mac and cheese", "potato", "taco", "nacho", "slider", "pasta", "grits")
MENU_STYLE_ONLY_TITLES = ("the queens table",)
EXCLUDED_NON_AREA_ITEM_PATTERNS = (
    r"^assorted cereals$",
    r"^starbucks regular$",
    r"^starbucks coffee$",
    r"^starbucks .+ coffee$",
    r"^decaf coffee$",
    r"^tea$",
    r"^orange juice$",
    r"^tractor iced tea$",
    r"^tractor iced tea & starbucks coffee$",
    r"^tractor iced tea\s*&\s*starbucks coffee.*$",
    r"^freshly brewed .+ coffee.*$",
    r"^assorted (tazo|teavana) teas?( and condiments)?$",
    r"^assorted pepsi sodas$",
    r"^bottled water[s]?$",
    r"^tractor .+ iced tea$",
    r"^seasonal fruit beverage$",
    r"^to include sweeteners$",
    r"^dairy$",
    r"^non dairy add-ins$",
)
PENDING_PLACEHOLDER_PATTERNS = (
    r"^chef'?s choice\s*-\s*assorted variety$",
)
COURSE_HINTS = {
    "salad": "salad",
    "greens": "salad",
    "entree": "entree",
    "chicken": "entree",
    "salmon": "entree",
    "tenderloin": "entree",
    "dessert": "dessert",
    "cake": "dessert",
    "beverage": "beverage",
    "coffee": "beverage",
}


def extract_menu_sections(raw_block: str) -> list[MenuSection]:
    lines = [_clean_line(line) for line in (raw_block or "").splitlines()]
    lines = [line for line in lines if line and not _is_noise(line)]
    lines = _merge_broken_menu_lines(lines)
    if not lines:
        return []

    sections: list[MenuSection] = []
    current: MenuSection | None = None

    for line in lines:
        if _is_pending_placeholder(line):
            continue

        if _looks_like_block_header(line):
            continue

        if current is not None and _looks_like_priced_item(line):
            current.items.extend(normalize_item_line(line))
            continue

        if current is not None and _starts_new_plated_item_section(current, line):
            current = _create_section("Items")
            sections.append(current)
            current.items.extend(normalize_item_line(line))
            continue

        if _starts_snack_section(line, current):
            current = _create_section("", preferred_type="snack_items")
            sections.append(current)

        if current is not None and current.type == "snack_items":
            current.items.extend(normalize_item_line(line))
            continue

        if current is not None and _looks_like_simple_item(line):
            current.items.extend(normalize_item_line(line))
            continue

        colon_match = re.match(r"^(Sides|Dessert|Beverages?|Choice of Two Proteins|Greens\s*&\s*Toppings)\s*:\s*(.+)$", line, re.IGNORECASE)
        if colon_match:
            current = _create_section(colon_match.group(1))
            if current.title == "Greens & Toppings":
                current.items.extend(_split_greens_and_toppings_items(colon_match.group(2)))
            else:
                current.items.extend(normalize_item_line(colon_match.group(2)))
            sections.append(current)
            continue

        salad_inline_match = re.match(r"^(Mixed Green Salad|Mixed Greens Salad)\s*,\s*(.+)$", line, re.IGNORECASE)
        if salad_inline_match:
            current = _create_section(salad_inline_match.group(1))
            current.items.extend(_split_salad_dash_items(salad_inline_match.group(2)))
            sections.append(current)
            continue

        dash_match = re.match(r"^([A-Za-z' ]{3,40})\s*-\s*(.+)$", line)
        if dash_match and _looks_like_dash_title(dash_match.group(1)):
            current = _create_section(dash_match.group(1))
            current.items.extend(_extract_dash_section_items(current, dash_match.group(2)))
            sections.append(current)
            continue

        if _looks_like_title(line):
            if _is_menu_style_only_title(line):
                continue
            current = _create_section(line)
            sections.append(current)
            continue

        if current is None:
            current = _create_section("Items")
            sections.append(current)

        current.items.extend(normalize_item_line(line))

    processed = [_post_process_section(section) for section in sections]
    return [section for section in processed if section.items or _should_keep_empty_section(section)]


def derive_menu_style(raw_block: str, sections: list[MenuSection]) -> str | None:
    for line in (_clean_line(line) for line in (raw_block or "").splitlines()):
        if line and _is_menu_style_only_title(line):
            return normalize_title(line)
    for section in sections:
        title = section.title.lower()
        if title not in {"items", "beverages", "sides", "dessert"}:
            return section.title
    for line in (_clean_line(line) for line in (raw_block or "").splitlines()):
        if line and not _is_noise(line) and not _looks_like_block_header(line):
            if _looks_like_title(line):
                return normalize_title(line)
    return None


def _clean_line(line: str) -> str:
    return " ".join((line or "").replace("\t", " ").split()).strip()


def _is_noise(line: str) -> bool:
    lower = line.lower()
    if _is_special_plate_count(line):
        return False
    return any(re.search(pattern, lower) for pattern in NOISE_PATTERNS)


def _looks_like_block_header(line: str) -> bool:
    return bool(re.match(r"^\d{1,2}:\d{2}\s*[AP]M\b", line, re.IGNORECASE))


def _looks_like_title(line: str) -> bool:
    lower = line.lower()
    if _contains_title_hint(lower):
        return True
    if " with " in lower:
        return False
    if len(line.split()) <= 4 and not re.search(r"[@$,]", line):
        return True
    return False


def _looks_like_simple_item(line: str) -> bool:
    lower = line.lower()
    if _contains_title_hint(lower):
        return False
    if re.search(r"[@$:]", line):
        return False
    return len(line.split()) <= 4


def _looks_like_priced_item(line: str) -> bool:
    return bool(re.match(r"^\(\d+\)\s+.+@\s*\$[\d.]+", line))


def _looks_like_dash_title(value: str) -> bool:
    lower = value.lower().strip()
    dash_title_hints = ("greens", "salad", "dessert", "sides", "beverages", "chef's choice")
    return any(hint in lower for hint in dash_title_hints)


def _starts_snack_section(line: str, current: MenuSection | None) -> bool:
    if current is None:
        return False
    if current.type != "break_items":
        return False
    lower = line.lower()
    return any(hint in lower for hint in SNACK_HINTS) and "charged on consumption" not in lower


def _create_section(title: str, preferred_type: str | None = None) -> MenuSection:
    title = normalize_title(title)
    lower = title.lower()
    if preferred_type == "snack_items":
        section_type = "snack_items"
        role = "bar"
        course_type = "break"
        return MenuSection(title=title, type=section_type, service_role=role, course_type=course_type)
    if "greens & toppings" in lower:
        section_type = "cold_items"
        role = "buffet"
    elif "display" in lower:
        section_type = "display"
        role = "display"
    elif "bar" in lower and any(hint in lower for hint in FOOD_BAR_HINTS):
        section_type = "station_items"
        role = "station"
    elif "station" in lower:
        section_type = "station_items"
        role = "station"
    elif "bar" in lower:
        section_type = "beverage"
        role = "bar"
    elif "break" in lower or "continental" in lower:
        section_type = "break_items"
        role = "break"
    elif any(hint in lower for hint in BEVERAGE_HINTS):
        section_type = "beverage"
        role = "other"
    else:
        section_type = "course"
        role = "other"

    course_type = "other"
    for key, mapped in COURSE_HINTS.items():
        if key in lower:
            course_type = mapped
            break
    if section_type == "station_items" and course_type == "beverage":
        course_type = "other"
    if section_type == "beverage":
        course_type = "beverage"

    return MenuSection(title=title, type=section_type, service_role=role, course_type=course_type)


def _post_process_section(section: MenuSection) -> MenuSection:
    quantity_only_items = []
    for item in section.items:
        name = (item.name or "").strip().lower()
        if re.fullmatch(r"\d+\s+each", name):
            quantity_only_items.append(item)

    if quantity_only_items:
        sandwich_items = [
            item
            for item in section.items
            if _is_breakfast_sandwich_variant(item.name or "")
        ]
        for quantity_item in quantity_only_items:
            match = re.fullmatch(r"(\d+)\s+(each)", quantity_item.name.strip().lower())
            if match and sandwich_items:
                qty = int(match.group(1))
                unit = match.group(2)
                for sandwich_item in sandwich_items:
                    if sandwich_item.quantity is None:
                        sandwich_item.quantity = qty
                        sandwich_item.unit = unit
        section.items = [item for item in section.items if item not in quantity_only_items]

    sandwich_items = [item for item in section.items if _is_breakfast_sandwich_variant(item.name or "")]
    if sandwich_items:
        aggregate_items = [
            item
            for item in section.items
            if (item.name or "").strip().lower() in {"breakfast sandwiches"}
        ]
        if aggregate_items:
            section.items = [item for item in section.items if item not in aggregate_items]

    section.items = _expand_oatmeal_with_accompaniments(section.items)
    _apply_special_dietary_counts(section)

    section.items = [
        item for item in section.items if not _is_excluded_non_area_item(item.name or "")
    ]

    return section


def _is_breakfast_sandwich_variant(value: str) -> bool:
    lower = value.lower()
    variant_hints = ("sandwich -", "muffin -", "bagel sandwich", "biscuit sandwich", "croissant sandwich", "english muffin -")
    return any(hint in lower for hint in variant_hints)


def _is_excluded_non_area_item(value: str) -> bool:
    lower = value.strip().lower()
    return any(re.fullmatch(pattern, lower) for pattern in EXCLUDED_NON_AREA_ITEM_PATTERNS)


def _contains_title_hint(lower: str) -> bool:
    return any(re.search(rf"\b{re.escape(hint)}\b", lower) for hint in TITLE_HINTS)


def _is_menu_style_only_title(value: str) -> bool:
    lower = value.strip().lower()
    return lower in MENU_STYLE_ONLY_TITLES


def _should_keep_empty_section(section: MenuSection) -> bool:
    return section.type in {"display", "station_items"} and bool(section.title)


def _is_pending_placeholder(value: str) -> bool:
    lower = value.strip().lower()
    return any(re.fullmatch(pattern, lower) for pattern in PENDING_PLACEHOLDER_PATTERNS)


def _merge_broken_menu_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        if (
            current.endswith(", White")
            and index + 1 < len(lines)
            and lines[index + 1].strip().lower() == "balsamic dressing"
        ):
            merged.append(f"{current} Balsamic Dressing")
            index += 2
            continue
        merged.append(current)
        index += 1
    return merged


def _split_greens_and_toppings_items(value: str) -> list:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return [normalize_item_line(part)[0] for part in parts if normalize_item_line(part)]


def _expand_oatmeal_with_accompaniments(items: list[MenuItem]) -> list[MenuItem]:
    expanded: list[MenuItem] = []
    for item in items:
        match = re.match(r"^(steel cut oatmeal)\s+with\s+(.+)$", (item.name or "").strip(), re.IGNORECASE)
        if not match:
            expanded.append(item)
            continue

        expanded.append(
            MenuItem(
                name="Steel Cut Oatmeal",
                quantity=item.quantity,
                unit=item.unit,
                notes=item.notes,
                source_text=item.source_text,
            )
        )
        accompaniments = re.split(r",|&|\band\b", match.group(2))
        for part in accompaniments:
            name = part.strip(" .")
            if not name:
                continue
            expanded.append(
                MenuItem(
                    name=name,
                    quantity=None,
                    unit=None,
                    notes=item.notes,
                    source_text=item.source_text,
                )
            )
    return expanded


def _starts_new_plated_item_section(current: MenuSection, line: str) -> bool:
    lower = line.lower()
    if current.course_type != "salad":
        return False
    if any(keyword in lower for keyword in ("ranch", "vinaigrette", "dressing")):
        return False
    if lower.startswith(("cucumber", "radish", "tomatoes", "carrots", "mixed greens")):
        return False
    return " with " in lower or any(
        protein in lower for protein in ("chicken", "salmon", "steak", "pork", "dessert", "rolls")
    )


def _extract_dash_section_items(section: MenuSection, value: str) -> list:
    if section.course_type == "salad" or "greens" in section.title.lower():
        return _split_salad_dash_items(value)
    return normalize_item_line(value)


def _split_salad_dash_items(value: str) -> list:
    cleaned = re.sub(r"(?i)\bon table\b", "", value).strip(" ,")
    cleaned = re.sub(r"(?i)\bon tables\b", "", cleaned).strip(" ,")
    cleaned = re.sub(r"(?i)\b(radish)\s+(ranch)\b", r"\1, \2", cleaned)
    if not cleaned:
        return []
    protected = cleaned.replace(" and ", ", ")
    parts = [part.strip() for part in protected.split(",") if part.strip()]
    items = []
    for part in parts:
        normalized = normalize_item_line(part)
        if normalized:
            items.append(normalized[0])
    return items


def _apply_special_dietary_counts(section: MenuSection) -> None:
    special_items = [
        item
        for item in section.items
        if _is_special_plate_count(item.source_text or "") or _is_special_plate_label(item)
    ]
    if not special_items:
        return

    target = next(
        (
            item
            for item in reversed(section.items)
            if item not in special_items and not _is_excluded_non_area_item(item.name or "")
        ),
        None,
    )
    if target is not None:
        notes = [target.notes] if target.notes else []
        notes.extend(item.source_text or item.name for item in special_items)
        target.notes = " | ".join(notes)

    section.items = [item for item in section.items if item not in special_items]


def _is_special_plate_count(value: str) -> bool:
    lower = value.strip().lower()
    if not re.match(r"^\(?\d+\)?\s+", lower):
        return False
    return any(keyword in lower for keyword in ("vegan", "vegetarian", "vegeterian", "gluten free", "gluten-free"))


def _is_special_plate_label(item) -> bool:
    lower = (item.name or "").strip().lower()
    if item.quantity is None:
        return False
    return any(keyword in lower for keyword in ("vegan", "vegetarian", "vegeterian", "gluten free", "gluten-free"))
