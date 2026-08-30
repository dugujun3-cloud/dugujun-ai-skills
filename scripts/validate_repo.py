#!/usr/bin/env python3
"""Validate the public Agent Skills repository without third-party packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
MANIFEST_PATH = ROOT / "skills-manifest.json"

REQUIRED_ROOT_FILES = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "skills-manifest.json",
}
FORBIDDEN_NAMES = {".DS_Store"}
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".log", ".zip"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_REPOSITORY_BYTES = 30 * 1024 * 1024
ALLOWED_MATURITY = {"stable", "beta"}
ALLOWED_SOURCE_STATUS = {
    "current",
    "sync-audit-required",
    "build-audit-required",
    "canonical-source-missing",
}

SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "GitHub classic token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
}
LOCAL_PATH_PATTERNS = {
    "macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "Linux home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "Windows home path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\]+\\\\"),
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def parse_skill_frontmatter_text(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")

    lines = match.group(1).splitlines()
    result: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        key_match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if not key_match:
            index += 1
            continue
        key, raw_value = key_match.group(1), (key_match.group(2) or "").strip()
        if raw_value in {"|", "|-", ">", ">-", "|+", ">+"}:
            block: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
                block.append(lines[index].strip())
                index += 1
            result[key] = "\n".join(block).strip()
            continue
        if raw_value.startswith(("'", '"')) and raw_value.endswith(raw_value[0]):
            raw_value = raw_value[1:-1]
        elif ": " in raw_value:
            raise ValueError(f"unquoted colon in {key}")
        result[key] = raw_value.strip()
        index += 1
    return result


def load_manifest(errors: list[str]) -> dict[str, object]:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"manifest: cannot parse {MANIFEST_PATH.name}: {exc}")
        return {}
    if payload.get("schema_version") != 1:
        errors.append("manifest: schema_version must be 1")
    return payload


def validate_markdown_links(path: Path, text: str, errors: list[str]) -> None:
    for target in MARKDOWN_LINK.findall(text):
        target = target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
        candidate = (path.parent / clean).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"link: {path.relative_to(ROOT)} escapes repository: {target}")
            continue
        if not candidate.exists():
            errors.append(f"link: {path.relative_to(ROOT)} -> missing {target}")


def repository_files(root: Path) -> list[Path]:
    """Return files that are tracked or would be added, excluding ignored artifacts."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
    return [path for path in root.rglob("*") if path.is_file() or path.is_symlink()]


def validate_repo(root: Path = ROOT) -> list[str]:
    global ROOT, SKILLS_ROOT, MANIFEST_PATH
    original = (ROOT, SKILLS_ROOT, MANIFEST_PATH)
    ROOT = root.resolve()
    SKILLS_ROOT = ROOT / "skills"
    MANIFEST_PATH = ROOT / "skills-manifest.json"
    errors: list[str] = []
    try:
        for name in sorted(REQUIRED_ROOT_FILES):
            if not (ROOT / name).is_file():
                errors.append(f"root: missing {name}")

        manifest = load_manifest(errors)
        entries = manifest.get("skills", []) if isinstance(manifest, dict) else []
        if not isinstance(entries, list):
            errors.append("manifest: skills must be an array")
            entries = []

        manifest_by_name: dict[str, dict[str, object]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append("manifest: every skill entry must be an object")
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                errors.append("manifest: skill entry missing name")
                continue
            if name in manifest_by_name:
                errors.append(f"manifest: duplicate skill {name}")
            manifest_by_name[name] = entry
            if entry.get("maturity") not in ALLOWED_MATURITY:
                errors.append(f"manifest: {name} has invalid maturity")
            if entry.get("source_status") not in ALLOWED_SOURCE_STATUS:
                errors.append(f"manifest: {name} has invalid source_status")
            if entry.get("install_selector") != name:
                errors.append(f"manifest: {name} install_selector must match name")
            if not entry.get("summary_zh") or not entry.get("license"):
                errors.append(f"manifest: {name} requires summary_zh and license")
            notice = entry.get("third_party_notice")
            if notice and not (ROOT / str(notice)).is_file():
                errors.append(f"manifest: {name} third_party_notice is missing")

        skill_dirs = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
        directory_names = {path.name for path in skill_dirs}
        manifest_names = set(manifest_by_name)
        for missing in sorted(directory_names - manifest_names):
            errors.append(f"manifest: missing directory entry for {missing}")
        for stale in sorted(manifest_names - directory_names):
            errors.append(f"manifest: points to missing directory {stale}")

        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"skill: {skill_dir.name} missing SKILL.md")
                continue
            try:
                metadata = parse_skill_frontmatter_text(skill_md.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"skill: {skill_dir.name} invalid frontmatter: {exc}")
                continue
            if metadata.get("name") != skill_dir.name:
                errors.append(f"skill: {skill_dir.name} frontmatter name mismatch")
            if not metadata.get("description"):
                errors.append(f"skill: {skill_dir.name} missing description")

        total_bytes = 0
        for path in sorted(repository_files(ROOT)):
            relative = path.relative_to(ROOT)
            if path.is_symlink():
                errors.append(f"file: symlink not allowed: {relative}")
                continue
            if any(part in FORBIDDEN_PARTS for part in relative.parts):
                errors.append(f"file: forbidden directory content: {relative}")
            if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                errors.append(f"file: forbidden artifact: {relative}")
            size = path.stat().st_size
            total_bytes += size
            if size > MAX_FILE_BYTES:
                errors.append(f"file: exceeds 5 MB: {relative}")
            if path.suffix.lower() == ".json":
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except Exception as exc:
                    errors.append(f"json: {relative}: {exc}")
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"text: invalid UTF-8: {relative}")
                continue
            if path.resolve() != Path(__file__).resolve():
                for label, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        errors.append(f"secret: {label} pattern in {relative}")
                for label, pattern in LOCAL_PATH_PATTERNS.items():
                    if pattern.search(text):
                        errors.append(f"path: {label} in {relative}")
            if path.suffix.lower() == ".md":
                validate_markdown_links(path, text, errors)

        if total_bytes > MAX_REPOSITORY_BYTES:
            errors.append("repository: public files exceed 30 MB")
    finally:
        ROOT, SKILLS_ROOT, MANIFEST_PATH = original
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a JSON result")
    args = parser.parse_args()
    errors = validate_repo()
    result = {
        "status": "passed" if not errors else "failed",
        "skills": len([p for p in SKILLS_ROOT.iterdir() if p.is_dir()]),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"OK validated {result['skills']} public skills")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
