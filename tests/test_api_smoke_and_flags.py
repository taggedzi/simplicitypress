# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from simplicitypress.api import build_site_api, init_site
from simplicitypress.core import ProgressEvent
from simplicitypress.core.config import load_config


def test_init_site_creates_basic_structure(tmp_path: Path) -> None:
    """init_site should create site.toml, content tree, and sample content."""
    site_root = tmp_path / "site"

    init_site(site_root)

    # Core config and content structure
    assert (site_root / "site.toml").is_file()
    assert (site_root / "content" / "posts").is_dir()
    assert (site_root / "content" / "pages").is_dir()

    # Sample content created on first init
    assert any((site_root / "content" / "posts").glob("*.md"))
    assert any((site_root / "content" / "pages").glob("*.md"))


def test_build_site_api_writes_to_default_output(tmp_path: Path) -> None:
    """build_site_api should write a built site into the default output directory."""
    site_root = tmp_path / "site"
    init_site(site_root)

    build_site_api(site_root)

    config = load_config(site_root)
    output_dir = config.paths.output_dir
    assert output_dir.is_dir()
    assert (output_dir / "index.html").is_file()


def test_build_site_api_respects_output_dir_override(tmp_path: Path) -> None:
    """build_site_api should honor an explicit output_dir override."""
    site_root = tmp_path / "site"
    custom_output = tmp_path / "custom-output"

    init_site(site_root)
    build_site_api(site_root, output_dir=custom_output)

    # Custom output directory should contain the built index page.
    assert custom_output.is_dir()
    assert (custom_output / "index.html").is_file()

    # The default output directory exists (created by load_config/init), but
    # should not contain the newly built index page for this run.
    config = load_config(site_root)
    default_output = config.paths.output_dir
    if default_output != custom_output:
        assert not (default_output / "index.html").exists()


def test_build_site_api_emits_progress_events(tmp_path: Path) -> None:
    """build_site_api should invoke the supplied progress callback."""
    site_root = tmp_path / "site"
    init_site(site_root)

    events: list[ProgressEvent] = []

    def collect(event: ProgressEvent) -> None:
        events.append(event)

    build_site_api(site_root, progress_cb=collect)

    assert events
    # At least one event should have a non-empty stage value.
    assert any(event.stage is not None for event in events)

