# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from simplicitypress.core.fs import copy_static_tree, ensure_directory


def test_ensure_directory_creates_parents(tmp_path: Path) -> None:
    """ensure_directory should create the directory and its parents."""
    target = tmp_path / "nested" / "dir"
    assert not target.exists()

    ensure_directory(target)

    assert target.is_dir()


def test_copy_static_tree_missing_source_no_changes(tmp_path: Path) -> None:
    """copy_static_tree should be a no-op if static_dir does not exist."""
    static_dir = tmp_path / "static"
    output_static_dir = tmp_path / "output_static"
    output_static_dir.mkdir()
    marker = output_static_dir / "existing.txt"
    marker.write_text("keep", encoding="utf-8")

    copy_static_tree(static_dir, output_static_dir)

    # Output directory and its contents are untouched.
    assert output_static_dir.is_dir()
    assert marker.read_text(encoding="utf-8") == "keep"


def test_copy_static_tree_replaces_existing_output_tree(tmp_path: Path) -> None:
    """copy_static_tree should replace any existing output_static_dir tree."""
    static_dir = tmp_path / "static"
    output_static_dir = tmp_path / "output_static"

    # Source static files.
    (static_dir / "css").mkdir(parents=True)
    (static_dir / "css" / "style.css").write_text("body{}", encoding="utf-8")

    # Existing output tree with stale content.
    (output_static_dir / "old").mkdir(parents=True)
    (output_static_dir / "old" / "old.txt").write_text("old", encoding="utf-8")

    copy_static_tree(static_dir, output_static_dir)

    # Old content removed; new static tree copied.
    assert not (output_static_dir / "old" / "old.txt").exists()
    assert (output_static_dir / "css" / "style.css").read_text(encoding="utf-8") == "body{}"

