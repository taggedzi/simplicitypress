# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from textwrap import dedent

import pytest

from simplicitypress.core.frontmatter import parse_front_matter_and_body


def test_frontmatter_with_toml(tmp_path: Path) -> None:
    content = dedent(
        """\
        +++
        title = "Hello"
        tags = ["a", "b"]
        +++
        This is the body.

        Second line.
        """,
    )
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    meta, body = parse_front_matter_and_body(path)

    assert meta["title"] == "Hello"
    assert meta["tags"] == ["a", "b"]
    assert "This is the body." in body
    assert "Second line." in body


def test_frontmatter_without_toml(tmp_path: Path) -> None:
    content = "Just some markdown.\nNo front matter here."
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    meta, body = parse_front_matter_and_body(path)

    assert meta == {}
    assert body.startswith("Just some markdown")


def test_frontmatter_missing_closing_fence_treated_as_body(tmp_path: Path) -> None:
    """If closing +++ is missing, treat whole file as body with empty metadata."""
    content = dedent(
        """\
        +++
        title = "Hello"
        This is not valid TOML and there is no closing fence.
        """,
    )
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    meta, body = parse_front_matter_and_body(path)

    assert meta == {}
    assert "This is not valid TOML" in body


def test_frontmatter_malformed_toml_raises(tmp_path: Path) -> None:
    """Malformed TOML inside front matter should raise ValueError."""
    content = dedent(
        """\
        +++
        title = "Hello"
        invalid = [1,,2]
        +++
        Body.
        """,
    )
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        parse_front_matter_and_body(path)
