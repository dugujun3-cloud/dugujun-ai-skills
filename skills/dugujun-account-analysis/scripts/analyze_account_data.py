#!/usr/bin/env python3
"""Normalize content-account post data and produce evidence-first baselines."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def configured_knowledge_base() -> Path | None:
    """Optional read-only knowledge-base root via DUGUJUN_KNOWLEDGE_BASE_ROOT."""
    raw = os.environ.get("DUGUJUN_KNOWLEDGE_BASE_ROOT", "").strip()
    return Path(raw).expanduser().resolve() if raw else None

TEXT_FIELDS = ["post_id", "title", "published_at", "content_type", "url"]
NUMERIC_FIELDS = [
    "impressions",
    "views",
    "likes",
    "comments",
    "saves",
    "shares",
    "followers_gain",
    "click_through_rate",
    "watch_time_seconds",
    "duration_seconds",
    "engagements",
]
OUTPUT_FIELDS = TEXT_FIELDS + NUMERIC_FIELDS

ALIASES = {
    "post_id": ["post_id", "note_id", "video_id", "作品id", "笔记id", "视频id", "内容id", "id"],
    "title": ["title", "标题", "作品标题", "笔记标题", "视频标题", "内容标题"],
    "published_at": ["published_at", "publish_time", "发布时间", "首次发布时间", "发布日期", "时间", "date"],
    "content_type": ["content_type", "type", "体裁", "内容类型", "作品类型", "笔记类型", "形式"],
    "url": ["url", "link", "链接", "作品链接", "笔记链接", "视频链接", "分享链接"],
    "impressions": ["impressions", "exposure", "曝光", "曝光量", "展现", "展现量"],
    "views": ["views", "view_count", "read_count", "观看", "观看量", "播放", "播放量", "阅读", "阅读量"],
    "likes": ["likes", "like_count", "点赞", "点赞量", "赞同", "赞同数"],
    "comments": ["comments", "comment_count", "评论", "评论量", "评论数"],
    "saves": ["saves", "favorites", "collects", "收藏", "收藏量", "收藏数"],
    "shares": ["shares", "share_count", "分享", "分享量", "转发", "转发量"],
    "followers_gain": ["followers_gain", "follower_gain", "涨粉", "新增粉丝", "净增粉丝"],
    "click_through_rate": ["click_through_rate", "ctr", "点击率", "封面点击率"],
    "watch_time_seconds": ["watch_time_seconds", "avg_watch_time", "平均播放时长", "人均观看时长", "观看时长"],
    "duration_seconds": ["duration_seconds", "duration", "视频时长", "作品时长", "时长"],
    "engagements": ["engagements", "engagement", "互动", "互动量", "互动数"],
}

PLATFORM_DEFAULTS = {
    "xiaohongshu": "saves",
    "rednote": "saves",
    "小红书": "saves",
    "douyin": "views",
    "抖音": "views",
    "bilibili": "views",
    "b站": "views",
    "zhihu": "views",
    "知乎": "views",
}


def normalize_key(value: Any) -> str:
    return re.sub(r"[\s_\-（）()]+", "", str(value).strip().lower())


NORMALIZED_ALIASES = {
    field: tuple(dict.fromkeys(normalize_key(alias) for alias in aliases))
    for field, aliases in ALIASES.items()
}


def parse_number(value: Any, *, rate: bool = False) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        if rate and number > 1:
            number /= 100.0
        return number

    text = str(value).strip().lower().replace(",", "").replace("，", "")
    if not text or text in {"-", "--", "—", "n/a", "na", "null", "none"}:
        return None

    percent = text.endswith("%")
    if percent:
        text = text[:-1].strip()

    multiplier = 1.0
    units = [("万", 10000.0), ("w", 10000.0), ("k", 1000.0)]
    for suffix, factor in units:
        if text.endswith(suffix):
            multiplier = factor
            text = text[: -len(suffix)].strip()
            break

    match = re.search(r"[-+]?\d*\.?\d+", text)
    if not match:
        return None
    number = float(match.group()) * multiplier
    if percent or (rate and number > 1):
        number /= 100.0
    return number


def parse_date(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    normalized = text.replace("年", "-").replace("月", "-").replace("日", "")
    normalized = normalized.replace("/", "-").replace(".", "-")
    candidates = [normalized, normalized[:19], normalized[:10]]
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y-%m",
    ]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in formats:
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = next(
                (
                    payload[key]
                    for key in ("posts", "items", "data", "results", "records")
                    if isinstance(payload.get(key), list)
                ),
                None,
            )
            if records is None:
                raise ValueError("JSON must be a list or contain posts/items/data/results/records list")
        else:
            raise ValueError("JSON input must contain objects")
        if not all(isinstance(item, dict) for item in records):
            raise ValueError("Every JSON record must be an object")
        return [dict(item) for item in records]
    raise ValueError("Only UTF-8 CSV and JSON are supported; convert XLSX to CSV first")


def find_value(row: dict[str, Any], field: str) -> Any:
    normalized_row = {normalize_key(key): value for key, value in row.items()}
    for alias in NORMALIZED_ALIASES[field]:
        if alias in normalized_row:
            return normalized_row[alias]
    return None


def stable_post_id(row: dict[str, Any], index: int) -> str:
    explicit = str(find_value(row, "post_id") or "").strip()
    if explicit:
        return explicit
    basis = "|".join(
        str(find_value(row, field) or "").strip() for field in ("url", "title", "published_at")
    )
    if not basis.replace("|", ""):
        basis = f"row-{index + 1}"
    return "generated-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def normalize_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    duplicate_count = 0

    for index, raw in enumerate(records):
        post_id = stable_post_id(raw, index)
        url = str(find_value(raw, "url") or "").strip()
        dedupe_key = url or post_id
        if dedupe_key in seen:
            duplicate_count += 1
            continue
        seen.add(dedupe_key)

        row: dict[str, Any] = {
            "post_id": post_id,
            "title": str(find_value(raw, "title") or "").strip(),
            "published_at": str(find_value(raw, "published_at") or "").strip(),
            "content_type": str(find_value(raw, "content_type") or "unknown").strip() or "unknown",
            "url": url,
        }
        for field in NUMERIC_FIELDS:
            row[field] = parse_number(find_value(raw, field), rate=field == "click_through_rate")

        if row["engagements"] is None:
            components = [row[field] for field in ("likes", "comments", "saves", "shares")]
            if any(value is not None for value in components):
                row["engagements"] = sum(value or 0.0 for value in components)
        normalized.append(row)

    return normalized, duplicate_count


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def metric_stats(records: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    rows = list(records)
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return {
        "available": len(values),
        "missing": len(rows) - len(values),
        "zero_rate": (sum(value == 0 for value in values) / len(values)) if values else None,
        "sum": sum(values) if values else None,
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "p75": percentile(values, 0.75),
        "p90": percentile(values, 0.90),
        "max": max(values) if values else None,
    }


def choose_primary_metric(records: list[dict[str, Any]], platform: str, requested: str | None) -> str:
    if requested:
        if requested not in NUMERIC_FIELDS:
            raise ValueError(f"Unsupported primary metric: {requested}")
        if not any(row.get(requested) is not None for row in records):
            raise ValueError(f"Primary metric has no usable values: {requested}")
        return requested

    default = PLATFORM_DEFAULTS.get(platform.strip().lower(), "views")
    candidates = [default, "views", "impressions", "saves", "engagements", "likes"]
    for field in dict.fromkeys(candidates):
        if any(row.get(field) is not None for row in records):
            return field
    raise ValueError("No usable result metric found")


def ranked_posts(records: list[dict[str, Any]], field: str, descending: bool) -> list[dict[str, Any]]:
    available = [row for row in records if row.get(field) is not None]
    count = min(10, max(1, math.ceil(len(available) * 0.2))) if available else 0
    ordered = sorted(available, key=lambda row: float(row[field]), reverse=descending)
    return [
        {
            "post_id": row["post_id"],
            "title": row["title"],
            "published_at": row["published_at"],
            "content_type": row["content_type"],
            field: row[field],
            "url": row["url"],
        }
        for row in ordered[:count]
    ]


def build_baseline(records: list[dict[str, Any]], primary_metric: str) -> dict[str, Any]:
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    invalid_dates = 0

    for row in records:
        by_type[row["content_type"]].append(row)
        parsed = parse_date(row["published_at"])
        if parsed:
            by_month[parsed.strftime("%Y-%m")].append(row)
        elif row["published_at"]:
            invalid_dates += 1

    return {
        "sample_size": len(records),
        "primary_metric": primary_metric,
        "metrics": {field: metric_stats(records, field) for field in NUMERIC_FIELDS},
        "by_content_type": {
            group: {
                "sample_size": len(rows),
                "primary_metric": metric_stats(rows, primary_metric),
            }
            for group, rows in sorted(by_type.items())
        },
        "by_month": {
            month: {
                "sample_size": len(rows),
                "primary_metric": metric_stats(rows, primary_metric),
            }
            for month, rows in sorted(by_month.items())
        },
        "invalid_date_values": invalid_dates,
        "top_posts": ranked_posts(records, primary_metric, descending=True),
        "bottom_posts": ranked_posts(records, primary_metric, descending=False),
    }


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [round_value(item) for item in value]
    return value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def quantitative_markdown(
    platform: str,
    account: str,
    baseline: dict[str, Any],
    quality: dict[str, Any],
) -> str:
    primary = baseline["primary_metric"]
    stats = baseline["metrics"][primary]
    lines = [
        "# 量化摘要",
        "",
        f"- 平台：{platform}",
        f"- 账号：{account}",
        f"- 有效作品：{baseline['sample_size']}",
        f"- 主指标：{primary}",
        f"- 主指标中位数：{display(stats['median'])}",
        f"- 主指标 P75：{display(stats['p75'])}",
        f"- 主指标 P90：{display(stats['p90'])}",
        f"- 主指标零值率：{display(stats['zero_rate'])}",
        "",
        "## 数据质量",
        "",
        f"- 原始行数：{quality['source_rows']}",
        f"- 去重后行数：{quality['normalized_rows']}",
        f"- 重复行：{quality['duplicate_rows']}",
        f"- 无法解析日期：{quality['invalid_date_values']}",
        "",
        "## 内容形态",
        "",
        "| 类型 | 样本量 | 中位数 | P75 | P90 | 零值率 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group, payload in baseline["by_content_type"].items():
        group_stats = payload["primary_metric"]
        lines.append(
            "| {group} | {count} | {median} | {p75} | {p90} | {zero} |".format(
                group=group,
                count=payload["sample_size"],
                median=display(group_stats["median"]),
                p75=display(group_stats["p75"]),
                p90=display(group_stats["p90"]),
                zero=display(group_stats["zero_rate"]),
            )
        )

    lines.extend(["", "## Top 作品", ""])
    for index, row in enumerate(baseline["top_posts"], 1):
        lines.append(f"{index}. {row['title'] or row['post_id']} — {primary}: {display(row[primary])}")
    lines.extend(
        [
            "",
            "> 本文件只陈述可计算事实。定位、原因和策略必须结合内容编码与证据账本后再判断。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 CSV or JSON file")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--primary-metric", choices=NUMERIC_FIELDS)
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")
    knowledge_base = configured_knowledge_base()
    if knowledge_base is not None and (
        output_dir == knowledge_base or knowledge_base in output_dir.parents
    ):
        raise SystemExit("Refusing to write inside the read-only knowledge base")

    records = load_records(input_path)
    if not records:
        raise SystemExit("Input contains no records")
    normalized, duplicates = normalize_records(records)
    if not normalized:
        raise SystemExit("No usable records after normalization")

    output_dir.mkdir(parents=True, exist_ok=True)
    primary_metric = choose_primary_metric(normalized, args.platform, args.primary_metric)
    baseline = build_baseline(normalized, primary_metric)
    quality = {
        "source_rows": len(records),
        "normalized_rows": len(normalized),
        "duplicate_rows": duplicates,
        "invalid_date_values": baseline["invalid_date_values"],
        "field_coverage": {
            field: round(sum(row.get(field) is not None and row.get(field) != "" for row in normalized) / len(normalized), 4)
            for field in OUTPUT_FIELDS
        },
        "warnings": [
            warning
            for warning, present in (
                ("Sample size is below 5; treat patterns as hypotheses", len(normalized) < 5),
                ("Some duplicate rows were removed", duplicates > 0),
                ("Some date values could not be parsed", baseline["invalid_date_values"] > 0),
            )
            if present
        ],
    }

    with (output_dir / "normalized_posts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(normalized)

    write_json(output_dir / "data_quality.json", quality)
    write_json(output_dir / "account_baseline.json", baseline)
    (output_dir / "quantitative_summary.md").write_text(
        quantitative_markdown(args.platform, args.account, baseline, quality), encoding="utf-8"
    )

    manifest_path = output_dir / "input_manifest.json"
    if not manifest_path.exists():
        write_json(
            manifest_path,
            {
                "platform": args.platform,
                "account": args.account,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "sources": [
                    {
                        "type": "user_or_workspace_file",
                        "path": str(input_path),
                        "evidence_level": "A_or_C_requires_manual_confirmation",
                        "source_rows": len(records),
                    }
                ],
                "paid_api_calls": [],
            },
        )

    write_json(
        output_dir / "workflow_status.json",
        {
            "schema_version": 1,
            "workflow": "dugujun-account-analysis",
            "platform": args.platform,
            "account": args.account,
            "state": "normalized",
            "primary_metric": primary_metric,
            "sample_size": len(normalized),
            "outputs": [
                "input_manifest.json",
                "normalized_posts.csv",
                "data_quality.json",
                "account_baseline.json",
                "quantitative_summary.md",
            ],
            "next_action": "encode_content_and_write_evidence_ledger",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    result = {
        "output_dir": str(output_dir),
        "source_rows": len(records),
        "normalized_rows": len(normalized),
        "duplicate_rows": duplicates,
        "primary_metric": primary_metric,
        "warnings": quality["warnings"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
