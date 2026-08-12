#!/usr/bin/env python3
"""Calculate membership-campaign observed and incremental economics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_brief import load_json, validate


GRADE_BY_TYPE = {
    "randomized_control": "A_experimental",
    "matched_control": "B_comparative",
    "historical_baseline": "C_historical",
    "none": "D_descriptive",
}


def safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def rounded(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def baseline_rate(counterfactual: dict[str, Any]) -> float | None:
    kind = counterfactual["type"]
    if kind in {"randomized_control", "matched_control"}:
        return safe_divide(float(counterfactual["control_results"]), float(counterfactual["control_eligible"]))
    if kind == "historical_baseline":
        return float(counterfactual["baseline_result_rate"])
    return None


def breached_guardrails(guardrails: dict[str, Any]) -> list[str]:
    breached = []
    if guardrails.get("capacity_breached"):
        breached.append("capacity_breached")
    if guardrails.get("privacy_or_compliance_issue"):
        breached.append("privacy_or_compliance_issue")
    return breached


def evaluate_thresholds(metrics: dict[str, Any], thresholds: dict[str, Any]) -> tuple[str, list[str]]:
    supplied = {key: value for key, value in thresholds.items() if value is not None}
    if not supplied:
        return "compare_with_business_thresholds", ["未提供经业务批准的继续阈值"]
    failures = []
    max_cost = supplied.get("max_cost_per_incremental_result")
    if max_cost is not None:
        actual = metrics.get("cost_per_incremental_result")
        if actual is None or actual > max_cost:
            failures.append("单位增量结果成本未达标")
    min_net = supplied.get("min_net_incremental_value")
    if min_net is not None:
        actual = metrics.get("net_incremental_value")
        if actual is None or actual < min_net:
            failures.append("增量净值未达标")
    min_roi = supplied.get("min_incremental_roi")
    if min_roi is not None:
        actual = metrics.get("net_incremental_roi")
        if actual is None or actual < min_roi:
            failures.append("增量ROI未达标")
    if failures:
        return "adjust_or_stop", failures
    return "eligible_for_small_scale", ["已通过用户提供的业务阈值，仍需人工审批"]


def calculate(data: dict[str, Any]) -> dict[str, Any]:
    population = data["population"]
    counterfactual = population["counterfactual"]
    treatment_eligible = float(population["treatment_eligible"])
    treatment_results = float(population["treatment_results"])
    observed_rate = treatment_results / treatment_eligible
    base_rate = baseline_rate(counterfactual)
    expected_baseline_results = treatment_eligible * base_rate if base_rate is not None else None
    incremental_results = treatment_results - expected_baseline_results if expected_baseline_results is not None else None
    total_cost = sum(float(value) for value in data["costs"].values())
    observed_cost_per_result = safe_divide(total_cost, treatment_results)
    cost_per_incremental_result = (
        safe_divide(total_cost, incremental_results)
        if incremental_results is not None and incremental_results > 0
        else None
    )
    economics = data["economics"]
    contribution_per_result = economics.get("contribution_value_per_result")
    observed_contribution = None
    baseline_contribution = None
    descriptive_roi = None
    incremental_contribution = None
    net_incremental_value = None
    benefit_cost_ratio = None
    net_incremental_roi = None
    has_treatment_economics = all(
        economics.get(key) is not None
        for key in ("treatment_net_revenue", "treatment_variable_costs")
    )
    if has_treatment_economics:
        observed_contribution = (
            float(economics["treatment_net_revenue"])
            - float(economics["treatment_variable_costs"])
        )
        if counterfactual["type"] in {"randomized_control", "matched_control"}:
            comparison_contribution = (
                float(economics["comparison_net_revenue"])
                - float(economics["comparison_variable_costs"])
            )
            scale = treatment_eligible / float(counterfactual["control_eligible"])
            baseline_contribution = comparison_contribution * scale
        elif counterfactual["type"] == "historical_baseline":
            baseline_contribution = (
                treatment_eligible * float(economics["baseline_contribution_per_eligible"])
            )
        descriptive_roi = safe_divide(observed_contribution - total_cost, total_cost)
        if baseline_contribution is not None:
            incremental_contribution = observed_contribution - baseline_contribution
    elif contribution_per_result is not None:
        contribution_per_result = float(contribution_per_result)
        observed_contribution = treatment_results * contribution_per_result
        descriptive_roi = safe_divide(observed_contribution - total_cost, total_cost)
        if incremental_results is not None:
            incremental_contribution = incremental_results * contribution_per_result
    if incremental_contribution is not None:
        net_incremental_value = incremental_contribution - total_cost
        benefit_cost_ratio = safe_divide(incremental_contribution, total_cost)
        net_incremental_roi = safe_divide(net_incremental_value, total_cost)

    metrics = {
        "observed_result_rate": rounded(observed_rate),
        "baseline_result_rate": rounded(base_rate),
        "result_rate_lift": rounded(observed_rate - base_rate) if base_rate is not None else None,
        "expected_baseline_results": rounded(expected_baseline_results),
        "incremental_results": rounded(incremental_results),
        "total_campaign_cost": rounded(total_cost),
        "observed_cost_per_result": rounded(observed_cost_per_result),
        "cost_per_incremental_result": rounded(cost_per_incremental_result),
        "observed_contribution_value": rounded(observed_contribution),
        "baseline_contribution_value": rounded(baseline_contribution),
        "descriptive_roi": rounded(descriptive_roi),
        "incremental_contribution_value": rounded(incremental_contribution),
        "benefit_cost_ratio": rounded(benefit_cost_ratio),
        "net_incremental_value": rounded(net_incremental_value),
        "net_incremental_roi": rounded(net_incremental_roi),
    }

    guardrail_breaches = breached_guardrails(data["guardrails"])
    if guardrail_breaches:
        action = "pause_and_investigate"
        reasons = ["触发履约、隐私或合规硬护栏"]
    elif base_rate is None:
        action = "evidence_insufficient"
        reasons = ["没有反事实，只能报告观察结果和描述性成本"]
    elif incremental_results is None or incremental_results <= 0:
        action = "do_not_scale"
        reasons = ["当前口径下增量结果不为正，先排查口径、人群和机制"]
    else:
        action, reasons = evaluate_thresholds(metrics, data.get("business_thresholds", {}))

    claim_boundary = {
        "randomized_control": "合格随机对照下可讨论实验增量，但仍需检查污染、样本和执行偏差。",
        "matched_control": "同窗匹配比较只支持方向判断，不能写成唯一因果。",
        "historical_baseline": "相对历史基线的估计，不能证明活动造成变化。",
        "none": "没有反事实，不得使用增量或因果表述。",
    }[counterfactual["type"]]

    return {
        "schema_version": "1.0",
        "status": "calculated",
        "decision_question": data["decision_question"],
        "objective": data["objective"],
        "result_name": data["result_name"],
        "currency": data.get("currency", "CNY"),
        "observation_window": data["observation_window"],
        "maturity_rule": data["maturity_rule"],
        "counterfactual_type": counterfactual["type"],
        "evidence_grade": GRADE_BY_TYPE[counterfactual["type"]],
        "claim_boundary": claim_boundary,
        "metrics": metrics,
        "guardrail_breaches": guardrail_breaches,
        "decision": {"action": action, "reasons": reasons},
        "known_changes": data.get("known_changes", []),
        "synthetic": bool(data.get("synthetic", False)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = load_json(args.brief)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    errors = validate(data)
    if errors:
        print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    result = calculate(data)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
