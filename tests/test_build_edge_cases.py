# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from simplicitypress.core.build import build_site
from simplicitypress.core.config import load_config


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
        posts_per_page = 2
        include_drafts = false

        [author]
        name = ""
        email = ""

        [search]
        enabled = false
        output_dir = "assets/search"
        page_path = "search/index.html"
        max_terms_per_doc = 300
        min_token_len = 2
        drop_df_ratio = 0.70
        drop_df_min = 0
        weight_body = 1.0
        weight_title = 8.0
        weight_tags = 6.0
        normalize_by_doc_len = true
        """,
    )
    (site_root / "site.toml").write_text(cfg, encoding="utf-8")


def _write_minimal_templates(site_root: Path) -> None:
    templates = site_root / "templates"
    templates.mkdir(parents=True, exist_ok=True)

    (templates / "base.html").write_text(
        "<!doctype html><html><body>{% block content %}{% endblock %}</body></html>",
        encoding="utf-8",
    )
    (templates / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}Index{% endblock %}",
        encoding="utf-8",
    )
    (templates / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}Post{% endblock %}",
        encoding="utf-8",
    )
    (templates / "page.html").write_text(
        "{% extends 'base.html' %}{% block content %}Page{% endblock %}",
        encoding="utf-8",
    )
    (templates / "tags.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tags{% endblock %}",
        encoding="utf-8",
    )
    (templates / "tag.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tag{% endblock %}",
        encoding="utf-8",
    )
    (templates / "search.html").write_text(
        "{% extends 'base.html' %}{% block content %}Search{% endblock %}",
        encoding="utf-8",
    )


def _prepare_empty_site(tmp_path: Path) -> Path:
    site_root = tmp_path
    (site_root / "content" / "posts").mkdir(parents=True, exist_ok=True)
    (site_root / "content" / "pages").mkdir(parents=True, exist_ok=True)
    (site_root / "static").mkdir(parents=True, exist_ok=True)
    _write_basic_site_toml(site_root)
    _write_minimal_templates(site_root)
    return site_root


def _prepare_site_with_tagged_posts(tmp_path: Path) -> Path:
    site_root = tmp_path
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    (site_root / "static").mkdir(parents=True, exist_ok=True)
    _write_basic_site_toml(site_root)
    _write_minimal_templates(site_root)

    # Two posts sharing a tag, plus another tag with spaces and punctuation.
    post1 = dedent(
        """\
        +++
        title = "Post 1"
        date = "2025-01-02"
        tags = ["shared", "Python"]
        +++
        Body 1.
        """,
    )
    (posts_dir / "post1.md").write_text(post1, encoding="utf-8")

    post2 = dedent(
        """\
        +++
        title = "Post 2"
        date = "2025-01-03"
        tags = ["shared", "Python dev!"]
        +++
        Body 2.
        """,
    )
    (posts_dir / "post2.md").write_text(post2, encoding="utf-8")

    # One page so that nav_items is non-empty.
    page_md = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        show_in_nav = true
        nav_order = 5
        +++
        About page.
        """,
    )
    (pages_dir / "about.md").write_text(page_md, encoding="utf-8")

    return site_root


def _prepare_site_with_invalid_post_frontmatter(tmp_path: Path) -> Path:
    site_root = tmp_path
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    (site_root / "static").mkdir(parents=True, exist_ok=True)
    _write_basic_site_toml(site_root)
    _write_minimal_templates(site_root)

    # Missing required date field.
    bad_post = dedent(
        """\
        +++
        title = "Bad Post"
        +++
        No date here.
        """,
    )
    (posts_dir / "bad.md").write_text(bad_post, encoding="utf-8")

    return site_root


def test_build_site_with_empty_content_succeeds(tmp_path: Path) -> None:
    """build_site should succeed when there are no posts or pages."""
    site_root = _prepare_empty_site(tmp_path)
    config = load_config(site_root)

    build_site(config)

    output = site_root / "output"
    # Home page and tags index should exist even with no content.
    assert (output / "index.html").exists()
    assert (output / "tags" / "index.html").exists()


def test_build_site_generates_tag_pages_for_shared_tags(tmp_path: Path) -> None:
    """build_site should generate tag index and per-tag pages based on tags."""
    site_root = _prepare_site_with_tagged_posts(tmp_path)
    config = load_config(site_root)

    build_site(config)

    output = site_root / "output"
    # Tags index.
    assert (output / "tags" / "index.html").exists()

    # Slugified tag names: "Python dev!" -> "python-dev"
    shared_slug = "shared"
    python_slug = "python"
    python_dev_slug = "python-dev"

    assert (output / "tags" / shared_slug / "index.html").exists()
    assert (output / "tags" / python_slug / "index.html").exists()
    assert (output / "tags" / python_dev_slug / "index.html").exists()


def test_build_site_propagates_invalid_frontmatter_errors(tmp_path: Path) -> None:
    """Invalid post frontmatter should cause build_site to fail with ValueError."""
    site_root = _prepare_site_with_invalid_post_frontmatter(tmp_path)
    config = load_config(site_root)

    with pytest.raises(ValueError):
        build_site(config)


def test_build_site_skips_search_assets_when_disabled(tmp_path: Path) -> None:
    """Search assets should not exist in the output unless search is enabled."""
    site_root = _prepare_empty_site(tmp_path)
    config = load_config(site_root)

    assert config.search.get("enabled") is False

    build_site(config)

    output = site_root / "output"
    assert not (output / "assets" / "search").exists()
    assert not (output / "search" / "index.html").exists()


def test_navigation_link_includes_search_only_when_enabled(tmp_path: Path) -> None:
    """Navigation items should include a Search link only when search is enabled."""
    site_root = _prepare_empty_site(tmp_path)
    templates = site_root / "templates"
    (templates / "base.html").write_text(
        "<!doctype html><html><body>"
        "<nav>{% for item in nav_items %}<span>{{ item.title }}|{{ item.url }}</span>{% endfor %}</nav>"
        "{% block content %}{% endblock %}"
        "</body></html>",
        encoding="utf-8",
    )
    config = load_config(site_root)

    build_site(config)
    index_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    assert "Search|" not in index_html

    config.search["enabled"] = True
    build_site(config)
    index_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    assert "Search|/search/" in index_html

