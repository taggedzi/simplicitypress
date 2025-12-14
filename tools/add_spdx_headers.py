#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

SPDX_LICENSE_LINE = "# SPDX-License-Identifier: MIT"
ENCODING_RE = re.compile(r"^#.*coding[:=]\s*([-_.a-zA-Z0-9]+)")
LICENSE_LINE_RE = re.compile(r"^#\s*SPDX-License-Identifier:\s*(.+)$", re.MULTILINE)
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".venv",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "LICENSES",
    "static",
    "templates",
}


@dataclass
class SPDXStats:
    added: int = 0
    already_present: int = 0
    conflicts: int = 0
    missing: int = 0


def apply_spdx_to_text(text: str, year: int, holder: str) -> tuple[str, bool, bool]:
    """Apply SPDX header comments to text if missing."""
    newline = _detect_newline(text)

    existing_license = _find_existing_license(text)
    if existing_license is not None:
        if existing_license == "MIT":
            return text, False, False
        return text, False, True

    lines = text.splitlines(keepends=True)
    insert_at = _find_insert_index(lines)
    header_lines = [
        f"# SPDX-FileCopyrightText: {year} {holder}{newline}",
        f"{SPDX_LICENSE_LINE}{newline}",
    ]
    new_content = "".join(lines[:insert_at] + header_lines + lines[insert_at:])
    return new_content, True, False


def _detect_newline(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def _find_insert_index(lines: list[str]) -> int:
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1

    for i in range(min(len(lines), 2)):
        if ENCODING_RE.search(lines[i]):
            insert_at = max(insert_at, i + 1)

    return insert_at


def _find_existing_license(text: str) -> str | None:
    match = LICENSE_LINE_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def _should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    for part in rel_parts:
        if part in EXCLUDED_PARTS:
            return True
        if part.endswith(".egg-info"):
            return True
    return False


def gather_target_files(root: Path) -> list[Path]:
    targets: list[Path] = []
    include_roots: list[tuple[Path, bool]] = [
        (root / "src" / "simplicitypress", True),
        (root / "tests", True),
        (root / "tools", False),
    ]
    for base, recursive in include_roots:
        if not base.exists():
            continue
        iterator: Iterable[Path]
        if recursive:
            iterator = base.rglob("*.py")
        else:
            iterator = base.glob("*.py")
        for path in iterator:
            if not path.is_file():
                continue
            if _should_skip(path, root):
                continue
            targets.append(path)

    nox_file = root / "noxfile.py"
    if nox_file.exists():
        targets.append(nox_file)

    return sorted(targets, key=lambda p: p.relative_to(root).as_posix())


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(content)


def process_files(
    paths: Iterable[Path],
    *,
    fix: bool,
    holder: str,
    year: int,
) -> SPDXStats:
    stats = SPDXStats()
    for path in paths:
        text = _read_text(path)
        new_text, added, conflict = apply_spdx_to_text(text, year, holder)

        if conflict:
            stats.conflicts += 1
            continue

        if added:
            stats.missing += 1
            if fix:
                if new_text != text:
                    _write_text(path, new_text)
                stats.added += 1
            continue

        stats.already_present += 1

    return stats


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure SimplicityPress Python files have SPDX headers.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Verify SPDX headers only.")
    mode.add_argument("--fix", action="store_true", help="Add SPDX headers to files.")
    parser.add_argument(
        "--copyright-holder",
        default="SimplicityPress contributors",
        help="Override the SPDX copyright holder text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    year = dt.datetime.now(dt.UTC).year
    target_files = gather_target_files(root)
    stats = process_files(
        target_files,
        fix=args.fix,
        holder=args.copyright_holder,
        year=year,
    )

    print(f"Added: {stats.added}")
    print(f"Already present: {stats.already_present}")
    print(f"Conflicts: {stats.conflicts}")
    print(f"Missing (check mode): {stats.missing}")

    exit_code = 0
    if stats.conflicts:
        exit_code = 1
    if args.check and stats.missing:
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
