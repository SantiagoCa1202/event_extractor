from __future__ import annotations

import re
from typing import Any

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
    r"^note$",
    r"^\d+\s*-\s*vegetarian/vegan$",
    r"^\d+\s*-\s*gluten free$",
    r"^arrangements$",
    r"^room setup",
    r"^\(.+\)$",
    r"^soft drinks and bottled water$",
    r"^complimentary per contract$",
    r"^available upon request$",
    r"^breaks in foyer$",
    r"^breaks on foyer$",
    r"^start with \d+",
    r"^and a selection of hot tazo teas$",
    r"^assorted pepsi soft drinks$",
    r"^lemonade$",
    r"^decoration provided by extravaganza events",
    r"^house wine$",
    r"^red wine$",
    r"^rose wine$",
    r"^white wine$",
    r"^wine is only served upon request",
    r"^chef attendant",
    r"^\(\d+\)\s*chef attendant",
    r"^on consumption available",
    r"^waters$",
    r"^tractor organic artisan ice tea$",
    r"^open symphony ballroom doors",
    r"^food \d{1,2}:\d{2}",
    r"^\**\s*\(\d+\)\s+bars to serve",
    r"^wine only$",
    r"^\**\s*no tequila to be served at bars$",
    r"^\**\s*client request",
    r"^must serve mixed$",
    r"^drinks only$",
    r"^after dinner$",
    r"^\**\s*\(.+\)\s+.*bar.+move into ballroom$",
    r"^\**\s*dietary needs in food header below:?$",
    r"^please leave non-perishable items out until end of morning break\b",
    r"^[o]\s*(?:\(cid:\d+\))?\s*(?:breakfast|lunch|dinner)\s+options\s+for\s+dr\.?\s+.+:?$",
)
CONTRACTUAL_NOISE_PATTERNS = (
    r"^guarantees are required\b",
    r"^any room set changes within\b",
    r"^absolutely no outside food\b",
    r"^beverage allowed unless determined at contract signing\b",
    r"^hotel will assess fees for\b",
    r"^each infraction\.?$",
    r"^a service charge of\b",
    r"^which will be provided to wait staff\b",
    r"^employee\b",
    r"^service employees and/or service bartenders\b",
    r"^banquet function\b",
    r"^the hotel will retain the portion of their service charge\b",
    r"^staffing for the function\b",
    r"^and the service charge is not the property of those third.?party employees\b",
    r"^administrative fee of\b",
    r"^administrative fee is retained by the hotel\b",
    r"^is not a tip\b",
    r"^gratuity or service charge for any employee\b",
    r"^property of the employee\(s\) providing service to you\b",
    r"^group to visit\b",
    r"^group will order drinks\b",
    r"^group will have one tab\b",
    r"^group to go offsite\b",
    r"^group to go off.?site\b",
    r"^will settle bill by credit card\b",
    r"^group will order drinks .+ and will setlle bill by credit card\b",
    r"^should inclemement weather cause reception to be moved\b",
    r"^please reserve semi.?private space\b",
)

