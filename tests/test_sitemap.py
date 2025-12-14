from __future__ import annotations

from pathlib import Path
from textwrap import dedent
import xml.etree.ElementTree as ET

import pytest

from simplicitypress.core.build import build_site
from simplicitypress.core.config import load_config


def _write_minimal_site(
    tmp_path: Path,
    *,
    sitemap_enabled: bool,
    site_url: str = "",
) -> Path:
    site_root = tmp_path
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()
    (site_root / "static" / "css").mkdir(parents=True)

    site_toml = dedent(
        f"""\
        [site]
        title = "Sitemap Site"
        subtitle = ""
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
        name = ""
        email = ""

        [sitemap]
        enabled = {"true" if sitemap_enabled else "false"}
        output = "sitemap.xml"
        include_tags = true
        include_pages = true
        include_posts = true
        include_index = true
        exclude_paths = []
        """,
    )
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    post_md = dedent(
        """\
        +++
        title = "Example Post"
        date = "2025-01-02"
        slug = "example-post"
        tags = ["Alpha"]
        +++
        Body.
        """,
    )
    (site_root / "content" / "posts" / "post1.md").write_text(post_md, encoding="utf-8")

    page_md = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        +++
        About page body.
        """,
    )
    (site_root / "content" / "pages" / "about.md").write_text(page_md, encoding="utf-8")

    (site_root / "templates" / "base.html").write_text(
        "<!doctype html><html><body>{% block content %}{% endblock %}</body></html>",
        encoding="utf-8",
    )
    (site_root / "templates" / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}Index{% endblock %}",
        encoding="utf-8",
    )
    (site_root / "templates" / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}Post{% endblock %}",
        encoding="utf-8",
    )
    (site_root / "templates" / "page.html").write_text(
        "{% extends 'base.html' %}{% block content %}Page{% endblock %}",
        encoding="utf-8",
    )
    (site_root / "templates" / "tags.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tags{% endblock %}",
        encoding="utf-8",
    )
    (site_root / "templates" / "tag.html").write_text(
        "{% extends 'base.html' %}{% block content %}Tag{% endblock %}",
        encoding="utf-8",
    )
    (site_root / "templates" / "feed.xml").write_text(
        "<rss><channel></channel></rss>",
        encoding="utf-8",
    )

    (site_root / "static" / "css" / "style.css").write_text("body{}", encoding="utf-8")
    return site_root


def test_sitemap_disabled_outputs_nothing(tmp_path: Path) -> None:
    site_root = _write_minimal_site(tmp_path, sitemap_enabled=False)
    config = load_config(site_root)
    build_site(config)

    sitemap_path = site_root / "output" / "sitemap.xml"
    assert not sitemap_path.exists()


def test_sitemap_generated_with_expected_entries(tmp_path: Path) -> None:
    site_root = _write_minimal_site(tmp_path, sitemap_enabled=True, site_url="https://example.com")
    config = load_config(site_root)
    build_site(config)

    sitemap_path = site_root / "output" / "sitemap.xml"
    assert sitemap_path.exists()

    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    assert root.tag == f"{ns}urlset"

    url_elements = root.findall(f"{ns}url")
    locs: list[str] = []
    lastmod_map: dict[str, str | None] = {}
    for url_el in url_elements:
        loc_el = url_el.find(f"{ns}loc")
        assert loc_el is not None
        loc_text = loc_el.text or ""
        locs.append(loc_text)
        lastmod_el = url_el.find(f"{ns}lastmod")
        lastmod_map[loc_text] = lastmod_el.text if lastmod_el is not None else None

    expected_locs = [
        "https://example.com/",
        "https://example.com/about/",
        "https://example.com/posts/example-post/",
        "https://example.com/tags/",
        "https://example.com/tags/alpha/",
    ]
    assert locs == expected_locs
    assert lastmod_map["https://example.com/posts/example-post/"] == "2025-01-02"
    assert lastmod_map["https://example.com/"] is None


def test_sitemap_requires_site_url_when_enabled(tmp_path: Path) -> None:
    site_root = _write_minimal_site(tmp_path, sitemap_enabled=True, site_url="")
    config = load_config(site_root)

    with pytest.raises(ValueError, match="site\\.url"):
        build_site(config)
