from __future__ import annotations

from .beo_parser import parse_pdf_to_documents, parse_text_pages_to_documents
from .event_detector import detect_event_candidates
from .event_object_builder import build_event_object


def extract_events_from_pdf(pdf_path: str) -> list[dict]:
    events: list[dict] = []
    for document in parse_pdf_to_documents(pdf_path):
        for candidate in detect_event_candidates(document):
            event = build_event_object(document, candidate)
            if event:
                events.append(event)
    return events


def extract_events_from_text_pages(page_texts: list[str], source_path: str = "<memory>") -> list[dict]:
    events: list[dict] = []
    for document in parse_text_pages_to_documents(page_texts, source_path):
        for candidate in detect_event_candidates(document):
            event = build_event_object(document, candidate)
            if event:
                events.append(event)
    return events
