#!/usr/bin/env python3
"""Validate a structured solo-business decision brief without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CORE_FIELDS = (
    "decision",
    "stage",
    "life_constraints",
    "target_customer",
    "problem",
    "evidence",
    "resource_limits",
)

STAGES = {
    "idea",
    "validation",
    "first_sales",
    "delivery",
    "systemization",
    "transition",
    "expansion",
}

DECISION_TYPES = {
    "diagnosis",
    "positioning",
    "customer_problem",
    "mvp",
    "pricing",
    "product_ladder",
    "acquisition",
    "ai_workflow",
    "transition",
    "review",
}

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_number": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "credential": re.compile(r"\b(api[_-]?key|access[_-]?token|password|secret)\b", re.IGNORECASE),
}


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            result.append(str(key))
            result.extend(flatten_strings(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(flatten_strings(item))
        return result
    return []


def has_value(data: dict[str, Any], field: str) -> bool:
    value = data.get(field)
    return value not in (None, "", [], {})


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [field for field in CORE_FIELDS if not has_value(data, field)]
    if missing:
        warnings.append("missing core context: " + ", ".join(missing))

    stage = str(data.get("stage", "")).strip().lower()
    if stage and stage not in STAGES:
        warnings.append("unknown stage; use one of: " + ", ".join(sorted(STAGES)))

    decision_type = str(data.get("decision_type", "diagnosis")).strip().lower()
    if decision_type not in DECISION_TYPES:
        warnings.append("unknown decision_type; use one of: " + ", ".join(sorted(DECISION_TYPES)))

    evidence = data.get("evidence", [])
    if evidence and not isinstance(evidence, list):
        errors.append("evidence must be a list")
    elif isinstance(evidence, list):
        allowed_labels = {"fact", "inference", "hypothesis", "unknown", "external_claim"}
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence[{index}] must be an object")
                continue
            label = str(item.get("type", "")).strip()
            if label not in allowed_labels:
                warnings.append(
                    f"evidence[{index}] needs type fact/inference/hypothesis/unknown/external_claim"
                )
            if label in {"fact", "external_claim"} and not item.get("source"):
                warnings.append(f"evidence[{index}] needs a source")
            if label == "external_claim" and not item.get("verification"):
                warnings.append(f"evidence[{index}] external claim needs a verification action")

    if decision_type in {"mvp", "pricing", "product_ladder"}:
        for field in ("offer", "success_signal", "stop_condition"):
            if not has_value(data, field):
                warnings.append(f"{decision_type} decision needs {field}")

    if decision_type == "pricing":
        for field in ("customer_value", "delivery_cost", "capacity"):
            if not has_value(data, field):
                warnings.append(f"pricing decision needs {field}")

    if decision_type == "transition":
        for field in ("cash_buffer", "income_quality", "concentration_risk", "fallback_plan"):
            if not has_value(data, field):
                warnings.append(f"transition decision needs {field}")

    if data.get("contains_current_market_or_legal_claims") is True and not has_value(
        data, "verification_plan"
    ):
        warnings.append("current market/legal claims require a verification_plan")

    if data.get("contains_real_personal_data") is True:
        errors.append("brief declares real personal data; anonymize and minimize before use")

    privacy_hits: list[str] = []
    joined = "\n".join(flatten_strings(data))
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(joined):
            privacy_hits.append(label)
    if privacy_hits:
        errors.append(
            "sensitive identifiers or credentials detected: "
            + ", ".join(privacy_hits)
            + "; redact them before analysis"
        )

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "decision_type": decision_type,
        "stage": stage or None,
        "errors": errors,
        "warnings": warnings,
        "can_proceed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="UTF-8 JSON brief")
    parser.add_argument("--strict", action="store_true", help="return non-zero when warnings exist")
    args = parser.parse_args()

    try:
        data = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(data, dict):
        print(json.dumps({"status": "error", "errors": ["brief root must be an object"]}, indent=2))
        return 2

    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]:
        return 2
    if args.strict and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
