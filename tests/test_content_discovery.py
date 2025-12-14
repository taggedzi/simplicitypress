# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from datetime import datetime
from pathlib import Path
from textwrap import dedent

from simplicitypress.core.config import load_config
from simplicitypress.core.content import discover_content


def _write_site_toml(site_root: Path) -> None:
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


def test_discover_content_basic(tmp_path: Path) -> None:
    site_root = tmp_path
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()
    (site_root / "static").mkdir()

    _write_site_toml(site_root)

    post_md = dedent(
        """\
        +++
        title = "Post 1"
        date = "2025-01-02"
        tags = ["test"]
        +++
        Body of post 1.
        """,
    )
    (site_root / "content" / "posts" / "post1.md").write_text(post_md, encoding="utf-8")

    page_md = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        show_in_nav = true
        nav_order = 10
        +++
        About page.
        """,
    )
    (site_root / "content" / "pages" / "about.md").write_text(page_md, encoding="utf-8")

    config = load_config(site_root)
    posts, pages = discover_content(config)

    assert len(posts) == 1
    post = posts[0]
    assert post.title == "Post 1"
    assert post.tags == ["test"]
    assert isinstance(post.date, datetime)

    assert len(pages) == 1
    page = pages[0]
    assert page.title == "About"
    assert page.slug == "about"
    assert page.show_in_nav is True
    assert page.nav_order == 10

