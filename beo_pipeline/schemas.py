from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str


@dataclass(slots=True)
class BeoDocument:
    source_path: str
    event_order: str
    quote: str | None
    day: str | None
    date: str | None
    organization: str | None
    beo_type: str
    revision_number: int
    pages: list[ParsedPage] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(page.text for page in self.pages if page.text)


@dataclass(slots=True)
class AttendanceEntry:
    start: str
    end: str | None
    function_name: str
    room: str | None
    gtd: int | None
    raw: str


@dataclass(slots=True)
class EventCandidate:
    start: str
    end: str | None
    function_name: str
    room: str | None
    gtd: int | None
    raw: str
    page_numbers: list[int]
    attendance_match: AttendanceEntry | None = None


@dataclass(slots=True)
class MenuItem:
    name: str
    quantity: int | None = None
    unit: str | None = None
    notes: str | None = None
    source_text: str | None = None


@dataclass(slots=True)
class MenuSection:
    title: str
    type: str
    service_role: str
    course_type: str
    items: list[MenuItem] = field(default_factory=list)


@dataclass(slots=True)
class RuleDecision:
    rule_name: str
    status: str
    target: str
    reason: str


@dataclass(slots=True)
class BreakdownStation:
    required: bool | None
    quantity: int | None
    size: str | None
    notes: str | None = None


@dataclass(slots=True)
class ServiceEquipment:
    name: str
    quantity: int | None
    unit: str | None
    applies_to: str


@dataclass(slots=True)
class Staffing:
    servers: int = 0
    bartenders: int = 0
    chefs: int = 0
    attendants: int = 0


@dataclass(slots=True)
class SourceTrace:
    page_ranges: list[str]
    text_snippets: list[str]
    confidence: str


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value
