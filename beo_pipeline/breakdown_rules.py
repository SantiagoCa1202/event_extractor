from __future__ import annotations

from dataclasses import dataclass

from .schemas import BreakdownStation, RuleDecision


PLATED_CATEGORIES = {"plated"}
NON_PLATED_CATEGORIES = {"buffet", "reception", "break", "other_food_service", "station", "display"}


@dataclass(slots=True)
class BreakdownOutcome:
    quantity: int
    size: str
    rule_name: str
    reason: str


def evaluate_breakdown_station(category: str, room: str | None, gtd: int | None) -> tuple[BreakdownStation, list[RuleDecision]]:
    normalized_room = (room or "").lower()
    if gtd is None:
        return _pending("missing_gtd", "Breakdown station requires GTD to select quantity and size.")

    if gtd < 25:
        return (
            BreakdownStation(
                required=False,
                quantity=0,
                size="unknown",
                notes="Events under 25 guests do not require a breakdown station.",
            ),
            [
                RuleDecision(
                    rule_name="global_lt_25_no_breakdown",
                    status="applied",
                    target="breakdown_station",
                    reason="Events under 25 guests do not require a breakdown station.",
                )
            ],
        )

    outcome = _match_room_rule(category, normalized_room, gtd)
    if outcome is None:
        return _pending(
            "breakdown_station_unmapped_room",
            f"No configured breakdown station rule for room '{room or 'unknown'}' and category '{category}'.",
        )

    return (
        BreakdownStation(
            required=True,
            quantity=outcome.quantity,
            size=outcome.size,
            notes=outcome.reason,
        ),
        [
            RuleDecision(
                rule_name=outcome.rule_name,
                status="applied",
                target="breakdown_station",
                reason=outcome.reason,
            )
        ],
    )


def _match_room_rule(category: str, room: str, gtd: int) -> BreakdownOutcome | None:
    if "symphony" in room:
        return _symphony_rule(category, gtd)
    if "mecklenburg" in room or "governors" in room:
        return _mecklenburg_governors_rule(category, gtd)
    if "executive boardroom" in room or "cardinal" in room:
        return _executive_cardinal_rule(category, gtd)
    if "carolina" in room:
        return _carolina_rule(category, gtd)
    if "cjs" in room:
        return _simple_small_large_rule(category, gtd, room_key="cjs", small_size="s", large_size="l")
    if "lm pdr" in room:
        return _simple_small_large_rule(category, gtd, room_key="lm_pdr", small_size="s", large_size="m")
    if "rooftop" in room:
        return _single_station_rule(category, "rooftop", "s")
    return None


def _symphony_rule(category: str, gtd: int) -> BreakdownOutcome:
    if category in PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "plated", "symphony_plated_lt_150", "Symphony plated under 150 guests uses 1 plated station.")
        if gtd <= 500:
            return BreakdownOutcome(2, "plated", "symphony_plated_150_500", "Symphony plated from 150 to 500 guests uses 2 plated stations.")
        if gtd <= 700:
            return BreakdownOutcome(2, "plated", "symphony_plated_500_700", "Symphony plated from 500 to 700 guests uses 2 plated stations.")
        return BreakdownOutcome(2, "xl", "symphony_plated_gt_700", "Symphony plated above 700 guests uses 2 XL plated stations.")
    if category in NON_PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "m", "symphony_non_plated_lt_150", "Symphony buffet/reception/break under 150 guests uses 1 medium station.")
        if gtd <= 500:
            return BreakdownOutcome(2, "l", "symphony_non_plated_150_500", "Symphony buffet/reception/break from 150 to 500 guests uses 2 large stations.")
        return BreakdownOutcome(2, "xl", "symphony_non_plated_gt_500", "Symphony buffet/reception/break above 500 guests uses 2 XL stations.")
    return BreakdownOutcome(1, "unknown", "symphony_unsupported_category", f"Symphony rule not explicitly configured for category '{category}'.")


def _mecklenburg_governors_rule(category: str, gtd: int) -> BreakdownOutcome:
    if category in PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "s", "meck_gov_plated_lt_150", "Mecklenburg/Governors plated under 150 guests uses 1 small plated station.")
        return BreakdownOutcome(1, "l", "meck_gov_plated_gt_150", "Mecklenburg/Governors plated at or above 150 guests uses 1 large plated station.")
    if category in NON_PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "m", "meck_gov_non_plated_lt_150", "Mecklenburg/Governors buffet/reception/break under 150 guests uses 1 medium station.")
        return BreakdownOutcome(1, "l", "meck_gov_non_plated_gt_150", "Mecklenburg/Governors buffet/reception/break at or above 150 guests uses 1 large station.")
    return BreakdownOutcome(1, "unknown", "meck_gov_unsupported_category", f"Mecklenburg/Governors rule not explicitly configured for category '{category}'.")


def _executive_cardinal_rule(category: str, gtd: int) -> BreakdownOutcome:
    if category in NON_PLATED_CATEGORIES:
        return BreakdownOutcome(1, "s", "executive_cardinal_non_plated", "Executive Boardroom/Cardinal buffet/reception/break uses 1 small station.")
    return BreakdownOutcome(1, "unknown", "executive_cardinal_unsupported_category", f"Executive Boardroom/Cardinal rule not explicitly configured for category '{category}'.")


def _carolina_rule(category: str, gtd: int) -> BreakdownOutcome:
    if category in PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "plated", "carolina_plated_lt_150", "Carolina plated under 150 guests uses 1 plated station.")
        if gtd <= 500:
            return BreakdownOutcome(2, "l", "carolina_plated_150_500", "Carolina plated from 150 to 500 guests uses 2 large plated stations.")
        return BreakdownOutcome(2, "plated", "carolina_plated_gt_500", "Carolina plated above 500 guests uses 2 plated stations.")
    if category in NON_PLATED_CATEGORIES:
        if gtd < 150:
            return BreakdownOutcome(1, "m", "carolina_non_plated_lt_150", "Carolina buffet/reception/break under 150 guests uses 1 medium station.")
        if gtd <= 500:
            return BreakdownOutcome(2, "l", "carolina_non_plated_150_500", "Carolina buffet/reception/break from 150 to 500 guests uses 2 large stations.")
        return BreakdownOutcome(2, "xl", "carolina_non_plated_gt_500", "Carolina buffet/reception/break above 500 guests uses 2 XL stations.")
    return BreakdownOutcome(1, "unknown", "carolina_unsupported_category", f"Carolina rule not explicitly configured for category '{category}'.")


def _simple_small_large_rule(category: str, gtd: int, room_key: str, small_size: str, large_size: str) -> BreakdownOutcome:
    size = small_size if gtd < 75 else large_size
    return BreakdownOutcome(
        1,
        size,
        f"{room_key}_{'lt_75' if gtd < 75 else 'gte_75'}",
        f"{room_key.upper()} uses 1 {size.upper()} station based on the 75-guest threshold.",
    )


def _single_station_rule(category: str, room_key: str, size: str) -> BreakdownOutcome:
    return BreakdownOutcome(1, size, f"{room_key}_single_station", f"{room_key.title()} always uses 1 {size.upper()} station.")


def _pending(rule_name: str, reason: str) -> tuple[BreakdownStation, list[RuleDecision]]:
    return (
        BreakdownStation(required=None, quantity=None, size="unknown", notes=reason),
        [
            RuleDecision(
                rule_name=rule_name,
                status="pending",
                target="breakdown_station",
                reason=reason,
            )
        ],
    )
