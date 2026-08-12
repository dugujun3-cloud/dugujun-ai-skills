#!/usr/bin/env python3
"""Validate a membership-campaign ROI result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


GRADES = {"A_experimental", "B_comparative", "C_historical", "D_descriptive", "E_unanswerable"}
ACTIONS = {
    "pause_and_investigate", "evidence_insufficient", "do_not_scale",
    "adjust_or_stop", "eligible_for_small_scale", "compare_with_business_thresholds",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    errors = []
    try:
        data = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if data.get("status") != "calculated":
        errors.append("status must be calculated")
    if data.get("evidence_grade") not in GRADES:
        errors.append("invalid evidence_grade")
    if not isinstance(data.get("claim_boundary"), str) or not data["claim_boundary"].strip():
        errors.append("claim_boundary is required")
    if not isinstance(data.get("metrics"), dict):
        errors.append("metrics must be an object")
    decision = data.get("decision")
    if not isinstance(decision, dict) or decision.get("action") not in ACTIONS:
        errors.append("invalid decision.action")
    output = {"status": "passed" if not errors else "failed", "errors": errors}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

