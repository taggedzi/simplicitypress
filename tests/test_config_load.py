from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from simplicitypress.core.config import load_config


def test_load_config_missing_site_toml(tmp_path: Path) -> None:
    """load_config should fail clearly when site.toml is missing."""
    site_root = tmp_path

    with pytest.raises(FileNotFoundError):
        load_config(site_root)


def test_load_config_invalid_toml_raises(tmp_path: Path) -> None:
    """Invalid/malformed site.toml should surface a TOML parse error."""
    site_root = tmp_path

    # Required directories so load_config reaches TOML parsing.
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()

    bad_toml = dedent(
        """\
        [site]
        title = "Broken"

        [paths]
        content_dir = "content"

        [build]
        posts_per_page = 10

        # malformed list value
        invalid = [1,,2]
        """,
    )
    (site_root / "site.toml").write_text(bad_toml, encoding="utf-8")

    with pytest.raises(Exception):
        # Exact exception type is tomllib.TOMLDecodeError on supported runtimes.
        load_config(site_root)


def test_load_config_creates_static_and_output_dirs(tmp_path: Path) -> None:
    """Static and output directories are created if missing."""
    site_root = tmp_path

    # Required content/template dirs exist.
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()

    # Intentionally do NOT create static/ or output/ so load_config must create them.
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

    config = load_config(site_root)

    assert config.paths.static_dir.is_dir()
    assert config.paths.output_dir.is_dir()
    assert config.paths.static_dir == (site_root / "static").resolve()
    assert config.paths.output_dir == (site_root / "output").resolve()


def test_load_config_missing_required_directories(tmp_path: Path) -> None:
    """Missing required content/templates directories should raise FileNotFoundError."""
    site_root = tmp_path

    # Only write site.toml; do not create content/posts, content/pages, or templates.
    site_toml = dedent(
        """\
        [site]
        title = "Test Site"

        [paths]
        content_dir = "content"
        posts_dir = "content/posts"
        pages_dir = "content/pages"
        templates_dir = "templates"
        static_dir = "static"
        output_dir = "output"
        """,
    )
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        load_config(site_root)


def test_load_config_preserves_existing_output_directory(tmp_path: Path) -> None:
    """Existing output directory with files should not be wiped by load_config."""
    site_root = tmp_path

    # Required directories present.
    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()

    # Pre-create output directory with a marker file.
    output_dir = site_root / "output"
    output_dir.mkdir(parents=True)
    marker = output_dir / "marker.txt"
    marker.write_text("keep-me", encoding="utf-8")

    site_toml = dedent(
        """\
        [site]
        title = "Test Site"

        [paths]
        content_dir = "content"
        posts_dir = "content/posts"
        pages_dir = "content/pages"
        templates_dir = "templates"
        static_dir = "static"
        output_dir = "output"
        """,
    )
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    config = load_config(site_root)

    assert config.paths.output_dir.is_dir()
    assert (config.paths.output_dir / "marker.txt").read_text(encoding="utf-8") == "keep-me"


def test_load_config_populates_search_defaults(tmp_path: Path) -> None:
    """Search configuration defaults should be merged automatically."""
    site_root = tmp_path

    (site_root / "content" / "posts").mkdir(parents=True)
    (site_root / "content" / "pages").mkdir(parents=True)
    (site_root / "templates").mkdir()

    site_toml = dedent(
        """\
        [site]
        title = "Test Site"

        [paths]
        content_dir = "content"
        posts_dir = "content/posts"
        pages_dir = "content/pages"
        templates_dir = "templates"
        static_dir = "static"
        output_dir = "output"
        """,
    )
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")

    config = load_config(site_root)

    assert config.search["enabled"] is False
    assert config.search["output_dir"] == "assets/search"
    assert config.search["page_path"] == "search/index.html"
