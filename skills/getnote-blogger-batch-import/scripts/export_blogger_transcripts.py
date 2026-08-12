#!/usr/bin/env python3
"""Export 得到大脑 blogger transcripts to resumable Markdown/ZIP batches."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CLI = os.environ.get("GETNOTE_CLI", "getnote")
FORMAT_VERSION = 2


def run_getnote(cli: str, args: list[str], attempts: int = 3) -> dict[str, Any]:
    command = [cli, *args, "-o", "json"]
    last_error = ""
    for attempt in range(1, attempts + 1):
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if completed.returncode == 0:
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                last_error = f"invalid JSON: {exc}"
            else:
                if payload.get("success"):
                    return payload
                last_error = payload.get("message") or str(payload)
        else:
            last_error = completed.stderr.strip() or completed.stdout.strip()
        if attempt < attempts:
            time.sleep(attempt * 1.5)
    raise RuntimeError(f"getnote failed after {attempts} attempts: {last_error}")


def load_catalog(cli: str, topic_id: str, follow_id: str) -> list[dict[str, Any]]:
    page = 1
    catalog: list[dict[str, Any]] = []
    while True:
        payload = run_getnote(
            cli,
            ["kb", "blogger-contents", topic_id, follow_id, "--page", str(page)],
        )
        data = payload["data"]
        catalog.extend(data.get("contents", []))
        if not data.get("has_more"):
            break
        page += 1
    return catalog


def load_transcript(cli: str, topic_id: str, post_id: str) -> dict[str, Any]:
    payload = run_getnote(cli, ["kb", "blogger-content", topic_id, post_id])
    data = payload["data"]
    transcript = (data.get("post_media_text") or "").strip()
    if transcript:
        data["_body_text"] = transcript
        data["_body_source"] = "post_media_text"
    else:
        original_post_text = (data.get("post_name") or "").strip()
        if not original_post_text:
            raise RuntimeError("post_media_text and post_name are empty")
        data["_body_text"] = original_post_text
        data["_body_source"] = "post_name"
    return data


def safe_filename(title: str) -> tuple[str, bool]:
    cleaned = re.sub(r"[\x00-\x1f/]", "／", title).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    max_title_bytes = 240 - len(".md".encode("utf-8"))
    encoded = cleaned.encode("utf-8")[:max_title_bytes]
    while True:
        try:
            cleaned = encoded.decode("utf-8")
            break
        except UnicodeDecodeError:
            encoded = encoded[:-1]
    return f"{cleaned}.md", cleaned == title


def atomic_write_text(path: Path, text: str) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(text, encoding="utf-8")
    os.replace(temp_path, path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def transcript_record(
    item: dict[str, Any],
    index: int,
    detail: dict[str, Any],
    markdown_dir: Path,
) -> dict[str, Any]:
    post_id = item["post_id_alias"]
    title = (item.get("post_title") or detail.get("post_name") or "未命名").strip()
    transcript = (detail.get("_body_text") or "").strip().replace("\r\n", "\n")
    filename, filename_is_exact_title = safe_filename(title)
    markdown_path = markdown_dir / filename
    markdown = f"{transcript}\n"
    digest = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    atomic_write_text(markdown_path, markdown)
    return {
        "index": index,
        "format_version": FORMAT_VERSION,
        "post_id_alias": post_id,
        "title": title,
        "markdown_file": filename,
        "filename_is_exact_title": filename_is_exact_title,
        "transcript_chars": len(transcript),
        "transcript_sha256": digest,
        "body_source": detail.get("_body_source", "post_media_text"),
        "source_url": detail.get("post_url", ""),
        "publish_time": detail.get("post_publish_time", ""),
        "status": "exported",
    }


def build_zip(markdown_dir: Path, records: list[dict[str, Any]], archive_path: Path) -> None:
    temp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for record in sorted(records, key=lambda value: value["index"]):
            markdown_path = markdown_dir / record["markdown_file"]
            archive.write(markdown_path, arcname=record["markdown_file"])
    os.replace(temp_path, archive_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pilot", "remaining", "audit", "verify"))
    parser.add_argument("--cli", default=DEFAULT_CLI)
    parser.add_argument("--topic-id", required=True)
    parser.add_argument("--follow-id", required=True)
    parser.add_argument("--pilot-id")
    parser.add_argument("--skip-post-id", action="append", default=[])
    parser.add_argument("--expected-notes-total", type=int)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    markdown_dir = output_root / ("pilot" if args.mode == "pilot" else "markdown")
    archives_dir = output_root / "archives"
    logs_dir = output_root / "logs"
    for directory in (markdown_dir, archives_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog(args.cli, args.topic_id, args.follow_id)
    indexed = [(index, item) for index, item in enumerate(catalog, start=1)]
    if args.mode == "verify":
        payload = run_getnote(args.cli, ["kb", args.topic_id, "--all"])
        notes = payload["data"].get("notes", [])
        notes_by_title = {note.get("title", ""): note for note in notes}
        expected_bodies: dict[str, str] = {}
        for manifest_name in ("pilot_manifest.json", "remaining_manifest.json"):
            manifest_file = logs_dir / manifest_name
            if not manifest_file.exists():
                continue
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            for record in manifest_data.get("records", []):
                markdown_file = output_root / ("pilot" if manifest_name.startswith("pilot") else "markdown") / record["markdown_file"]
                if markdown_file.exists():
                    expected_bodies[record["title"]] = markdown_file.read_text(encoding="utf-8").strip()
        expected_titles = list(expected_bodies)
        missing_titles = [title for title in expected_titles if title not in notes_by_title]
        body_mismatches = []
        body_mismatch_details = []
        body_formatting_differences = []
        for title, expected_body in expected_bodies.items():
            note = notes_by_title.get(title)
            if note is None:
                continue
            actual_body = (note.get("content") or "").strip().replace("\r\n", "\n")
            if actual_body != expected_body.replace("\r\n", "\n"):
                expected_normalized = expected_body.replace("\r\n", "\n")
                detail = {
                    "title": title,
                    "expected_chars": len(expected_normalized),
                    "actual_chars": len(actual_body),
                    "equal_ignoring_whitespace": "".join(expected_normalized.split()) == "".join(actual_body.split()),
                    "expected_sha256": hashlib.sha256(expected_normalized.encode("utf-8")).hexdigest(),
                    "actual_sha256": hashlib.sha256(actual_body.encode("utf-8")).hexdigest(),
                }
                if detail["equal_ignoring_whitespace"]:
                    body_formatting_differences.append(detail)
                else:
                    body_mismatches.append(title)
                    body_mismatch_details.append(detail)
        report = {
            "notes_total": len(notes),
            "expected_notes_total": args.expected_notes_total,
            "expected_new_titles": len(expected_titles),
            "matched_new_titles": len(expected_titles) - len(missing_titles),
            "missing_titles": missing_titles,
            "body_checks": len(expected_bodies) - len(missing_titles),
            "body_exact_matches": len(expected_bodies) - len(missing_titles) - len(body_mismatches) - len(body_formatting_differences),
            "body_mismatches": body_mismatches,
            "body_mismatch_details": body_mismatch_details,
            "body_formatting_differences": body_formatting_differences,
            "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        report_path = logs_dir / "import_verification.json"
        atomic_write_json(report_path, report)
        print(json.dumps({"report": str(report_path), **report}, ensure_ascii=False))
        count_ok = args.expected_notes_total is None or len(notes) == args.expected_notes_total
        return 0 if count_ok and not missing_titles and not body_mismatches else 3
    if args.mode == "audit":
        title_counts: dict[str, int] = {}
        for _, item in indexed:
            title = (item.get("post_title") or "").strip()
            title_counts[title] = title_counts.get(title, 0) + 1
        issues = []
        for index, item in indexed:
            title = (item.get("post_title") or "").strip()
            filename, exact = safe_filename(title)
            if not exact or title_counts[title] > 1:
                issues.append({
                    "index": index,
                    "post_id_alias": item.get("post_id_alias", ""),
                    "title": title,
                    "filename": filename,
                    "filename_is_exact_title": exact,
                    "duplicate_title_count": title_counts[title],
                })
        audit = {
            "catalog_total": len(catalog),
            "issue_count": len(issues),
            "issues": issues,
        }
        audit_path = logs_dir / "title_filename_audit.json"
        atomic_write_json(audit_path, audit)
        print(json.dumps({"audit": str(audit_path), **audit}, ensure_ascii=False))
        return 0
    if args.mode == "pilot":
        if not args.pilot_id:
            raise RuntimeError("pilot mode requires --pilot-id")
        selected = [(index, item) for index, item in indexed if item["post_id_alias"] == args.pilot_id]
        archive_name = "pilot.zip"
        manifest_name = "pilot_manifest.json"
    else:
        skipped_post_ids = set(args.skip_post_id)
        selected = [(index, item) for index, item in indexed if item["post_id_alias"] not in skipped_post_ids]
        archive_name = f"blogger_notes_{len(selected)}_original_titles.zip"
        manifest_name = "remaining_manifest.json"

    if not selected:
        raise RuntimeError("No matching posts found")

    manifest_path = logs_dir / manifest_name
    previous_records: list[dict[str, Any]] = []
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}
        if previous.get("mode") == args.mode and previous.get("topic_id") == args.topic_id:
            previous_records = [
                record
                for record in previous.get("records", [])
                if record.get("format_version") == FORMAT_VERSION
                and (markdown_dir / record.get("markdown_file", "")).is_file()
            ]

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "format_version": FORMAT_VERSION,
        "mode": args.mode,
        "topic_id": args.topic_id,
        "follow_id": args.follow_id,
        "catalog_total": len(catalog),
        "completed_post_ids_skipped": sorted(set(args.skip_post_id)),
        "selected_total": len(selected),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "records": sorted(previous_records, key=lambda value: value["index"]),
        "errors": [],
    }
    atomic_write_json(manifest_path, manifest)

    records: list[dict[str, Any]] = list(previous_records)
    errors: list[dict[str, str]] = []
    completed_ids = {record["post_id_alias"] for record in records}
    pending = [pair for pair in selected if pair[1]["post_id_alias"] not in completed_ids]

    def fetch(pair: tuple[int, dict[str, Any]]) -> tuple[int, dict[str, Any], dict[str, Any]]:
        index, item = pair
        return index, item, load_transcript(args.cli, args.topic_id, item["post_id_alias"])

    workers = 1 if args.mode == "pilot" else max(1, min(args.workers, 8))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, pair): pair for pair in pending}
        for future in concurrent.futures.as_completed(futures):
            index, item = futures[future]
            try:
                _, _, detail = future.result()
                record = transcript_record(item, index, detail, markdown_dir)
                records.append(record)
            except Exception as exc:  # noqa: BLE001
                errors.append(
                    {
                        "index": str(index),
                        "post_id_alias": item.get("post_id_alias", ""),
                        "title": item.get("post_title", ""),
                        "error": str(exc),
                    }
                )
            manifest["records"] = sorted(records, key=lambda value: value["index"])
            manifest["errors"] = sorted(errors, key=lambda value: int(value["index"]))
            atomic_write_json(manifest_path, manifest)

    if errors:
        print(f"Export incomplete: {len(errors)} error(s). See {manifest_path}", file=sys.stderr)
        return 2

    archive_path = archives_dir / archive_name
    build_zip(markdown_dir, records, archive_path)
    manifest["archive"] = str(archive_path)
    manifest["archive_sha256"] = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    atomic_write_json(manifest_path, manifest)
    print(json.dumps({
        "manifest": str(manifest_path),
        "archive": str(archive_path),
        "exported": len(records),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
