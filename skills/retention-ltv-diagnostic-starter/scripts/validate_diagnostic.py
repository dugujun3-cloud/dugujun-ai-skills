#!/usr/bin/env python3
"""Validate the structured retention/LTV diagnostic output contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from validate_brief import DIRECT_IDENTIFIER_KEYS, EMAIL_RE, PHONE_RE, load_json, walk

REQUIRED_FIELDS = {
    "schema_version",
    "decision",
    "scope",
    "confidence",
    "data_quality",
    "metric_dictionary",
    "findings",
    "value_bridge",
    "cause_tree",
    "experiment",
    "economics",
    "guardrails",
    "stop_conditions",
    "unknowns",
    "routing",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_EVIDENCE = {
    "fact",
    "descriptive",
    "supported_inference",
    "causal",
    "prediction",
    "unknown",
}
UNSUPPORTED_PROMISE_RE = re.compile(
    r"(保证|必然|一定).{0,8}(提升|增长|翻倍|改善)|自动找到.{0,4}(唯一|真实)根因"
)


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    missing = sorted(REQUIRED_FIELDS - data.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    if data.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("confidence must be low, medium or high")

    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array")
    else:
        required_finding = {
            "statement",
            "evidence_level",
            "evidence",
            "limitations",
            "next_validation",
        }
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"findings[{index}] must be an object")
                continue
            missing_finding = sorted(required_finding - finding.keys())
            if missing_finding:
                errors.append(f"findings[{index}] missing: {', '.join(missing_finding)}")
            if finding.get("evidence_level") not in ALLOWED_EVIDENCE:
                errors.append(f"findings[{index}].evidence_level is invalid")

    for item_path, key, value in walk(data):
        if key.lower() in DIRECT_IDENTIFIER_KEYS:
            errors.append(f"{item_path} is a prohibited direct-identifier field")
        if isinstance(value, str):
            if EMAIL_RE.search(value):
                errors.append(f"{item_path} contains an email address")
            if PHONE_RE.search(value):
                errors.append(f"{item_path} contains a phone number")
            if UNSUPPORTED_PROMISE_RE.search(value):
                errors.append(f"{item_path} contains an unsupported growth promise")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic", type=Path)
    args = parser.parse_args()

    try:
        data = load_json(args.diagnostic)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    for error in errors:
        print(f"ERROR: {error}")
    print("VALID" if not errors else "INVALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
