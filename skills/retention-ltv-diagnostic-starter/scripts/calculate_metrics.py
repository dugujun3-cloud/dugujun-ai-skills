#!/usr/bin/env python3
"""Calculate supported cohort retention, repurchase and observed-value metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_brief import load_json, validate_brief


def ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def metrics_for_cohort(row: dict[str, Any], ltv_basis: str) -> dict[str, Any]:
    eligible = float(row["eligible_users"])
    revenue = float(row["revenue"])
    refunds = float(row["refunds"])
    costs = float(row["variable_costs"])
    acquisition_cost = float(row["acquisition_cost"])
    net_revenue = revenue - refunds
    contribution = net_revenue - costs

    value_total = net_revenue if ltv_basis == "revenue" else contribution
    observed_value = ratio(value_total, eligible)
    cac = ratio(acquisition_cost, eligible)
    ltv_cac = None
    if observed_value is not None and cac not in (None, 0):
        ltv_cac = round(observed_value / cac, 6)

    return {
        "name": row["name"],
        "mature": row["mature"],
        "synthetic": bool(row.get("synthetic", False)),
        "eligible_users": int(row["eligible_users"]),
        "retention_rate": ratio(float(row["retained_users"]), eligible),
        "repeat_purchase_rate": ratio(float(row["repeat_buyers"]), eligible),
        "net_revenue": round(net_revenue, 2),
        "contribution": round(contribution, 2),
        "observed_value_basis": ltv_basis,
        "observed_value_per_eligible_user": observed_value,
        "cac_per_eligible_user": cac,
        "observed_value_to_cac": ltv_cac,
    }


def aggregate(rows: list[dict[str, Any]], ltv_basis: str) -> dict[str, Any] | None:
    if not rows:
        return None
    combined = {
        "name": "mature-cohorts-total",
        "eligible_users": sum(float(row["eligible_users"]) for row in rows),
        "retained_users": sum(float(row["retained_users"]) for row in rows),
        "repeat_buyers": sum(float(row["repeat_buyers"]) for row in rows),
        "revenue": sum(float(row["revenue"]) for row in rows),
        "refunds": sum(float(row["refunds"]) for row in rows),
        "variable_costs": sum(float(row["variable_costs"]) for row in rows),
        "acquisition_cost": sum(float(row["acquisition_cost"]) for row in rows),
        "mature": True,
        "synthetic": all(bool(row.get("synthetic", False)) for row in rows),
    }
    return metrics_for_cohort(combined, ltv_basis)


def calculate(data: dict[str, Any]) -> dict[str, Any]:
    ltv_basis = data["business"]["ltv_basis"]
    cohort_metrics = [metrics_for_cohort(row, ltv_basis) for row in data["cohorts"]]
    mature_rows = [row for row in data["cohorts"] if row["mature"]]
    warnings: list[str] = []
    if len(mature_rows) != len(data["cohorts"]):
        warnings.append("immature cohorts are shown separately and excluded from the mature aggregate")
    if not mature_rows:
        warnings.append("no mature cohorts; do not make release or causal decisions")
    if any(row["variable_costs"] == 0 for row in data["cohorts"]):
        warnings.append("zero variable_costs may mean contribution value is incomplete")

    return {
        "schema_version": "1.0",
        "decision_question": data["decision_question"],
        "window": data["observation"]["window"],
        "as_of": data["observation"]["as_of"],
        "ltv_basis": ltv_basis,
        "cohorts": cohort_metrics,
        "mature_aggregate": aggregate(mature_rows, ltv_basis),
        "warnings": warnings,
        "interpretation_limits": [
            "metrics are descriptive unless a valid counterfactual is supplied",
            "observed window value is not lifetime value",
            "value-bridge components do not prove causal roots",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        data = load_json(args.brief)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_brief(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    payload = calculate(data)
    payload["input_warnings"] = warnings
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
