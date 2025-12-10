from pathlib import Path
from typing import Optional

import typer

from .api import build_site_api, init_site, serve_site
from .core import ProgressEvent

app = typer.Typer(help="SimplicityPress static site generator CLI.")


def _print_progress(event: ProgressEvent) -> None:
    """
    Simple progress callback used by the CLI to report build stages.
    """
    message = event.message or ""
    typer.echo(f"[{event.stage}] {message}")


@app.command()
def init(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
) -> None:
    """
    Initialize a new SimplicityPress site at the given path.
    """
    typer.echo(f"[init] Initializing site at: {site_root}")

    site_toml = site_root / "site.toml"
    sample_post = site_root / "content" / "posts" / "example-post.md"
    sample_page = site_root / "content" / "pages" / "about.md"

    site_toml_existed = site_toml.exists()
    sample_post_existed = sample_post.exists()
    sample_page_existed = sample_page.exists()

    try:
        init_site(site_root)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during init: {exc}")
        raise typer.Exit(code=1) from exc

    if site_toml_existed:
        typer.echo("site.toml already exists; leaving it unchanged.")
    else:
        typer.echo("Created default site.toml")

    if not sample_post_existed and sample_post.exists():
        typer.echo("Created sample post at content/posts/example-post.md")

    if not sample_page_existed and sample_page.exists():
        typer.echo("Created sample page at content/pages/about.md")

    typer.echo("Initialization complete.")


@app.command()
def new(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the existing site root directory.",
    ),
) -> None:
    """
    Create a new content item (post or page) within the site.
    """
    typer.echo(f"[new] Would create new content in site at: {site_root}")


@app.command()
def build(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Override the site's configured output directory.",
    ),
    include_drafts: bool = typer.Option(
        False,
        "--include-drafts",
        help="Include draft posts in the build.",
    ),
) -> None:
    """
    Build the static site from the given site root.
    """
    try:
        typer.echo(f"[build] Building site at: {site_root}")
        build_site_api(
            site_root=site_root,
            output_dir=output,
            include_drafts=include_drafts,
            progress_cb=_print_progress,
        )
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during build: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def serve(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory to serve (defaults to config.paths.output_dir).",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to serve on.",
    ),
    no_build: bool = typer.Option(
        False,
        "--no-build",
        help="Serve without rebuilding the site first.",
    ),
) -> None:
    """
    Serve the generated static site for local development.
    """
    try:
        typer.echo(f"[serve] Serving site at: {site_root}")
        serve_site(
            site_root=site_root,
            output_dir=output,
            port=port,
            build_first=not no_build,
        )
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during serve: {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
