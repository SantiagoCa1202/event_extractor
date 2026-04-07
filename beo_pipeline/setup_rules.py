from __future__ import annotations

from .breakdown_rules import evaluate_breakdown_station
from .equipment_rules import evaluate_equipment_rules


def evaluate_setup(category: str) -> dict:
    breakdown_station, breakdown_trace = evaluate_breakdown_station(category)
    equipment, equipment_trace = evaluate_equipment_rules(category)
    return {
        "breakdown_station": breakdown_station,
        "service_equipment": equipment,
        "rule_trace": {
            "applied": [],
            "pending": [decision for decision in breakdown_trace + equipment_trace if decision.status == "pending"],
            "excluded": [decision for decision in breakdown_trace + equipment_trace if decision.status == "excluded"],
        },
    }
