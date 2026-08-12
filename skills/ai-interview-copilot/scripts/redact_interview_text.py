#!/usr/bin/env python3
"""Redact common identifiers and user-specified entities from interview text."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATTERNS = (
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[PHONE]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[ID]"),
    (re.compile(r"https?://\S+"), "[URL]"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--replace", action="append", default=[], help="SOURCE=LABEL")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    for item in args.replace:
        source, separator, label = item.partition("=")
        if not separator or not source:
            raise SystemExit(f"invalid --replace: {item}")
        text = text.replace(source, label or "[REDACTED]")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

