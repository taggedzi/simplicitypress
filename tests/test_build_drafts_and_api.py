from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from simplicitypress.api import build_site_api
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
        posts_per_page = 10
        include_drafts = false

        [author]
        name = ""
        email = ""
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


def _write_site_with_draft_content(site_root: Path) -> None:
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Published post
    post_md = dedent(
        """\
        +++
        title = "Published Post"
        date = "2025-01-02"
        slug = "published"
        +++
        Body of published post.
        """,
    )
    (posts_dir / "published.md").write_text(post_md, encoding="utf-8")

    # Draft post
    draft_md = dedent(
        """\
        +++
        title = "Draft Post"
        date = "2025-01-03"
        slug = "draft-post"
        draft = true
        +++
        Body of draft post.
        """,
    )
    (posts_dir / "draft.md").write_text(draft_md, encoding="utf-8")

    # One page to exercise nav items.
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
    (pages_dir / "about.md").write_text(page_md, encoding="utf-8")


def _write_static(site_root: Path) -> None:
    static_dir = site_root / "static" / "css"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "style.css").write_text("body{}", encoding="utf-8")


def _prepare_site_root(tmp_path: Path) -> Path:
    site_root = tmp_path
    site_root.mkdir(parents=True, exist_ok=True)
    _write_basic_site_toml(site_root)
    _write_minimal_templates(site_root)
    _write_site_with_draft_content(site_root)
    _write_static(site_root)
    return site_root


def test_build_site_excludes_drafts_by_default(tmp_path: Path) -> None:
    """
    Core build_site should exclude draft posts when include_drafts is false.
    """
    site_root = _prepare_site_root(tmp_path)
    config = load_config(site_root)

    # include_drafts is false in the config written above
    build_site(config)

    output = site_root / "output"
    assert (output / "posts" / "published" / "index.html").exists()
    assert not (output / "posts" / "draft-post" / "index.html").exists()


def test_build_site_api_respects_output_dir_and_include_drafts(tmp_path: Path) -> None:
    """
    build_site_api should honor output_dir override and include_drafts flag.
    """
    site_root = _prepare_site_root(tmp_path / "site")
    override_output = tmp_path / "custom-output"

    build_site_api(
        site_root=site_root,
        output_dir=override_output,
        include_drafts=True,
    )

    # Output is written to the overridden directory.
    assert (override_output / "index.html").exists()
    # Draft post should now be rendered when include_drafts=True.
    assert (override_output / "posts" / "draft-post" / "index.html").exists()
