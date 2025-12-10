from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from simplicitypress.cli import app


def test_cli_init_creates_site(tmp_path: Path) -> None:
    """`simplicitypress init` should create a new site in the given directory."""
    runner = CliRunner()
    site_root = tmp_path / "site"

    result = runner.invoke(app, ["init", "--site-root", str(site_root)])

    assert result.exit_code == 0
    assert (site_root / "site.toml").is_file()


def test_cli_build_succeeds_after_init(tmp_path: Path) -> None:
    """`simplicitypress build` should succeed on a freshly initialized site."""
    runner = CliRunner()
    site_root = tmp_path / "site"

    init_result = runner.invoke(app, ["init", "--site-root", str(site_root)])
    assert init_result.exit_code == 0

    build_result = runner.invoke(app, ["build", "--site-root", str(site_root)])

    assert build_result.exit_code == 0
    # Basic smoke check that some output was produced.
    assert (site_root / "output" / "index.html").is_file()


def test_cli_build_with_invalid_root_fails_cleanly(tmp_path: Path) -> None:
    """`simplicitypress build` should report an error for a non-existent site root."""
    runner = CliRunner()
    invalid_root = tmp_path / "does_not_exist"

    result = runner.invoke(app, ["build", "--site-root", str(invalid_root)])

    assert result.exit_code != 0
    # Error message should mention an error during build.
    assert "Error during build:" in result.stdout

