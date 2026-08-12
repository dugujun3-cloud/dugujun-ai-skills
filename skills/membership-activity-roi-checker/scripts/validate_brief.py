#!/usr/bin/env python3
"""Validate an anonymous aggregate membership-campaign ROI brief."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


OBJECTIVES = {"reactivation_value", "member_acquisition", "qualified_traffic"}
COUNTERFACTUAL_TYPES = {"randomized_control", "matched_control", "historical_baseline", "none"}
FORBIDDEN_KEYS = {
    "name", "full_name", "phone", "mobile", "email", "address",
    "openid", "open_id", "unionid", "union_id", "id_card", "user_id",
}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("brief root must be an object")
    return data


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def scan_privacy(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"direct identifier field is not allowed: {path}.{key}")
            scan_privacy(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_privacy(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if EMAIL_RE.search(value) or PHONE_RE.search(value):
            errors.append(f"possible direct identifier in {path}")


def require_number(container: dict[str, Any], key: str, path: str, errors: list[str], *, positive: bool = False) -> None:
    value = container.get(key)
    if not is_number(value):
        errors.append(f"{path}.{key} must be a number")
    elif positive and value <= 0:
        errors.append(f"{path}.{key} must be > 0")
    elif value < 0:
        errors.append(f"{path}.{key} must be >= 0")


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scan_privacy(data, "$", errors)

    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not isinstance(data.get("decision_question"), str) or not data["decision_question"].strip():
        errors.append("decision_question is required")
    if data.get("objective") not in OBJECTIVES:
        errors.append(f"objective must be one of {sorted(OBJECTIVES)}")
    if not isinstance(data.get("result_name"), str) or not data["result_name"].strip():
        errors.append("result_name is required")
    if not isinstance(data.get("observation_window"), str) or not data["observation_window"].strip():
        errors.append("observation_window is required")
    if not isinstance(data.get("maturity_rule"), str) or not data["maturity_rule"].strip():
        errors.append("maturity_rule is required")

    population = data.get("population")
    if not isinstance(population, dict):
        errors.append("population must be an object")
        population = {}
    require_number(population, "treatment_eligible", "population", errors, positive=True)
    require_number(population, "treatment_results", "population", errors)
    eligible = population.get("treatment_eligible")
    results = population.get("treatment_results")
    if is_number(eligible) and is_number(results) and results > eligible:
        errors.append("population.treatment_results cannot exceed treatment_eligible")

    counterfactual = population.get("counterfactual")
    if not isinstance(counterfactual, dict):
        errors.append("population.counterfactual must be an object")
        counterfactual = {}
    counterfactual_type = counterfactual.get("type")
    if counterfactual_type not in COUNTERFACTUAL_TYPES:
        errors.append(f"population.counterfactual.type must be one of {sorted(COUNTERFACTUAL_TYPES)}")
    if counterfactual_type in {"randomized_control", "matched_control"}:
        require_number(counterfactual, "control_eligible", "population.counterfactual", errors, positive=True)
        require_number(counterfactual, "control_results", "population.counterfactual", errors)
        control_eligible = counterfactual.get("control_eligible")
        control_results = counterfactual.get("control_results")
        if is_number(control_eligible) and is_number(control_results) and control_results > control_eligible:
            errors.append("control_results cannot exceed control_eligible")
    if counterfactual_type == "historical_baseline":
        baseline_rate = counterfactual.get("baseline_result_rate")
        if not is_number(baseline_rate) or not 0 <= baseline_rate <= 1:
            errors.append("baseline_result_rate must be a decimal between 0 and 1")

    economics = data.get("economics")
    if not isinstance(economics, dict):
        errors.append("economics must be an object")
        economics = {}
    economic_values = (
        "treatment_net_revenue", "treatment_variable_costs",
        "comparison_net_revenue", "comparison_variable_costs",
        "baseline_contribution_per_eligible", "contribution_value_per_result",
    )
    for key in economic_values:
        value = economics.get(key)
        if value is not None and (not is_number(value) or value < 0):
            errors.append(f"economics.{key} must be null or >= 0")
    if economics.get("double_count_checked") is not True:
        errors.append("economics.double_count_checked must be true")

    has_treatment_economics = all(
        economics.get(key) is not None
        for key in ("treatment_net_revenue", "treatment_variable_costs")
    )
    has_value_fallback = economics.get("contribution_value_per_result") is not None
    if data.get("objective") == "reactivation_value" and not (has_treatment_economics or has_value_fallback):
        errors.append("reactivation_value requires treatment economics or contribution_value_per_result")
    if has_treatment_economics and counterfactual_type in {"randomized_control", "matched_control"}:
        if economics.get("comparison_net_revenue") is None or economics.get("comparison_variable_costs") is None:
            errors.append("control comparison economics are required when treatment economics are used")
    if has_treatment_economics and counterfactual_type == "historical_baseline":
        if economics.get("baseline_contribution_per_eligible") is None:
            errors.append("baseline_contribution_per_eligible is required for historical contribution comparison")

    costs = data.get("costs")
    if not isinstance(costs, dict):
        errors.append("costs must be an object")
        costs = {}
    for key in (
        "incentives", "media", "technology", "incremental_labor",
        "fulfillment", "fraud_and_abnormal_loss", "other",
    ):
        require_number(costs, key, "costs", errors)

    thresholds = data.get("business_thresholds", {})
    if not isinstance(thresholds, dict):
        errors.append("business_thresholds must be an object")
    else:
        for key, value in thresholds.items():
            if value is not None and not is_number(value):
                errors.append(f"business_thresholds.{key} must be null or a number")

    guardrails = data.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("guardrails must be an object")
        guardrails = {}
    for key in ("refund_rate", "complaint_rate", "cancellation_rate"):
        value = guardrails.get(key)
        if value is not None and (not is_number(value) or not 0 <= value <= 1):
            errors.append(f"guardrails.{key} must be null or a decimal between 0 and 1")
    for key in ("capacity_breached", "privacy_or_compliance_issue"):
        if not isinstance(guardrails.get(key), bool):
            errors.append(f"guardrails.{key} must be true or false")

    privacy = data.get("privacy")
    if not isinstance(privacy, dict):
        errors.append("privacy must be an object")
    else:
        if privacy.get("aggregate_only") is not True:
            errors.append("privacy.aggregate_only must be true")
        if privacy.get("contains_direct_identifiers") is not False:
            errors.append("privacy.contains_direct_identifiers must be false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    args = parser.parse_args()
    try:
        data = load_json(args.brief)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    errors = validate(data)
    print(json.dumps({"status": "passed" if not errors else "failed", "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
