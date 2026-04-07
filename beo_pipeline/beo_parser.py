from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from text_extraction import safe_extract_text

from .schemas import BeoDocument, ParsedPage


EVENT_ORDER_RE = re.compile(r"Event Order\s*#\s*:?\s*(\d+)", re.IGNORECASE)
DATE_RE = re.compile(
    r"FUNCTION DAY/DATE:\s*([A-Za-z]+),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
    re.IGNORECASE,
)
ORG_RE = re.compile(r"ORGANIZATION:\s*(.+)", re.IGNORECASE)


def infer_beo_type(source_path: str) -> tuple[str, int]:
    name = Path(source_path).name.lower()
    if "popup" in name or "pop-up" in name:
        revision = _extract_revision_number(name)
        return "popup", revision
    if "revision" in name or "revisions" in name:
        revision = _extract_revision_number(name)
        return "revision", revision
    return "original", 0


def _extract_revision_number(value: str) -> int:
    match = re.search(r"(?:rev(?:ision)?\D*)(\d+)", value, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def extract_pdf_pages(pdf_path: str) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    with pdfplumber.open(pdf_path) as pdf:
        for index in range(len(pdf.pages)):
            text = safe_extract_text(pdf_path, index)
            pages.append(ParsedPage(page_number=index + 1, text=text or ""))
    return pages


def group_pages_into_documents(pages: list[ParsedPage], source_path: str) -> list[BeoDocument]:
    beo_type, revision_number = infer_beo_type(source_path)
    documents: list[BeoDocument] = []
    current_pages: list[ParsedPage] = []
    current_order: str | None = None

    for page in pages:
        event_match = EVENT_ORDER_RE.search(page.text)
        page_order = event_match.group(1) if event_match else None
        if page_order and current_pages and page_order != current_order:
            documents.append(_build_document(source_path, current_order, current_pages, beo_type, revision_number))
            current_pages = []
        if page_order:
            current_order = page_order
            current_pages.append(page)
        elif current_pages:
            current_pages.append(page)

    if current_pages and current_order:
        documents.append(_build_document(source_path, current_order, current_pages, beo_type, revision_number))

    return documents


def _build_document(
    source_path: str,
    event_order: str | None,
    pages: list[ParsedPage],
    beo_type: str,
    revision_number: int,
) -> BeoDocument:
    full_text = "\n".join(page.text for page in pages if page.text)
    date_match = DATE_RE.search(full_text)
    org_match = ORG_RE.search(full_text)
    return BeoDocument(
        source_path=source_path,
        event_order=event_order or "",
        day=date_match.group(1) if date_match else None,
        date=date_match.group(2) if date_match else None,
        organization=org_match.group(1).strip() if org_match else None,
        beo_type=beo_type,
        revision_number=revision_number,
        pages=pages,
    )


def parse_pdf_to_documents(pdf_path: str) -> list[BeoDocument]:
    return group_pages_into_documents(extract_pdf_pages(pdf_path), pdf_path)


def parse_text_pages_to_documents(page_texts: list[str], source_path: str = "<memory>") -> list[BeoDocument]:
    pages = [ParsedPage(page_number=index + 1, text=text) for index, text in enumerate(page_texts)]
    return group_pages_into_documents(pages, source_path)
