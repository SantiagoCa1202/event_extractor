from __future__ import annotations

from dataclasses import dataclass

from .schemas import RuleDecision, ServiceEquipment


EQUIPMENT_TARGETS = (
    "glasses",
    "covers",
    "salad_trees",
    "speed_racks",
    "plates_in_cold_area",
    "plates_in_hot_box",
    "hot_boxes",
)


@dataclass(slots=True)
class EquipmentRule:
    name: str
    categories: set[str]
    target: str
    requires_formula: bool
    justification: str


DEFAULT_EQUIPMENT_RULES = [
    EquipmentRule(
        name="plated_hot_holding",
        categories={"plated"},
        target="hot_boxes",
        requires_formula=True,
        justification="Plated service often requires hot holding, but the exact formula must be supplied by operations.",
    ),
    EquipmentRule(
        name="buffet_covers",
        categories={"buffet"},
        target="covers",
        requires_formula=True,
        justification="Buffet cover counts vary by station count and menu configuration.",
    ),
    EquipmentRule(
        name="reception_glassware",
        categories={"reception", "beverage"},
        target="glasses",
        requires_formula=True,
        justification="Glassware depends on bar package, duration and guest profile.",
    ),
]


def evaluate_equipment_rules(category: str) -> tuple[list[ServiceEquipment], list[RuleDecision]]:
    applied: list[ServiceEquipment] = []
    decisions: list[RuleDecision] = []
    for rule in DEFAULT_EQUIPMENT_RULES:
        if category not in rule.categories:
            decisions.append(
                RuleDecision(
                    rule_name=rule.name,
                    status="excluded",
                    target=rule.target,
                    reason=f"Category '{category}' does not match rule categories.",
                )
            )
            continue
        decisions.append(
            RuleDecision(
                rule_name=rule.name,
                status="pending",
                target=rule.target,
                reason=rule.justification,
            )
        )
    for target in EQUIPMENT_TARGETS:
        if not any(decision.target == target for decision in decisions):
            decisions.append(
                RuleDecision(
                    rule_name=f"default_exclusion_{target}",
                    status="excluded",
                    target=target,
                    reason="No configured rule applies to this service category.",
                )
            )
    return applied, decisions