TITLE_HINTS = (
    "display",
    "station",
    "bar",
    "buffet",
    "continental",
    "break",
    "table",
    "greens",
    "condiments",
    "passed",
    "displayed",
    "preset salad",
    "preset alternating dessert",
    "duo plate meal",
)
SNACK_HINTS = (
    "granola bar",
    "chips",
    "candy bar",
    "protein bar",
    "pastries",
    "whole fruit",
    "lemon bars",
    "cookies",
    "popcorn",
    "pretzels",
)
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
    r"^soft drinks and bottled water$",
    r"^complimentary per contract$",
    r"^available upon request$",
    r"^cheerwine soda$",
    r"^breaks in foyer$",
    r"^breaks on foyer$",
    r"^house wine$",
    r"^red wine$",
    r"^rose wine$",
    r"^white wine$",
)
PENDING_PLACEHOLDER_PATTERNS = (
    r"^chef'?s choice\s*-\s*assorted variety$",
    r"^menu tbd\b.*$",
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
PASSED_PREFIX_RE = re.compile(r"^\(passed\)\s*", re.IGNORECASE)
DISPLAYED_PREFIX_RE = re.compile(r"^\(displayed\)\s*", re.IGNORECASE)
TITLE_VALUE_PREFIX_RE = re.compile(
    r"^(chef'?s choice|preset salad choice|preset salad|salad choice|salad|dessert choice|dessert|entree choice|entree)\s*\(?(?:title)?\)?\s*:\s*(.+)$",
    re.IGNORECASE,
)
ASSORTED_BAGS_TITLE_RE = re.compile(r"^(assorted bags? of)\s+(.+)$", re.IGNORECASE)
MANUAL_COMBINE_PAIRS = {
    ("garlic", "chili broccolini"): "Garlic & Chili Broccolini",
    ("creamy mac", "cheese"): "Creamy Mac & Cheese",
    ("(displayed) macaroni", "cheese bites"): "(Displayed) Macaroni & Cheese Bites",
}
TITLE_ALIASES = {
    "boxed lunch": "Boxed Lunch",
    "box lunch": "Boxed Lunch",
    "greens": "Greens",
    "condiments": "Condiments",
    "passed": "Passed",
    "displayed": "Displayed",
    "preset salad": "Preset Salad",
    "preset salad choice": "Preset Salad Choice",
    "salad": "Salad",
    "salad choice": "Salad Choice",
    "entree": "Entree",
    "entree choice": "Entree Choice",
    "dessert": "Dessert",
    "dessert choice": "Dessert Choice",
    "preset alternating dessert": "Preset Alternating Dessert",
    "duo plate meal (served after opening speech)": "Duo Plate Meal (Served After Opening Speech)",
}
INLINE_MENU_SECTION_TITLES = {
    "greens",
    "greens & toppings",
    "breads",
    "spreads",
    "boards head meats",
    "cheese",
    "condiments",
    "dessert",
    "country potato salad",
}
JOINED_SECTION_TITLES = {
    "preset salad",
    "preset salad choice",
    "salad",
    "salad choice",
    "entree",
    "entree choice",
    "dessert",
    "dessert choice",
    "duo plate meal (served after opening speech)",
    "preset alternating dessert",
}


def extract_dietary_restrictions(raw_block: str) -> tuple[str, list[dict[str, Any]]]:
    lines = (raw_block or "").splitlines()
    cleaned_lines: list[str] = []
    restrictions: list[dict[str, Any]] = []
    collecting = False

    for raw_line in lines:
        line = _clean_line(raw_line)
        lower = line.lower()
        special_count = _parse_special_dietary_count_line(line)
        if special_count is not None:
            restrictions.append(special_count)
            continue
        if lower in {"dietary restrictions", "dietary restrictions:", "dietary:", "dietary"}:
            collecting = True
            continue

        if collecting:
            if not line:
                continue
            if _is_noise(line):
                continue
            if _looks_like_block_header(line) or lower.startswith("room setup"):
                collecting = False
                cleaned_lines.append(raw_line)
                continue
            if _is_dietary_note_line(line):
                continue

            parsed = _parse_dietary_restriction_line(line)
            if parsed is not None:
                restrictions.append(parsed)
                continue

            collecting = False

        cleaned_lines.append(raw_line)

    cleaned_raw = "\n".join(line for line in cleaned_lines if line is not None)
    return cleaned_raw, restrictions


def extract_menu_sections(raw_block: str) -> list[MenuSection]:
    lines = [_clean_line(line) for line in (raw_block or "").splitlines()]
    lines = [line for line in lines if line and not _is_noise(line)]
    lines = _apply_manual_line_rules(_merge_broken_menu_lines(lines))
    if not lines:
        return []

    sections: list[MenuSection] = []
    current: MenuSection | None = None
    skipping_dietary_guidance = False

    for line in lines:
        if _is_dietary_guidance_header(line):
            skipping_dietary_guidance = True
            continue

        if skipping_dietary_guidance:
            if _looks_like_block_header(line) or _ends_dietary_guidance_block(line):
                skipping_dietary_guidance = False
            else:
                continue

        if _is_pending_placeholder(line):
            continue

        if _looks_like_block_header(line):
            continue

        title_value_match = TITLE_VALUE_PREFIX_RE.match(line)
        if title_value_match:
            current = _create_section(title_value_match.group(1))
            sections.append(current)
            current.items.extend(normalize_item_line(title_value_match.group(2)))
            continue

        assorted_bags_match = ASSORTED_BAGS_TITLE_RE.match(line)
        if assorted_bags_match:
            current = _create_section(assorted_bags_match.group(1))
            current.items.extend(_split_greens_and_toppings_items(assorted_bags_match.group(2)))
            sections.append(current)
            continue

        if PASSED_PREFIX_RE.match(line):
            if current is None or current.title != "Passed":
                current = _create_section("Passed")
                sections.append(current)
            current.items.extend(normalize_item_line(PASSED_PREFIX_RE.sub("", line)))
            continue

        if DISPLAYED_PREFIX_RE.match(line):
            if current is None or current.title != "Displayed":
                current = _create_section("Displayed")
                sections.append(current)
            current.items.extend(normalize_item_line(DISPLAYED_PREFIX_RE.sub("", line)))
            continue

        if _looks_like_priced_item(line):
            if current is None or current.title.lower() in JOINED_SECTION_TITLES:
                current = _create_section("Items")
                sections.append(current)
            current.items.extend(normalize_item_line(line))
            continue

        if current is not None and _starts_new_plated_item_section(current, line):
            current = _create_section("Items")
            sections.append(current)
            current.items.extend(normalize_item_line(line))
            continue

        if _should_break_out_cold_from_greens(current, line):
            current = _create_section("Cold")
            sections.append(current)
            current.items.extend(normalize_item_line(line))
            continue

        if _starts_snack_section(line, current):
            current = _create_section("", preferred_type="snack_items")
            sections.append(current)

        if _looks_like_inline_greens_line(line):
            current = _create_section("Greens")
            current.items.extend(_split_salad_dash_items(line))
            sections.append(current)
            continue

        if _starts_standalone_item_section(current, line):
            current = _create_section("Items")
            current.items.extend(normalize_item_line(line))
            sections.append(current)
            continue

        if current is not None and current.type == "snack_items":
            current.items.extend(normalize_item_line(line))
            continue

        if current is not None and _looks_like_simple_item(line):
            current.items.extend(normalize_item_line(line))
            continue

        if _should_append_to_plated_entree(current, line):
            _append_line_to_joined_section(current, line)
            continue

        colon_match = re.match(r"^([A-Za-z'& ]{2,80})\s*:\s*(.+)$", line, re.IGNORECASE)
        if colon_match:
            section_title = normalize_title(colon_match.group(1))
            current = _create_section(section_title)
            if current.title in {"Greens & Toppings", "Greens", "Condiments"}:
                current.items.extend(_split_greens_and_toppings_items(colon_match.group(2)))
            elif _should_keep_colon_section_whole(current.title):
                current.items.extend(
                    [
                        MenuItem(
                            name=f"{current.title}: {normalize_title(colon_match.group(2))}",
                            quantity=None,
                            unit=None,
                            notes=None,
                            source_text=line,
                        )
                    ]
                )
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

        dash_match = re.match(r"^([A-Za-z' ]{3,60})\s*-\s*(.+)$", line)
        if dash_match and _looks_like_dash_title(dash_match.group(1)):
            current = _create_section(dash_match.group(1))
            current.items.extend(_extract_dash_section_items(current, dash_match.group(2)))
            sections.append(current)
            continue

        if _looks_like_title(line):
            if _is_menu_style_only_title(line) and not line.endswith(":"):
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


def _parse_dietary_restriction_line(line: str) -> dict[str, Any] | None:
    match = re.match(r"^(?P<restrictions>.+?)\s+-\s+(?P<guest>.+)$", line)
    if not match:
        return None
    restriction_text = match.group("restrictions").strip(" ,")
    guest_name = match.group("guest").strip()
    if not restriction_text or not guest_name:
        return None
    items = [part.strip() for part in re.split(r",|/", restriction_text) if part.strip()]
    if not items:
        return None
    return {
        "guest_name": guest_name,
        "restrictions": items,
        "source_text": line,
    }


def _parse_special_dietary_count_line(line: str) -> dict[str, Any] | None:
    match = re.fullmatch(
        r"\(?(?P<count>\d+)\)?\s+(?P<label>vegan/vegeterian|vegan/vegetarian|vegan salads?|vegetarian salads?|vegeterian salads?|dairy free salads?|gluten free salads?|gluten-free salads?|no pecan salads?|vegan|vegetarian|vegeterian|dairy free|gluten free|gluten-free|celiac|peanut allergy|tree nut allergy|nut allergy|shellfish allergy|seafood allergy)\b",
        line.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    raw_label = match.group("label").strip().lower()
    label_map = {
        "vegeterian": "Vegetarian",
        "vegan/vegeterian": "Vegan/Vegetarian",
        "vegan/vegetarian": "Vegan/Vegetarian",
        "vegan salad": "Vegan Salad",
        "vegan salads": "Vegan Salad",
        "vegetarian salad": "Vegetarian Salad",
        "vegetarian salads": "Vegetarian Salad",
        "vegeterian salad": "Vegetarian Salad",
        "vegeterian salads": "Vegetarian Salad",
        "dairy free salad": "Dairy Free Salad",
        "dairy free salads": "Dairy Free Salad",
        "gluten-free": "Gluten Free",
        "gluten free": "Gluten Free",
        "gluten free salad": "Gluten Free Salad",
        "gluten free salads": "Gluten Free Salad",
        "gluten-free salad": "Gluten Free Salad",
        "gluten-free salads": "Gluten Free Salad",
        "no pecan salad": "No Pecan Salad",
        "no pecan salads": "No Pecan Salad",
        "dairy free": "Dairy Free",
        "peanut allergy": "Peanut Allergy",
        "tree nut allergy": "Tree Nut Allergy",
        "nut allergy": "Nut Allergy",
        "shellfish allergy": "Shellfish Allergy",
        "seafood allergy": "Seafood Allergy",
        "vegan": "Vegan",
        "vegetarian": "Vegetarian",
        "celiac": "Celiac",
    }
    return {
        "guest_name": None,
        "restrictions": [label_map[raw_label]],
        "count": int(match.group("count")),
        "kind": "special_count",
        "source_text": line.strip(),
    }


def _is_dietary_note_line(line: str) -> bool:
    lower = line.strip().lower()
    return bool(
        re.fullmatch(r"\d+\s+chef'?s choice .+", lower)
        or re.fullmatch(r"\d+\s+vegetarian options?", lower)
        or re.fullmatch(r"\d+\s*-\s*vegetarian/vegan", lower)
        or re.fullmatch(r"\d+\s*-\s*gluten free", lower)
        or re.fullmatch(r"please have .+", lower)
        or re.fullmatch(r"no nuts!+", lower)
    )


def derive_menu_style(raw_block: str, sections: list[MenuSection]) -> str | None:
    for line in (_clean_line(line) for line in (raw_block or "").splitlines()):
        if line and _is_menu_style_only_title(line):
            return _normalize_menu_style_title(line)
    for section in sections:
        title = section.title.lower()
        if title not in {"items", "beverages", "sides", "dessert", "passed", "displayed"} and title not in INLINE_MENU_SECTION_TITLES and not _is_operational_note_title(
            section.title
        ):
            return section.title
    for line in (_clean_line(line) for line in (raw_block or "").splitlines()):
        if line and not _is_noise(line) and not _looks_like_block_header(line):
            if _looks_like_title(line) and not _is_operational_note_title(line):
                return normalize_title(line)
    return None


def _clean_line(line: str) -> str:
    cleaned = (line or "").replace("\t", " ").replace("**", " ")
    cleaned = re.sub(r"[•]", " ", cleaned)
    cleaned = re.sub(r"\(cid:\d+\)", " ", cleaned)
    return " ".join(cleaned.split()).strip()


def _is_noise(line: str) -> bool:
    lower = line.lower()
    if _is_special_plate_count(line):
        return False
    return any(re.search(pattern, lower) for pattern in NOISE_PATTERNS) or any(
        re.search(pattern, lower) for pattern in CONTRACTUAL_NOISE_PATTERNS
    )


def _looks_like_block_header(line: str) -> bool:
    return bool(re.match(r"^\d{1,2}:\d{2}\s*[AP]M\b", line, re.IGNORECASE))


def _is_dietary_guidance_header(line: str) -> bool:
    lower = line.strip().lower()
    if re.fullmatch(r"\**\s*dietary needs in food header below:?", lower):
        return True
    return bool(re.fullmatch(r"(breakfast|lunch|dinner)\s+options\s+for\s+dr\.?\s+.+:?", lower))


def _ends_dietary_guidance_block(line: str) -> bool:
    lower = line.strip().lower()
    return bool(
        re.fullmatch(r"\$\d[\d.,]*(?:\s*per\s+person)?", lower)
        or lower.startswith("room setup")
        or lower.startswith("arrangements")
        or lower.startswith("dietary restrictions")
        or lower.startswith("food ")
    )


def _looks_like_title(line: str) -> bool:
    lower = line.lower()
    if "@" in line:
        return False
    if lower in TITLE_ALIASES:
        return True
    if _contains_title_hint(lower):
        return True
    if " with " in lower:
        return False
    if len(line.split()) <= 4 and not re.search(r"[@$,]", line):
        return True
    return False


def _looks_like_simple_item(line: str) -> bool:
    lower = line.lower()
    if lower in TITLE_ALIASES:
        return False
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


def _starts_standalone_item_section(current: MenuSection | None, line: str) -> bool:
    if current is None:
        return False
    current_title = current.title.lower().strip()
    if current_title not in INLINE_MENU_SECTION_TITLES:
        return False
    lower = line.lower().strip()
    if ":" in line or "@" in line:
        return False
    if _contains_title_hint(lower):
        return False
    return len(line.split()) <= 4


def _create_section(title: str, preferred_type: str | None = None) -> MenuSection:
    title = normalize_title(title)
    if _is_menu_style_only_title(title):
        title = _normalize_menu_style_title(title)
    lower = title.lower()
    if lower in TITLE_ALIASES:
        title = TITLE_ALIASES[lower]
        lower = title.lower()
    if preferred_type == "snack_items":
        return MenuSection(title=title, type="snack_items", service_role="bar", course_type="break")
    if lower in {"greens", "greens & toppings"}:
        section_type = "cold_items"
        role = "buffet"
    elif "boxed lunch" in lower or "box lunch" in lower:
        section_type = "course"
        role = "other"
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
    elif lower in {
        "passed",
        "displayed",
        "condiments",
        "preset salad",
        "preset salad choice",
        "salad",
        "salad choice",
        "entree",
        "entree choice",
        "dessert",
        "dessert choice",
        "preset alternating dessert",
    }:
        section_type = "course"
        role = "other"
    elif lower in {"assorted bag of", "assorted bags of"}:
        section_type = "snack_items"
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
    section = _collapse_boxed_lunch_items(section)
    section = _collapse_composed_priced_items(section)
    quantity_only_items = []
    for item in section.items:
        name = (item.name or "").strip().lower()
        if re.fullmatch(r"\d+\s+each", name):
            quantity_only_items.append(item)

    if quantity_only_items:
        sandwich_items = [item for item in section.items if _is_breakfast_sandwich_variant(item.name or "")]
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
        aggregate_items = [item for item in section.items if (item.name or "").strip().lower() in {"breakfast sandwiches"}]
        if aggregate_items:
            section.items = [item for item in section.items if item not in aggregate_items]

    section.items = _expand_oatmeal_with_accompaniments(section.items)
    _apply_special_dietary_counts(section)
    section.items = [item for item in section.items if not _is_excluded_non_area_item(item.name or "")]
    section = _combine_joined_section_items(section)
    return section


def _should_keep_colon_section_whole(title: str) -> bool:
    return title.lower().strip() in {"country potato salad"}


def _is_breakfast_sandwich_variant(value: str) -> bool:
    lower = value.lower()
    variant_hints = ("sandwich -", "muffin -", "bagel sandwich", "biscuit sandwich", "croissant sandwich", "english muffin -")
    return any(hint in lower for hint in variant_hints)


def _is_boxed_lunch_section(section: MenuSection) -> bool:
    lower = section.title.lower().strip()
    return lower in {"boxed lunch", "box lunch"}


def _is_excluded_non_area_item(value: str) -> bool:
    lower = value.strip().lower()
    return any(re.fullmatch(pattern, lower) for pattern in EXCLUDED_NON_AREA_ITEM_PATTERNS)


def _contains_title_hint(lower: str) -> bool:
    return any(re.search(rf"\b{re.escape(hint)}\b", lower) for hint in TITLE_HINTS)


def _is_menu_style_only_title(value: str) -> bool:
    return value.strip().rstrip(":").lower() in MENU_STYLE_ONLY_TITLES


def _is_operational_note_title(value: str) -> bool:
    lower = value.strip().rstrip(":").lower()
    return "bar" in lower and any(
        phrase in lower
        for phrase in (
            "to move into ballroom",
            "no tequila",
            "drinks only",
            "must serve mixed",
        )
    )


def _normalize_menu_style_title(value: str) -> str:
    return normalize_title(value).rstrip(":").strip()


def _should_keep_empty_section(section: MenuSection) -> bool:
    return section.type in {"display", "station_items"} and bool(section.title)


def _is_pending_placeholder(value: str) -> bool:
    lower = re.sub(r"^\(\d+\)\s+", "", value.strip().lower())
    return any(re.fullmatch(pattern, lower) for pattern in PENDING_PLACEHOLDER_PATTERNS)


def _merge_broken_menu_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        if index + 1 < len(lines) and lines[index + 1].strip().lower() == "balsamic dressing":
            if current.endswith(", White"):
                merged.append(f"{current} Balsamic Dressing")
                index += 2
                continue
            if current.endswith(" and White"):
                merged.append(f"{current[:-10]}, White Balsamic Dressing")
                index += 2
                continue
        merged.append(current)
        index += 1
    return merged


def _apply_manual_line_rules(lines: list[str]) -> list[str]:
    rewritten: list[str] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        combined = MANUAL_COMBINE_PAIRS.get((current.lower(), (next_line or "").lower()))
        if combined:
            rewritten.append(combined)
            index += 2
            continue
        if current.lower() == "and popcorn":
            rewritten.append("Popcorn")
            index += 1
            continue
        if current.lower().startswith("protein and breakfast bars - "):
            rewritten.append("Protein and Breakfast Bars")
            index += 1
            continue
        if current.lower().startswith("welcome to clt - "):
            rewritten.append("Welcome to CLT")
            index += 1
            continue
        if current.lower().startswith("tsweet rolls with butter"):
            rewritten.append("Sweet Rolls with Butter")
            index += 1
            continue
        if current.lower() == "caluiflower":
            rewritten.append("Cauliflower")
            index += 1
            continue
        if current.lower() == "and accoutrement":
            rewritten.append("Accoutrement")
            index += 1
            continue
        rewritten.append(current)
        index += 1
    return rewritten


def _split_greens_and_toppings_items(value: str) -> list[MenuItem]:
    protected = value.replace(" and ", ", ")
    raw_parts = [part.strip() for part in protected.split(",") if part.strip()]
    expanded_parts: list[str] = []
    for part in raw_parts:
        expanded_parts.extend(_split_contextual_cold_part(part))
    items: list[MenuItem] = []
    for part in expanded_parts:
        normalized = normalize_item_line(part)
        if normalized:
            items.append(normalized[0])
    return items


def _expand_oatmeal_with_accompaniments(items: list[MenuItem]) -> list[MenuItem]:
    expanded: list[MenuItem] = []
    for item in items:
        match = re.match(r"^(steel cut oatmeal)\s+with\s+(.+)$", (item.name or "").strip(), re.IGNORECASE)
        if not match:
            expanded.append(item)
            continue
        expanded.append(MenuItem(name="Steel Cut Oatmeal", quantity=item.quantity, unit=item.unit, notes=item.notes, source_text=item.source_text))
        accompaniments = re.split(r",|&|\band\b", match.group(2))
        for part in accompaniments:
            name = part.strip(" .")
            if not name:
                continue
            expanded.append(MenuItem(name=name, quantity=None, unit=None, notes=item.notes, source_text=item.source_text))
    return expanded


def _starts_new_plated_item_section(current: MenuSection, line: str) -> bool:
    lower = line.lower()
    if current.course_type != "salad":
        return False
    if any(keyword in lower for keyword in ("ranch", "vinaigrette", "dressing")):
        return False
    if lower.startswith(("cucumber", "radish", "tomatoes", "carrots", "mixed greens")):
        return False
    return " with " in lower or any(protein in lower for protein in ("chicken", "salmon", "steak", "pork", "dessert", "rolls"))


def _extract_dash_section_items(section: MenuSection, value: str) -> list[MenuItem]:
    if section.course_type == "salad" or "greens" in section.title.lower():
        return _split_salad_dash_items(value)
    return normalize_item_line(value)


def _split_salad_dash_items(value: str) -> list[MenuItem]:
    cleaned = re.sub(r"(?i)\bon table\b", "", value).strip(" ,")
    cleaned = re.sub(r"(?i)\bon tables\b", "", cleaned).strip(" ,")
    cleaned = re.sub(r"(?i)\b(radish)\s+(ranch)\b", r"\1, \2", cleaned)
    if not cleaned:
        return []
    protected = cleaned.replace(" and ", ", ")
    parts = [part.strip() for part in protected.split(",") if part.strip()]
    items: list[MenuItem] = []
    for part in parts:
        for expanded in _split_contextual_cold_part(part):
            normalized = normalize_item_line(expanded)
            if normalized:
                items.append(normalized[0])
    return items


def _split_contextual_cold_part(value: str) -> list[str]:
    lower = value.strip().lower()
    if not lower:
        return []
    if lower == "spring mix with cherry tomato":
        return ["Spring Mix", "Cherry Tomato"]
    if lower == "baby spinach with cherry tomato":
        return ["Baby Spinach", "Cherry Tomato"]
    if lower == "croutons with buttermilk ranch":
        return ["Croutons", "Buttermilk Ranch Dressing"]
    return [value]


def _should_break_out_cold_from_greens(current: MenuSection | None, line: str) -> bool:
    if current is None or current.title not in {"Greens", "Greens & Toppings"}:
        return False
    lower = line.strip().lower()
    return lower in {"coleslaw"}


def _looks_like_inline_greens_line(line: str) -> bool:
    lower = line.strip().lower()
    return lower.startswith(("spring mix with cherry tomato", "baby spinach with cherry tomato"))


def _apply_special_dietary_counts(section: MenuSection) -> None:
    special_items = [item for item in section.items if _is_special_plate_count(item.source_text or "") or _is_special_plate_label(item)]
    if not special_items:
        return
    target = next((item for item in reversed(section.items) if item not in special_items and not _is_excluded_non_area_item(item.name or "")), None)
    if target is not None:
        notes = [target.notes] if target.notes else []
        notes.extend(item.source_text or item.name for item in special_items)
        target.notes = " | ".join(notes)
    section.items = [item for item in section.items if item not in special_items]


def _collapse_boxed_lunch_items(section: MenuSection) -> MenuSection:
    if not _is_boxed_lunch_section(section):
        return section

    collapsed: list[MenuItem] = []
    current_choice: MenuItem | None = None

    for item in section.items:
        name = (item.name or "").strip()
        lower = name.lower()
        is_priced_choice = item.quantity is not None or bool(re.match(r"^\(\d+\)\s+.+@\s*\$[\d.]+", item.source_text or "", re.IGNORECASE))

        if is_priced_choice:
            current_choice = MenuItem(
                name=name,
                quantity=item.quantity,
                unit=item.unit,
                notes=item.notes,
                source_text=item.source_text,
            )
            collapsed.append(current_choice)
            continue

        if lower in {"dietary", "dietary:"} or lower.startswith("each lunch is packed with "):
            current_choice = None
            continue

        if current_choice is not None:
            note_text = (item.source_text or name).strip()
            note_parts = [part for part in [current_choice.notes, note_text] if part]
            current_choice.notes = " | ".join(note_parts)
            if item.source_text:
                source_parts = [part for part in [current_choice.source_text, item.source_text] if part]
                current_choice.source_text = "\n".join(source_parts)

    section.items = collapsed
    return section


def _collapse_composed_priced_items(section: MenuSection) -> MenuSection:
    collapsed: list[MenuItem] = []
    current_choice: MenuItem | None = None
    continuation_names = {
        "mason jar caesar": {
            "baby gem",
            "parmesan",
            "roasted",
            "tomato",
            "garlic croutons",
            "caesar dressing",
        }
    }

    for item in section.items:
        name = (item.name or "").strip()
        lower = name.lower()
        is_priced_choice = item.quantity is not None or bool(re.match(r"^\(\d+\)\s+.+@\s*\$[\d.]+", item.source_text or "", re.IGNORECASE))

        if is_priced_choice:
            current_choice = item
            collapsed.append(item)
            continue

        if current_choice is not None:
            target_name = (current_choice.name or "").strip().lower()
            allowed_names = continuation_names.get(target_name)
            if allowed_names and lower in allowed_names:
                note_text = (item.source_text or name).strip(" ,")
                note_parts = [part for part in [current_choice.notes, note_text] if part]
                current_choice.notes = " | ".join(note_parts)
                continue

        collapsed.append(item)

    section.items = collapsed
    return section


def _combine_joined_section_items(section: MenuSection) -> MenuSection:
    if section.title.lower() not in JOINED_SECTION_TITLES or len(section.items) <= 1:
        return section
    separator = _joined_section_separator(section.title)
    combined_name = separator.join(item.name for item in section.items if item.name)
    if not combined_name:
        return section
    combined_source = "\n".join(item.source_text or item.name for item in section.items if item.name)
    section.items = [MenuItem(name=combined_name, quantity=None, unit=None, notes=None, source_text=combined_source)]
    return section


def _should_append_to_plated_entree(current: MenuSection | None, line: str) -> bool:
    if current is None or current.title.lower() not in {"entree", "entree choice"}:
        return False
    lower = line.lower()
    return lower.startswith(("starch choice:", "vegetable choice:", "starch:", "vegetable:"))


def _append_line_to_joined_section(section: MenuSection, line: str) -> None:
    normalized_line = normalize_title(line)
    if not normalized_line:
        return
    section.items.append(
        MenuItem(
            name=normalized_line,
            quantity=None,
            unit=None,
            notes=None,
            source_text=line,
        )
    )


def _joined_section_separator(title: str) -> str:
    lower = (title or "").strip().lower()
    if lower in {"entree", "entree choice"}:
        return "\n"
    return ", "


def _is_special_plate_count(value: str) -> bool:
    lower = value.strip().lower()
    if not re.match(r"^\(?\d+\)?\s+", lower):
        return False
    return any(keyword in lower for keyword in ("vegan", "vegetarian", "vegeterian", "gluten free", "gluten-free"))


def _is_special_plate_label(item: MenuItem) -> bool:
    lower = (item.name or "").strip().lower()
    if item.quantity is None:
        return False
    return any(keyword in lower for keyword in ("vegan", "vegetarian", "vegeterian", "gluten free", "gluten-free"))
