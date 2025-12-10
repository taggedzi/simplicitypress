from __future__ import annotations

from pathlib import Path

import pytest

from simplicitypress.api import serve_site
from simplicitypress.core.config import load_config


def _write_basic_site_toml(site_root: Path) -> None:
    site_toml = """\
[site]
title = "Test Site"

[paths]
content_dir = "content"
posts_dir = "content/posts"
pages_dir = "content/pages"
templates_dir = "templates"
static_dir = "static"
output_dir = "output"
"""
    (site_root / "site.toml").write_text(site_toml, encoding="utf-8")


def test_serve_site_raises_if_output_missing_and_no_build(tmp_path: Path) -> None:
    """
    serve_site should raise FileNotFoundError if the configured output
    directory does not exist and build_first=False.
    """
    site_root = tmp_path

    # Minimal config and required directories so load_config succeeds.
    (site_root / "content" / "posts").mkdir(parents=True, exist_ok=True)
    (site_root / "content" / "pages").mkdir(parents=True, exist_ok=True)
    (site_root / "templates").mkdir()
    (site_root / "static").mkdir()
    _write_basic_site_toml(site_root)

    # Point serve_site at an output directory that does not exist and
    # skip the build step so the check for existence fails before
    # any HTTP server is started.
    missing_output = tmp_path / "nonexistent-output"

    with pytest.raises(FileNotFoundError):
        serve_site(site_root=site_root, output_dir=missing_output, build_first=False)
