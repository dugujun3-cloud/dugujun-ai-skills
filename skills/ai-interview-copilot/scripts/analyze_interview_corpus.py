#!/usr/bin/env python3
"""Aggregate extracted interview JSON files by session coverage, not keyword volume."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def normalize(text: str) -> str:
    text = re.sub(r"[\s，。！？、,.!?：:；;（）()\-—]+", "", text.lower())
    return re.sub(r"^(那|然后|好的|好|嗯|ok)+", "", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    files = sorted(args.input_dir.glob("*.json"))
    sessions: list[dict[str, object]] = []
    type_sessions: defaultdict[str, set[str]] = defaultdict(set)
    normalized_questions: defaultdict[str, dict[str, object]] = defaultdict(lambda: {"count": 0, "sessions": set(), "examples": []})
    review_needed = []

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        source = str(data.get("source", path.name))
        questions = data.get("questions", [])
        types = Counter(
            str(label)
            for item in questions
            for label in (item.get("types") or [item.get("type", "其他追问")])
        )
        for label in types:
            type_sessions[label].add(source)
        for item in questions:
            text = str(item.get("text", "")).strip()
            key = normalize(text)
            if not key:
                continue
            bucket = normalized_questions[key]
            bucket["count"] = int(bucket["count"]) + 1
            bucket["sessions"].add(source)
            if text not in bucket["examples"] and len(bucket["examples"]) < 3:
                bucket["examples"].append(text)
        if data.get("role_detection", {}).get("needs_review"):
            review_needed.append(source)
        sessions.append({"source": source, "source_type": data.get("source_type"), "question_count": len(questions), "question_types": dict(types)})

    recurring = []
    for bucket in normalized_questions.values():
        session_names = sorted(bucket["sessions"])
        if len(session_names) >= 2:
            recurring.append({"session_count": len(session_names), "occurrence_count": bucket["count"], "examples": bucket["examples"], "sessions": session_names})
    recurring.sort(key=lambda item: (-item["session_count"], -item["occurrence_count"], item["examples"][0]))

    result = {
        "method_note": "Frequency is ranked by number of distinct interview sessions. Review inferred speaker roles before treating counts as final.",
        "summary": {
            "session_count": len(sessions),
            "role_filtered_question_count": sum(int(session["question_count"]) for session in sessions),
            "role_review_needed": review_needed,
        },
        "type_session_coverage": dict(sorted(((label, len(names)) for label, names in type_sessions.items()), key=lambda item: (-item[1], item[0]))),
        "recurring_questions": recurring,
        "sessions": sessions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
