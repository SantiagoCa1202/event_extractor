from __future__ import annotations

import hashlib
import re

from .schemas import MenuItem


PRICE_SUFFIX_RE = re.compile(r"\s*@\s*\$[\d.,]+(?:\s+per\s+\w+|\s+each)?", re.IGNORECASE)
LEADING_QTY_RE = re.compile(r"^\((\d+)\)\s+(.+)$")


def normalize_item_line(line: str) -> list[MenuItem]:
    cleaned = " ".join((line or "").replace("•", " ").split()).strip(" -")
    if not cleaned:
        return []

    quantity = None
    unit = None
    notes = None

    qty_match = LEADING_QTY_RE.match(cleaned)
    if qty_match:
        quantity = int(qty_match.group(1))
        cleaned = qty_match.group(2).strip()

    if "per dozen" in cleaned.lower():
        unit = "dozen"
    elif "per gallon" in cleaned.lower():
        unit = "gallon"
    elif re.search(r"\beach\b", cleaned, re.IGNORECASE):
        unit = "each"

    no_price = PRICE_SUFFIX_RE.sub("", cleaned).strip()
    if "charged on consumption" in no_price.lower():
        notes = "Charged on consumption"
        no_price = re.sub(r"(?i)charged on consumption", "", no_price).strip(", ")

    if _should_keep_whole(no_price):
        return [MenuItem(name=no_price, quantity=quantity, unit=unit, notes=notes, source_text=line)]

    parts = [part.strip(" .") for part in re.split(r",|(?<!\w)&(?!\w)|\+", no_price) if part.strip()]
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
    guarded_tokens = (" with ", " on table", " offered ", " preset ", " choice of ", "types at")
    return any(token in lower for token in guarded_tokens)
