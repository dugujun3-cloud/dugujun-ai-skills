#!/usr/bin/env python3
"""Validate a Dugujun deep-research directory without third-party packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("research_dir", type=Path)
    args = parser.parse_args()
    root = args.research_dir.resolve()
    required = ["research_plan.yaml", "fields.yaml", "research_status.json"]
    errors = [f"missing: {name}" for name in required if not (root / name).is_file()]
    status_path = root / "research_status.json"
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(status, dict):
                errors.append("research_status.json must contain an object")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid research_status.json: {exc}")
    results_dir = root / "results"
    if results_dir.is_dir():
        for path in sorted(results_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid result {path.name}: {exc}")
                continue
            for key in ("id", "name", "fields", "sources", "uncertain", "checked_at"):
                if key not in data:
                    errors.append(f"{path.name} missing key: {key}")
            if not isinstance(data.get("sources"), list):
                errors.append(f"{path.name} sources must be a list")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
