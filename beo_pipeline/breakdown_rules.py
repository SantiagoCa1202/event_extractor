from __future__ import annotations

from dataclasses import dataclass

from .schemas import BreakdownStation, RuleDecision


@dataclass(slots=True)
class BreakdownRule:
    name: str
    categories: set[str]
    justification: str


DEFAULT_BREAKDOWN_RULES = [
    BreakdownRule(
        name="breakdown_station_size",
        categories={"buffet", "plated", "reception", "station", "display", "break"},
        justification="Breakdown quantity and size depend on GTD, menu volume and local operating standards.",
    )
]


def evaluate_breakdown_station(category: str) -> tuple[BreakdownStation, list[RuleDecision]]:
    for rule in DEFAULT_BREAKDOWN_RULES:
        if category in rule.categories:
            return (
                BreakdownStation(
                    required=None,
                    quantity=None,
                    size="unknown",
                    notes="Pending exact business rule configuration for breakdown station sizing.",
                ),
                [
                    RuleDecision(
                        rule_name=rule.name,
                        status="pending",
                        target="breakdown_station",
                        reason=rule.justification,
                    )
                ],
            )

    return (
        BreakdownStation(required=None, quantity=None, size="unknown", notes="No breakdown rule applies."),
        [
            RuleDecision(
                rule_name="breakdown_station_excluded",
                status="excluded",
                target="breakdown_station",
                reason=f"Service category '{category}' has no configured breakdown rule.",
            )
        ],
    )
