from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from simplicitypress.core.build import build_site
from simplicitypress.core.config import load_config
from simplicitypress.core.search_index import SearchSettings, should_drop_token, tokenize_text


def test_tokenize_text_enforces_minimum_length() -> None:
    tokens = tokenize_text("Hello, world! 123 go", min_len=3)
    assert tokens == ["hello", "world", "123"]


def test_df_drop_rules_respected() -> None:
    settings = SearchSettings(
        max_terms_per_doc=10,
        min_token_len=2,
        drop_df_ratio=0.5,
        drop_df_min=0,
        weight_body=1.0,
        weight_title=2.0,
        weight_tags=2.0,
        normalize_by_doc_len=True,
    )
    # Drop when df equals doc_count.
    assert should_drop_token(5, 5, settings) is True
    # Drop when df/doc_count >= ratio (0.5).
    assert should_drop_token(3, 6, settings) is True
    # Keep when df/doc_count < ratio.
    assert should_drop_token(2, 6, settings) is False

    rare_drop = SearchSettings(
        max_terms_per_doc=10,
        min_token_len=2,
        drop_df_ratio=0.9,
        drop_df_min=2,
        weight_body=1.0,
        weight_title=2.0,
        weight_tags=2.0,
        normalize_by_doc_len=True,
    )
    assert should_drop_token(1, 10, rare_drop) is True
    assert should_drop_token(3, 10, rare_drop) is False


def test_search_assets_are_deterministic(tmp_path: Path) -> None:
    site_root = _prepare_search_enabled_site(tmp_path)
    config = load_config(site_root)

    # First build
    build_site(config)
    docs1, terms1 = _read_search_payloads(site_root / "output")

    # Second build to ensure deterministic outputs (ignoring timestamp)
    build_site(config)
    docs2, terms2 = _read_search_payloads(site_root / "output")

    assert docs1["doc_count"] == 3
    assert [doc["title"] for doc in docs1["docs"]] == ["Alpha Post", "Beta Release", "About"]
    assert docs1["docs"][0]["tags"] == ["python", "news"]
    assert docs1["docs"][1]["tags"] == ["python"]
    assert docs1["docs"][2]["tags"] == []
    assert docs1["docs"][0]["date"] == "2025-01-02"
    assert docs1["docs"][2]["date"] is None

    # Confirm search files exist.
    output_dir = site_root / "output"
    assert (output_dir / "assets" / "search" / "search_docs.json").exists()
    assert (output_dir / "assets" / "search" / "search_terms.json").exists()
    assert (output_dir / "assets" / "search" / "search.js").exists()
    assert (output_dir / "search" / "index.html").exists()

    # Verify token postings.
    python_postings = terms1["python"]
    assert python_postings[0][0] == 0  # doc id 0
    assert python_postings[1][0] == 1
    about_postings = terms1["about"]
    assert about_postings[0][0] == 2
    welcoming_postings = terms1["welcoming"]
    assert welcoming_postings[0][0] == 2

    # Deterministic comparison (ignore timestamp).
    docs1_no_ts = {**docs1, "generated_at": None}
    docs2_no_ts = {**docs2, "generated_at": None}
    assert docs1_no_ts == docs2_no_ts
    assert terms1 == terms2


def test_normalization_toggle_affects_scores(tmp_path: Path) -> None:
    norm_root = _prepare_search_enabled_site(tmp_path / "norm", normalize_by_doc_len=True)
    build_site(load_config(norm_root))
    _, terms_norm = _read_search_payloads(norm_root / "output")

    non_norm_root = _prepare_search_enabled_site(tmp_path / "non_norm", normalize_by_doc_len=False)
    build_site(load_config(non_norm_root))
    _, terms_non_norm = _read_search_payloads(non_norm_root / "output")

    python_norm = terms_norm["python"]
    python_non_norm = terms_non_norm["python"]

    assert python_norm[0][0] == 0
    assert python_norm[1][0] == 1
    assert python_norm[0][1] > python_norm[1][1]
    assert python_non_norm[0][1] == python_non_norm[1][1]


def _prepare_search_enabled_site(site_root: Path, *, normalize_by_doc_len: bool = True) -> Path:
    site_root.mkdir(parents=True, exist_ok=True)
    posts_dir = site_root / "content" / "posts"
    pages_dir = site_root / "content" / "pages"
    templates_dir = site_root / "templates"
    static_dir = site_root / "static"

    posts_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    site_toml = dedent(
        """\
        [site]
        title = "Search Test"
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
        posts_per_page = 5
        include_drafts = false

        [author]
        name = ""
        email = ""

        [search]
        enabled = true
        normalize_by_doc_len = %s
        """,
    ) % ("true" if normalize_by_doc_len else "false")
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    _write_search_templates(templates_dir)

    post_one = dedent(
        """\
        +++
        title = "Alpha Post"
        date = "2025-01-02"
        tags = ["python", "news"]
        summary = "Alpha summary body."
        +++
        Alpha body content is short.
        """,
    )
    post_two = dedent(
        """\
        +++
        title = "Beta Release"
        date = "2025-01-01"
        tags = ["python"]
        summary = "Beta summary."
        +++
        Beta body content is considerably longer than the alpha body content.
        It keeps elaborating on details for several sentences so that its token
        count grows significantly in comparison to the shorter alpha post.
        """,
    )
    (posts_dir / "alpha.md").write_text(post_one, encoding="utf-8")
    (posts_dir / "beta.md").write_text(post_two, encoding="utf-8")

    page_about = dedent(
        """\
        +++
        title = "About"
        slug = "about"
        +++
        <p>About SimplicityPress page welcoming everyone with friendly details.</p>
        """,
    )
    (pages_dir / "about.md").write_text(page_about, encoding="utf-8")

    return site_root


def _write_search_templates(templates_dir: Path) -> None:
    base_template = (
        "<!doctype html><html><head><title>{{ site.title }}</title></head>"
        "<body>{% block content %}{% endblock %}</body></html>"
    )
    (templates_dir / "base.html").write_text(base_template, encoding="utf-8")
    for name in ("index", "post", "page", "tags", "tag"):
        (templates_dir / f"{name}.html").write_text(
            "{% extends 'base.html' %}{% block content %}" + name.capitalize() + "{% endblock %}",
            encoding="utf-8",
        )
    (templates_dir / "feed.xml").write_text("<rss></rss>", encoding="utf-8")
    search_template = dedent(
        """\
        {% extends 'base.html' %}
        {% block content %}
        <form id="sp-search-form">
          <input id="sp-search-input" type="search">
        </form>
        <div id="sp-search-results"></div>
        <script>
          window.__SP_SEARCH__ = {
            assetsBase: "{{ search_assets_base }}",
            minTokenLength: {{ search_min_token_len }},
          };
        </script>
        <script src="{{ search_bundle_path }}"></script>
        {% endblock %}
        """,
    )
    (templates_dir / "search.html").write_text(search_template, encoding="utf-8")


def _read_search_payloads(output_dir: Path) -> tuple[dict, dict]:
    docs_data = json.loads((output_dir / "assets" / "search" / "search_docs.json").read_text(encoding="utf-8"))
    terms_data = json.loads((output_dir / "assets" / "search" / "search_terms.json").read_text(encoding="utf-8"))
    return docs_data, terms_data
