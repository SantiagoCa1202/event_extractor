from __future__ import annotations

import re

from .menu_normalizer import normalize_item_line, normalize_title
from .schemas import MenuSection


NOISE_PATTERNS = (
    r"^marriott proprietary",
    r"^charged on consumption",
    r"^based on ",
    r"^\$\d",
    r"^post as:",
    r"^special$",
    r"^arrangements$",
    r"^room setup",
)

TITLE_HINTS = ("display", "station", "bar", "buffet", "continental", "break", "table")
BEVERAGE_HINTS = ("coffee", "tea", "juice", "water", "pepsi", "soda", "iced tea", "wine", "beer", "bourbon", "scotch")
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
    if not lines:
        return []

    sections: list[MenuSection] = []
    current: MenuSection | None = None

    for line in lines:
        if _looks_like_block_header(line):
            continue

        if current is not None and _looks_like_simple_item(line):
            current.items.extend(normalize_item_line(line))
            continue

        colon_match = re.match(r"^(Sides|Dessert|Beverages?|Choice of Two Proteins)\s*:\s*(.+)$", line, re.IGNORECASE)
        if colon_match:
            current = _create_section(colon_match.group(1))
            current.items.extend(normalize_item_line(colon_match.group(2)))
            sections.append(current)
            continue

        dash_match = re.match(r"^([A-Za-z' ]{3,40})\s*-\s*(.+)$", line)
        if dash_match and _looks_like_title(dash_match.group(1)):
            current = _create_section(dash_match.group(1))
            current.items.extend(normalize_item_line(dash_match.group(2)))
            sections.append(current)
            continue

        if _looks_like_title(line):
            current = _create_section(line)
            sections.append(current)
            continue

        if current is None:
            current = _create_section("Items")
            sections.append(current)

        current.items.extend(normalize_item_line(line))

    return [section for section in sections if section.items]


def derive_menu_style(raw_block: str, sections: list[MenuSection]) -> str | None:
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
    return any(re.search(pattern, lower) for pattern in NOISE_PATTERNS)


def _looks_like_block_header(line: str) -> bool:
    return bool(re.match(r"^\d{1,2}:\d{2}\s*[AP]M\b", line, re.IGNORECASE))


def _looks_like_title(line: str) -> bool:
    lower = line.lower()
    if any(hint in lower for hint in TITLE_HINTS):
        return True
    if len(line.split()) <= 4 and not re.search(r"[@$,]", line):
        return True
    return False


def _looks_like_simple_item(line: str) -> bool:
    lower = line.lower()
    if any(hint in lower for hint in TITLE_HINTS):
        return False
    if re.search(r"[@$:]", line):
        return False
    return len(line.split()) <= 4


def _create_section(title: str) -> MenuSection:
    title = normalize_title(title)
    lower = title.lower()
    if "display" in lower:
        section_type = "display"
        role = "display"
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
    if section_type == "beverage":
        course_type = "beverage"

    return MenuSection(title=title, type=section_type, service_role=role, course_type=course_type)
