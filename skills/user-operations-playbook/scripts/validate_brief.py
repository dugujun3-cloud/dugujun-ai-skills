#!/usr/bin/env python3
"""Validate a structured user-operations brief without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CORE_FIELDS = (
    "product",
    "business_goal",
    "target_users",
    "problem",
    "primary_metric",
    "time_window",
)

ANALYSIS_FIELDS = {
    "acquisition": (
        {"user_id", "channel", "cost", "first_seen_time", "key_behavior"},
        {"user_id", "channel", "cost", "signup_time", "event_name", "event_time"},
    ),
    "activation": (
        {"user_id", "first_seen_time", "event_name", "event_time"},
        {"user_id", "signup_time", "event_name", "event_time"},
    ),
    "engagement": ({"user_id", "event_name", "event_time"},),
    "funnel": ({"user_id", "event_name", "event_time"},),
    "retention": (
        {"user_id", "event_time", "event_name", "cohort_time"},
        {"user_id", "event_time", "event_name", "signup_time"},
    ),
    "ltv": (
        {"user_id", "transaction_time", "revenue"},
        {"user_id", "transaction_time", "gross_profit"},
    ),
    "experiment": (
        {"user_id", "variant", "exposure_time", "outcome"},
        {"user_id", "group", "exposure_time", "outcome"},
    ),
    "segmentation": (
        {"user_id", "last_transaction_time", "transaction_count", "revenue"},
        {"user_id", "event_time", "event_name"},
    ),
    "repurchase": (
        {"user_id", "transaction_time", "revenue", "product_id"},
        {"user_id", "transaction_time", "gross_profit", "product_id"},
    ),
    "referral": (
        {"referrer_user_id", "referred_user_id", "invite_time", "key_behavior"},
        {"user_id", "referral_code", "event_name", "event_time"},
    ),
    "membership": (
        {"user_id", "membership_start", "membership_status", "transaction_time", "revenue"},
        {"user_id", "membership_start", "membership_status", "benefit_cost", "gross_profit"},
    ),
    "private_domain": ({"user_id", "touch_time", "touch_channel", "outcome"},),
    "campaign": (
        {"user_id", "group", "exposure_time", "outcome", "cost"},
        {"user_id", "variant", "exposure_time", "outcome", "cost"},
    ),
    "crm_journey": ({"user_id", "journey_version", "event_name", "event_time", "outcome"},),
    "b2b_customer_success": (
        {"account_id", "event_name", "event_time", "contract_status"},
        {"account_id", "health_score", "renewal_time", "contract_value"},
    ),
    "service_voc": (
        {"user_id", "ticket_id", "ticket_time", "ticket_status", "outcome"},
        {"user_id", "survey_time", "survey_score", "survey_topic"},
    ),
}

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_number": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "wechat_openid": re.compile(r"\bopenid\b", re.IGNORECASE),
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


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_core = [field for field in CORE_FIELDS if not data.get(field)]
    if missing_core:
        warnings.append("missing core context: " + ", ".join(missing_core))

    available_fields_raw = data.get("available_fields", [])
    if not isinstance(available_fields_raw, list):
        errors.append("available_fields must be a list")
        available_fields: set[str] = set()
    else:
        available_fields = {str(item).strip() for item in available_fields_raw if str(item).strip()}

    analysis_type = str(data.get("analysis_type", "diagnosis")).lower()
    if analysis_type not in {"diagnosis", *ANALYSIS_FIELDS}:
        warnings.append(
            "unknown analysis_type; use diagnosis or one of: " + ", ".join(sorted(ANALYSIS_FIELDS))
        )
    required_options = ANALYSIS_FIELDS.get(analysis_type)
    if required_options and not any(option <= available_fields for option in required_options):
        options = [" + ".join(sorted(option)) for option in required_options]
        warnings.append(
            f"{analysis_type} analysis is not supported by available_fields; provide one of: "
            + " OR ".join(options)
        )

    if analysis_type == "ltv" and not data.get("value_definition"):
        warnings.append("define value_definition as revenue, gross_profit, or contribution_profit")

    if analysis_type in ANALYSIS_FIELDS and not data.get("time_window"):
        warnings.append("a time_window is required for comparable analysis")

    privacy_hits: list[str] = []
    joined = "\n".join(flatten_strings(data))
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(joined):
            privacy_hits.append(label)
    if privacy_hits:
        errors.append(
            "direct identifiers detected: "
            + ", ".join(privacy_hits)
            + "; replace them with anonymous IDs before analysis"
        )

    if data.get("synthetic") is False and data.get("contains_real_personal_data") is True:
        errors.append("brief declares real personal data; anonymize and minimize before use")

    return {
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "analysis_type": analysis_type,
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
