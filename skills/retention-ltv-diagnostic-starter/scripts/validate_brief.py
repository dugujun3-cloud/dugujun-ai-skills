#!/usr/bin/env python3
"""Validate an aggregated retention/LTV diagnostic brief with no dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALLOWED_MODES = {"combined", "retention_ltv", "repurchase_ltv", "renewal_ltv"}
ALLOWED_LTV_BASES = {"revenue", "gross_margin", "contribution"}
DIRECT_IDENTIFIER_KEYS = {
    "full_name",
    "phone",
    "mobile",
    "email",
    "openid",
    "open_id",
    "id_card",
    "identity_number",
    "address",
    "order_id",
    "order_number",
    "cookie",
    "token",
    "api_key",
}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def walk(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    items: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            items.append((child_path, str(key), child))
            items.extend(walk(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(walk(child, f"{path}[{index}]"))
    return items


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_brief(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ["root must be a JSON object"], warnings

    required = {
        "schema_version",
        "mode",
        "decision_question",
        "business",
        "observation",
        "cohorts",
        "constraints",
    }
    missing = sorted(required - data.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    if data.get("mode") not in ALLOWED_MODES:
        errors.append(f"mode must be one of: {', '.join(sorted(ALLOWED_MODES))}")

    decision = data.get("decision_question")
    if not isinstance(decision, str) or not decision.strip():
        errors.append("decision_question must be a non-empty string")

    business = data.get("business")
    if not isinstance(business, dict):
        errors.append("business must be an object")
    else:
        for field in ("model", "product_or_service", "cohort_entry_event", "value_event", "ltv_basis"):
            if not isinstance(business.get(field), str) or not business[field].strip():
                errors.append(f"business.{field} must be a non-empty string")
        if business.get("ltv_basis") not in ALLOWED_LTV_BASES:
            errors.append(
                "business.ltv_basis must be one of: "
                + ", ".join(sorted(ALLOWED_LTV_BASES))
            )

    observation = data.get("observation")
    if not isinstance(observation, dict):
        errors.append("observation must be an object")
    else:
        for field in ("window", "as_of", "maturity_rule"):
            if not isinstance(observation.get(field), str) or not observation[field].strip():
                errors.append(f"observation.{field} must be a non-empty string")
        if not isinstance(observation.get("all_cohorts_mature"), bool):
            errors.append("observation.all_cohorts_mature must be boolean")

    cohorts = data.get("cohorts")
    if not isinstance(cohorts, list) or not cohorts:
        errors.append("cohorts must be a non-empty array")
    else:
        cohort_names: set[str] = set()
        numeric_fields = (
            "eligible_users",
            "retained_users",
            "repeat_buyers",
            "revenue",
            "refunds",
            "variable_costs",
            "acquisition_cost",
        )
        for index, cohort in enumerate(cohorts):
            prefix = f"cohorts[{index}]"
            if not isinstance(cohort, dict):
                errors.append(f"{prefix} must be an object")
                continue
            name = cohort.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{prefix}.name must be a non-empty string")
            elif name in cohort_names:
                errors.append(f"{prefix}.name duplicates another cohort")
            else:
                cohort_names.add(name)
            for field in numeric_fields:
                value = cohort.get(field)
                if not is_number(value):
                    errors.append(f"{prefix}.{field} must be numeric")
                elif value < 0:
                    errors.append(f"{prefix}.{field} must be >= 0")
            eligible = cohort.get("eligible_users")
            if is_number(eligible) and eligible <= 0:
                errors.append(f"{prefix}.eligible_users must be > 0")
            for field in ("retained_users", "repeat_buyers"):
                value = cohort.get(field)
                if is_number(eligible) and is_number(value) and value > eligible:
                    errors.append(f"{prefix}.{field} cannot exceed eligible_users")
            if not isinstance(cohort.get("mature"), bool):
                errors.append(f"{prefix}.mature must be boolean")
            if cohort.get("refunds", 0) > cohort.get("revenue", 0):
                warnings.append(f"{prefix}: refunds exceed revenue; confirm the window and currency")

    constraints = data.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("constraints must be an object")
    elif not isinstance(constraints.get("contact_permission"), bool):
        errors.append("constraints.contact_permission must be boolean")

    for item_path, key, value in walk(data):
        normalized = key.lower()
        if normalized in DIRECT_IDENTIFIER_KEYS:
            errors.append(f"{item_path} is a prohibited direct-identifier field")
        if isinstance(value, str):
            if EMAIL_RE.search(value):
                errors.append(f"{item_path} contains an email address")
            if PHONE_RE.search(value):
                errors.append(f"{item_path} contains a phone number")

    if isinstance(observation, dict) and observation.get("all_cohorts_mature") is False:
        warnings.append("not all cohorts are mature; avoid cross-cohort release decisions")

    return sorted(set(errors)), sorted(set(warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        data = load_json(args.brief)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_brief(data)
    payload = {"valid": not errors, "errors": errors, "warnings": warnings}
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"WARN: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print("VALID" if not errors else "INVALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
