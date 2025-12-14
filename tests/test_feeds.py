from __future__ import annotations

from pathlib import Path
from textwrap import dedent
import xml.etree.ElementTree as ET

import pytest

from simplicitypress.core.build import build_site
from simplicitypress.core.config import load_config


def _write_site_with_feeds(
    tmp_path: Path,
    *,
    feeds_block: str,
    site_url: str = "https://example.com",
) -> Path:
    site_root = tmp_path
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()
    (site_root / "static" / "css").mkdir(parents=True)

    site_toml = dedent(
        f"""\
        [site]
        title = "Feed Site"
        subtitle = "Feed Subs"
        base_url = ""
        url = "{site_url}"
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
        name = "Author Name"
        email = "author@example.com"

        {feeds_block}
        """,
    )
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    posts_dir = site_root / "content" / "posts"
    posts = [
        {
            "slug": "alpha-post",
            "title": "Alpha Post",
            "date": "2024-05-03T10:00:00",
            "tags": '["alpha"]',
            "summary": "Alpha summary text.",
            "draft": "false",
        },
        {
            "slug": "featured-post",
            "title": "Featured Post",
            "date": "2024-04-20T12:00:00",
            "tags": '["featured", "updates"]',
            "summary": "Featured summary text.",
            "draft": "false",
        },
        {
            "slug": "draft-post",
            "title": "Draft Post",
            "date": "2024-03-15T09:00:00",
            "tags": '["featured"]',
            "summary": "Draft summary text.",
            "draft": "true",
        },
    ]
    for post in posts:
        post_md = dedent(
            f"""\
            +++
            title = "{post['title']}"
            slug = "{post['slug']}"
            date = "{post['date']}"
            tags = {post['tags']}
            summary = "{post['summary']}"
            draft = {post['draft']}
            +++
            Body for {post['title']}.
            """,
        )
        (posts_dir / f"{post['slug']}.md").write_text(post_md, encoding="utf-8")

    pages_dir = site_root / "content" / "pages"
    page_md = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        date = "2024-01-15T00:00:00"
        +++
        About page body.
        """,
    )
    (pages_dir / "about.md").write_text(page_md, encoding="utf-8")

    templates_dir = site_root / "templates"
    base_html = "<!doctype html><html><body>{% block content %}{% endblock %}</body></html>"
    (templates_dir / "base.html").write_text(base_html, encoding="utf-8")
    (templates_dir / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}Index{% endblock %}",
        encoding="utf-8",
    )
    (templates_dir / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}Post{% endblock %}",
        encoding="utf-8",
    )
    (templates_dir / "page.html").write_text(
        "{% extends 'base.html' %}{% block content %}Page{% endblock %}",
        encoding="utf-8",
    )
    (templates_dir / "tags.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tags{% endblock %}",
        encoding="utf-8",
    )
    (templates_dir / "tag.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tag{% endblock %}",
        encoding="utf-8",
    )

    (site_root / "static" / "css" / "style.css").write_text("body{}", encoding="utf-8")
    return site_root


def test_feeds_disabled_outputs_nothing(tmp_path: Path) -> None:
    feeds_block = dedent(
        """\
        [feeds]
        enabled = false
        """,
    )
    site_root = _write_site_with_feeds(tmp_path, feeds_block=feeds_block, site_url="")

    config = load_config(site_root)
    build_site(config)

    assert not (site_root / "output" / "rss.xml").exists()
    assert not (site_root / "output" / "atom.xml").exists()


def test_feeds_require_site_url_when_enabled(tmp_path: Path) -> None:
    feeds_block = dedent(
        """\
        [feeds]
        enabled = true
        """,
    )
    site_root = _write_site_with_feeds(tmp_path, feeds_block=feeds_block, site_url="")
    config = load_config(site_root)

    with pytest.raises(ValueError, match="feeds\\.enabled"):
        build_site(config)


def test_feeds_generate_rss_and_atom(tmp_path: Path) -> None:
    feeds_block = dedent(
        """\
        [feeds]
        enabled = true
        rss_output = "rss.xml"
        atom_output = "atom.xml"
        include_pages = true
        max_items = 5
        [feeds.summary]
        mode = "excerpt"
        max_chars = 120
        """,
    )
    site_root = _write_site_with_feeds(tmp_path, feeds_block=feeds_block)
    config = load_config(site_root)
    build_site(config)

    rss_path = site_root / "output" / "rss.xml"
    atom_path = site_root / "output" / "atom.xml"
    assert rss_path.exists()
    assert atom_path.exists()

    rss_tree = ET.parse(rss_path)
    rss_root = rss_tree.getroot()
    assert rss_root.tag == "rss"
    channel = rss_root.find("channel")
    assert channel is not None
    rss_links = [item.findtext("link") for item in channel.findall("item")]
    assert "https://example.com/posts/alpha-post/" in rss_links
    assert "https://example.com/about/" in rss_links  # page included due to include_pages

    atom_tree = ET.parse(atom_path)
    atom_root = atom_tree.getroot()
    assert atom_root.tag == "{http://www.w3.org/2005/Atom}feed"
    atom_entries = atom_root.findall("{http://www.w3.org/2005/Atom}entry")
    assert atom_entries, "Atom feed should contain entries"
    atom_titles = [
        entry.find("{http://www.w3.org/2005/Atom}title").text
        for entry in atom_entries
        if entry.find("{http://www.w3.org/2005/Atom}title") is not None
    ]
    assert "Featured Post" in atom_titles


def test_feeds_max_items_and_filters_are_deterministic(tmp_path: Path) -> None:
    feeds_block = dedent(
        """\
        [feeds]
        enabled = true
        rss_output = "rss.xml"
        atom_enabled = false
        include_pages = true
        include_tags = ["featured"]
        max_items = 1
        [feeds.summary]
        mode = "text"
        max_chars = 40
        """,
    )
    site_root = _write_site_with_feeds(tmp_path, feeds_block=feeds_block)
    config = load_config(site_root)

    build_site(config)
    rss_path = site_root / "output" / "rss.xml"
    assert rss_path.exists()
    first_pass = rss_path.read_text(encoding="utf-8")

    # Run again to ensure deterministic output.
    build_site(config)
    second_pass = rss_path.read_text(encoding="utf-8")
    assert first_pass == second_pass

    rss_tree = ET.fromstring(first_pass)
    channel = rss_tree.find("channel")
    assert channel is not None
    items = channel.findall("item")
    assert len(items) == 1
    assert items[0].findtext("title") == "Featured Post"
    # Draft post should never appear even though it has the matching tag
    assert all("Draft Post" != item.findtext("title") for item in items)
