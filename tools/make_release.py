#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
"""
make_release.py

Helper script for cutting a new SimplicityPress release.

Usage:
    python tools/make_release.py 0.5.0

What it does:
  1. Checks that git working tree is clean.
  2. Updates [project].version in pyproject.toml.
  3. Commits the change: "Release v0.5.0".
  4. Creates an annotated git tag: v0.5.0.
  5. Prints the `git push` commands you should run next.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"


def die(msg: str) -> NoReturn:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run(
    cmd: list[str],
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    print(f"+ {' '.join(cmd)}")
    kwargs: dict[str, object] = {"check": check, "text": True}
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    return subprocess.run(cmd, **kwargs)  # type: ignore[arg-type]


def ensure_clean_git() -> None:
    """Abort if there are uncommitted changes."""
    result = run(["git", "status", "--porcelain"], check=False, capture_output=True)
    if result.stdout.strip():
        die(
            "Git working tree is not clean.\n"
            "Commit or stash your changes before running tools/make_release.py."
        )


def update_version_in_pyproject(new_version: str) -> str:
    """
    Replace the [project] version string in pyproject.toml.

    This assumes a line like:
        version = "0.4.0"
    in the [project] table.
    """
    if not PYPROJECT.exists():
        die(f"pyproject.toml not found at {PYPROJECT}")

    text = PYPROJECT.read_text(encoding="utf-8")

    # Simple sanity check: make sure there's a [project] table
    if "[project]" not in text:
        die("Could not find [project] table in pyproject.toml.")

    # Replace the first version = "..."
    pattern = r'(?m)^(version\s*=\s*")([^"]+)(")'
    match = re.search(pattern, text)
    if not match:
        die('Could not find a `version = "...` line in pyproject.toml.')

    old_version = match.group(2)
    if old_version == new_version:
        die(f"pyproject.toml already has version {new_version!r}.")

    def _repl(match: "re.Match[str]") -> str:
        return f'{match.group(1)}{new_version}{match.group(3)}'

    new_text = re.sub(pattern, _repl, text, count=1)
    PYPROJECT.write_text(new_text, encoding="utf-8")

    print(f"Updated version: {old_version} → {new_version}")
    return old_version


def ensure_git_cliff() -> None:
    if shutil.which("git-cliff") is None:
        die(
            "git-cliff is required but was not found in PATH.\n"
            "Install it via `pip install git-cliff` or see docs/release.md."
        )


def generate_changelog(version: str) -> None:
    ensure_git_cliff()
    tag = f"v{version}"
    cmd = [
        "git",
        "cliff",
        "--tag",
        tag,
        "--output",
        str(CHANGELOG),
    ]
    run(cmd)


def git_commit_and_tag(version: str) -> None:
    """Create a commit and an annotated tag for the new version."""
    # Stage updated files
    run(["git", "add", str(PYPROJECT), str(CHANGELOG)])

    # Commit
    msg = f"chore(release): update changelog for v{version}"
    run(["git", "commit", "-m", msg])

    # Tag
    tag = f"v{version}"
    run(["git", "tag", "-a", tag, "-m", f"Release {tag}"])

    print()
    print(f"Created tag {tag}.")
    print("Next steps:")
    print("  git push")
    print("  git push --tags")


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        print("Usage: python tools/make_release.py <version>", file=sys.stderr)
        sys.exit(1)

    new_version = argv[1].strip()

    # Very light sanity check: X.Y or X.Y.Z
    if not re.match(r"^\d+\.\d+(\.\d+)?$", new_version):
        die(f"Version {new_version!r} does not look like X.Y or X.Y.Z")

    ensure_clean_git()
    update_version_in_pyproject(new_version)
    generate_changelog(new_version)
    git_commit_and_tag(new_version)


if __name__ == "__main__":
    main(sys.argv)
