from pathlib import Path
from textwrap import dedent
from typing import Optional
from importlib.resources import files
import http.server
import os
import shutil
import socketserver

import typer

from .core import ProgressEvent, build_site, load_config

app = typer.Typer(help="SimplicityPress static site generator CLI.")


def _print_progress(event: ProgressEvent) -> None:
    """
    Simple progress callback used by the CLI to report build stages.
    """
    message = event.message or ""
    typer.echo(f"[{event.stage}] {message}")


def _copy_scaffold(site_root: Path) -> None:
    """
    Copy default templates and static files from the packaged scaffold
    into the new site's templates/ and static/ directories.
    Does not overwrite existing files.
    """
    scaffold_root = files("simplicitypress.scaffold")
    templates_src = scaffold_root / "templates"
    static_src = scaffold_root / "static"

    templates_dest = site_root / "templates"
    static_dest = site_root / "static"

    templates_dest.mkdir(parents=True, exist_ok=True)
    static_dest.mkdir(parents=True, exist_ok=True)

    # Copy templates
    for entry in templates_src.iterdir():
        if entry.is_file():
            target = templates_dest / entry.name
            if not target.exists():
                shutil.copy2(entry, target)

    # Copy static tree recursively
    for entry in static_src.rglob("*"):
        if entry.is_file():
            relative = entry.relative_to(static_src)
            target = static_dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(entry, target)


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
    site_root.mkdir(parents=True, exist_ok=True)

    content_dir = site_root / "content"
    posts_dir = content_dir / "posts"
    pages_dir = content_dir / "pages"

    for directory in (content_dir, posts_dir, pages_dir):
        directory.mkdir(parents=True, exist_ok=True)

    site_toml = site_root / "site.toml"
    if site_toml.exists():
        typer.echo("site.toml already exists; leaving it unchanged.")
    else:
        site_toml.write_text(
            dedent(
                """\
                [site]
                title = "My SimplicityPress Site"
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
            ),
            encoding="utf-8",
        )
        typer.echo("Created default site.toml")

    # Copy scaffold templates and static assets
    _copy_scaffold(site_root)

    # Sample content
    sample_post = posts_dir / "example-post.md"
    if not sample_post.exists():
        sample_post.write_text(
            dedent(
                """\
                +++
                title = "Example Post"
                date = "2024-01-01"
                tags = ["example", "intro"]
                summary = "This is an example post created by SimplicityPress init."
                +++
                Welcome to **SimplicityPress**!

                This is your first post. Edit or delete it, then start writing.
                """,
            ),
            encoding="utf-8",
        )
        typer.echo("Created sample post at content/posts/example-post.md")

    sample_page = pages_dir / "about.md"
    if not sample_page.exists():
        sample_page.write_text(
            dedent(
                """\
                +++
                title = "About"
                slug = "about"
                show_in_nav = true
                nav_title = "About"
                nav_order = 10
                +++
                This is an example *About* page created by SimplicityPress init.
                """,
            ),
            encoding="utf-8",
        )
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
        typer.echo(f"[build] Loading config from: {site_root}")
        config = load_config(site_root)

        # Apply CLI overrides.
        if output is not None:
            config.paths.output_dir = output.resolve()
        if include_drafts:
            config.build["include_drafts"] = True

        typer.echo(f"[build] Writing output to: {config.paths.output_dir}")
        build_site(config, progress_cb=_print_progress)
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
        typer.echo(f"[serve] Loading config from: {site_root}")
        config = load_config(site_root)

        if output is not None:
            config.paths.output_dir = output.resolve()

        if not no_build:
            typer.echo("[serve] Building site before serving...")
            build_site(config, progress_cb=_print_progress)

        output_dir = config.paths.output_dir
        if not output_dir.exists():
            typer.echo(f"Output directory does not exist: {output_dir}")
            raise typer.Exit(code=1)

        typer.echo(f"[serve] Serving {output_dir} at http://localhost:{port}/")
        typer.echo("[serve] Press Ctrl+C to stop.")

        os.chdir(output_dir)

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                typer.echo("\n[serve] Stopping server.")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during serve: {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
