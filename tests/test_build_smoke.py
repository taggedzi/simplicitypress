# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from textwrap import dedent

from simplicitypress.core.build import build_site
from simplicitypress.core.config import load_config


def _basic_site(tmp_path: Path) -> Path:
    site_root = tmp_path
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()
    (site_root / "static" / "css").mkdir(parents=True)

    # Minimal site.toml
    site_toml = dedent(
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
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    # One post
    post_md = dedent(
        """\
        +++
        title = "Post 1"
        date = "2025-01-02"
        +++
        Body of post 1.
        """,
    )
    (site_root / "content" / "posts" / "post1.md").write_text(post_md, encoding="utf-8")

    # Minimal templates (just enough for build_site to succeed)
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
    # Minimal CSS
    (site_root / "static" / "css" / "style.css").write_text("body{}", encoding="utf-8")

    return site_root


def test_build_smoke(tmp_path: Path) -> None:
    site_root = _basic_site(tmp_path)
    config = load_config(site_root)
    build_site(config)

    output = site_root / "output"
    assert (output / "index.html").exists()
    assert (output / "posts" / "post1" / "index.html").exists()
    assert (output / "tags" / "index.html").exists()
    assert (output / "static" / "css" / "style.css").exists()
