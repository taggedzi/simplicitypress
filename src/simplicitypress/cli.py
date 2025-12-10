from pathlib import Path

import typer

from .core import ProgressEvent, build_site, load_config

app = typer.Typer(help="SimplicityPress static site generator CLI.")


def _print_progress(event: ProgressEvent) -> None:
    """
    Simple progress callback used by the CLI to report build stages.
    """
    typer.echo(f"[{event.stage}] {event.current}/{event.total} {event.message}")


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
    typer.echo(f"[init] Would initialize a new site at: {site_root}")


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
    ) -> None:
    """
    Build the static site from the given site root.
    """
    typer.echo(f"[build] Building site at: {site_root}")
    config = load_config(site_root)
    build_site(config, progress_cb=_print_progress)


@app.command()
def serve(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
) -> None:
    """
    Serve the generated static site for local development.
    """
    typer.echo(f"[serve] Would serve site from: {site_root}")


if __name__ == "__main__":
    app()
