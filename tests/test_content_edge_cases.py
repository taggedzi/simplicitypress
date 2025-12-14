# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pytest

from simplicitypress.core.config import load_config
from simplicitypress.core.content import _normalize_tags, discover_content


def _write_basic_site_toml(site_root: Path) -> None:
    cfg = dedent(
        """\
        [site]
        title = "Test Site"
        subtitle = ""
        base_url = ""
        language = "en"
        timezone = "UTC"

        [paths]
        content_dir = "content"
        posts_dir = "content/posts"
        pages_dir = "content/pages"
        templates_dir = "templates"
        static_dir = "static"
        output_dir = "output"

        [build]
        posts_per_page = 10
        include_drafts = false

        [author]
        name = ""
        email = ""
        """,
    )
    (site_root / "site.toml").write_text(cfg, encoding="utf-8")


def test_normalize_tags_various_inputs(tmp_path: Path) -> None:
    """_normalize_tags should handle None, strings, lists, and reject invalid types."""
    dummy_path = tmp_path / "dummy.md"

    assert _normalize_tags(None, source=dummy_path) == []
    assert _normalize_tags("single", source=dummy_path) == ["single"]
    assert _normalize_tags(["a", 1], source=dummy_path) == ["a", "1"]

    with pytest.raises(ValueError):
        _normalize_tags(123, source=dummy_path)


def test_discover_content_missing_post_title_raises(tmp_path: Path) -> None:
    """Posts missing required title should cause discover_content to raise."""
    site_root = tmp_path
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    (site_root / "templates").mkdir()
    (site_root / "static").mkdir()

    _write_basic_site_toml(site_root)

    # Missing title in front matter.
    post_md = dedent(
        """\
        +++
        date = "2025-01-02"
        +++
        Body.
        """,
    )
    (posts_dir / "post1.md").write_text(post_md, encoding="utf-8")

    config = load_config(site_root)

    with pytest.raises(ValueError):
        discover_content(config)


def test_discover_content_invalid_post_date_raises(tmp_path: Path) -> None:
    """Invalid date format in post front matter should raise ValueError."""
    site_root = tmp_path
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    (site_root / "templates").mkdir()
    (site_root / "static").mkdir()

    _write_basic_site_toml(site_root)

    post_md = dedent(
        """\
        +++
        title = "Post 1"
        date = "not-a-date"
        +++
        Body.
        """,
    )
    (posts_dir / "post1.md").write_text(post_md, encoding="utf-8")

    config = load_config(site_root)

    with pytest.raises(ValueError):
        discover_content(config)


def test_discover_content_invalid_page_nav_order_falls_back(tmp_path: Path) -> None:
    """Non-integer nav_order should fall back to default value."""
    site_root = tmp_path
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    (site_root / "templates").mkdir()
    (site_root / "static").mkdir()

    _write_basic_site_toml(site_root)

    page_md = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        show_in_nav = true
        nav_order = "not-an-int"
        +++
        About page.
        """,
    )
    (pages_dir / "about.md").write_text(page_md, encoding="utf-8")

    config = load_config(site_root)

    posts, pages = discover_content(config)

    assert posts == []
    assert len(pages) == 1
    page = pages[0]
    assert page.title == "About"
    assert page.nav_order == 1000

