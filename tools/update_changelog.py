#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
"""Deterministic changelog generator based on git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import difflib

SECTION_ORDER = ["Features", "Fixes", "Documentation", "Maintenance", "Other"]
TYPE_TO_SECTION = {
    "feat": "Features",
    "fix": "Fixes",
    "bug": "Fixes",
    "docs": "Documentation",
    "chore": "Maintenance",
    "ci": "Maintenance",
    "refactor": "Maintenance",
    "test": "Maintenance",
    "build": "Maintenance",
    "perf": "Maintenance",
}
INTRO_LINES = [
    "# Changelog",
    "",
    "This file is generated from git history via tools/update_changelog.py.",
    "Releases before v0.2.0 predate that workflow, so earlier sections may not list every historical commit.",
    "",
]


@dataclass
class Commit:
    short_hash: str
    subject: str
    section: str


@dataclass
class RenderInfo:
    latest_tag: str | None
    unreleased_range: str | None
    unreleased_commits: int


def run_git(*args: str) -> str:
    """Run git and return stdout (stripped)."""
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def list_version_tags() -> List[str]:
    output = run_git("tag", "--list", "v*", "--sort=-version:refname")
    return [line.strip() for line in output.splitlines() if line.strip()]


def get_tag_date(tag: str) -> str:
    return run_git("log", "-1", "--date=short", "--pretty=%ad", tag)


def should_skip_subject(subject: str) -> bool:
    lowered = subject.lower()
    if lowered.startswith("merge "):
        return True
    if lowered.startswith("chore(release):"):
        return True
    if "update changelog" in lowered:
        return True
    if "changelog" in lowered:
        return True
    return False


def categorize_subject(subject: str) -> str:
    lowered = subject.lower()
    if ":" in lowered:
        prefix = lowered.split(":", 1)[0]
        if prefix.endswith("!"):
            prefix = prefix[:-1]
        if "(" in prefix:
            prefix = prefix.split("(", 1)[0]
        if prefix in TYPE_TO_SECTION:
            return TYPE_TO_SECTION[prefix]
    for prefix, section in TYPE_TO_SECTION.items():
        if lowered.startswith(f"{prefix} "):
            return section
    return "Other"


def parse_commit_line(line: str) -> Commit | None:
    if not line:
        return None
    try:
        short_hash, subject = line.split("\t", 1)
    except ValueError:
        return None
    subject = subject.strip()
    if not subject or should_skip_subject(subject):
        return None
    section = categorize_subject(subject)
    return Commit(short_hash=short_hash, subject=subject, section=section)


def gather_commits(range_spec: str | None) -> List[Commit]:
    args = ["log", "--pretty=format:%h%x09%s", "--no-merges"]
    if range_spec:
        args.append(range_spec)
    output = run_git(*args)
    commits: List[Commit] = []
    for line in output.splitlines():
        commit = parse_commit_line(line)
        if commit:
            commits.append(commit)
    return commits


def group_commits(commits: Iterable[Commit]) -> dict[str, List[Commit]]:
    grouped: dict[str, List[Commit]] = {name: [] for name in SECTION_ORDER}
    for commit in commits:
        grouped.setdefault(commit.section, []).append(commit)
    return grouped


def format_section(title: str, commits: List[Commit]) -> List[str]:
    lines: List[str] = [f"## {title}", ""]
    if not commits:
        lines.append("_No notable changes._")
        lines.append("")
        return lines

    grouped = group_commits(commits)
    for section_name in SECTION_ORDER:
        section_commits = grouped.get(section_name) or []
        if not section_commits:
            continue
        lines.append(f"### {section_name}")
        lines.append("")
        for commit in section_commits:
            lines.append(f"- {commit.subject} ({commit.short_hash})")
        lines.append("")
    return lines


def build_release_sections(tags: List[str]) -> List[List[str]]:
    sections: List[List[str]] = []
    for idx, tag in enumerate(tags):
        older = tags[idx + 1] if idx + 1 < len(tags) else None
        range_spec = f"{older}..{tag}" if older else tag
        commits = gather_commits(range_spec)
        date_str = get_tag_date(tag)
        sections.append(format_section(f"{tag} - {date_str}", commits))
    return sections


def build_unreleased_section(
    base_ref: str | None,
    include: bool,
) -> tuple[List[str], str | None, int]:
    if not include:
        return ([], None, 0)
    range_spec = f"{base_ref}..HEAD" if base_ref else None
    commits = gather_commits(range_spec)
    descriptor = range_spec or "<root>..HEAD"
    return format_section("Unreleased", commits), descriptor, len(commits)


def render_changelog(
    include_unreleased: bool = True,
    version_override: str | None = None,
    since_ref: str | None = None,
) -> tuple[str, RenderInfo]:
    tags = list_version_tags()
    release_sections: List[List[str]] = []
    latest_ref = since_ref or (tags[0] if tags else None)

    if version_override and version_override not in tags:
        base = since_ref or (tags[0] if tags else None)
        range_spec = f"{base}..HEAD" if base else None
        commits = gather_commits(range_spec)
        today = dt.date.today().isoformat()
        release_sections.append(format_section(f"{version_override} - {today}", commits))
        latest_ref = "HEAD"
    elif version_override:
        start_idx = tags.index(version_override)
        tags = tags[: start_idx + 1]

    lines: List[str] = INTRO_LINES.copy()
    unreleased_lines, range_desc, range_count = build_unreleased_section(
        latest_ref,
        include_unreleased,
    )
    lines.extend(unreleased_lines)
    if lines and lines[-1] != "":
        lines.append("")
    release_sections.extend(build_release_sections(tags))
    for section in release_sections:
        lines.extend(section)
    content = "\n".join(lines).rstrip("\n") + "\n"
    info = RenderInfo(
        latest_tag=latest_ref,
        unreleased_range=range_desc,
        unreleased_commits=range_count,
    )
    return content.replace("\r\n", "\n"), info


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize “weird spaces” so changelog output is stable across platforms/editors.
    normalized = normalized.replace("\u202f", " ")  # narrow no-break space
    normalized = normalized.replace("\u00a0", " ")  # no-break space (optional but helpful)
    # Handle historical mojibake where U+202F narrow no-break space became 'â€¯'
    normalized = normalized.replace("â€¯", " ")
    return normalized.rstrip("\n") + "\n"


def write_changelog(content: str, path: Path) -> None:
    normalized = normalize_text(content)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(normalized, encoding="utf-8", newline="\n")
    tmp_path.replace(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update SimplicityPress changelog.")
    parser.add_argument("--update", action="store_true", help="Rewrite CHANGELOG.md")
    parser.add_argument("--check", action="store_true", help="Check if changelog is up to date")
    parser.add_argument("--version", help="Regenerate up to a specific version/tag")
    parser.add_argument(
        "--since",
        help="Override the reference used for the Unreleased section base",
    )
    parser.add_argument(
        "--include-unreleased",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Include the Unreleased section (default: true)",
    )
    parser.add_argument(
        "--output-file",
        default="CHANGELOG.md",
        help="Override the changelog path (default: CHANGELOG.md)",
    )
    args = parser.parse_args(argv)
    if not args.update and not args.check:
        parser.error("One of --update or --check must be provided.")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_path = Path(args.output_file)
    content, info = render_changelog(
        include_unreleased=args.include_unreleased,
        version_override=args.version,
        since_ref=args.since,
    )
    normalized_content = normalize_text(content)
    if args.check:
        existing = ""
        if output_path.exists():
            existing = normalize_text(output_path.read_text(encoding="utf-8"))
        latest = info.latest_tag or "<none>"
        rng = info.unreleased_range or "<unreleased disabled>"
        print(f"[changelog] latest tag: {latest}")
        print(f"[changelog] unreleased range: {rng}")
        print(f"[changelog] unreleased commits: {info.unreleased_commits}")
        if existing != normalized_content:
            print("[changelog] Detected differences, showing unified diff (first 200 lines):")
            diff = list(
                difflib.unified_diff(
                    existing.splitlines(keepends=True),
                    normalized_content.splitlines(keepends=True),
                    fromfile="CHANGELOG.md (current)",
                    tofile="CHANGELOG.md (expected)",
                )
            )
            max_lines = 200
            for line in diff[:max_lines]:
                print(line, end="")
            if len(diff) > max_lines:
                print(f"... (diff truncated, {len(diff) - max_lines} more lines)")
            return 1
    if args.update:
        write_changelog(normalized_content, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
