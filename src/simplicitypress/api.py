from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Callable, Optional
import http.server
import os
import shutil
import socketserver

from importlib.resources import files
from importlib.resources.abc import Traversable

from .core import ProgressEvent, build_site, load_config


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

    def _copy_file(src: Traversable, dst: Path) -> None:
        with src.open("rb") as src_f, dst.open("wb") as dst_f:
            shutil.copyfileobj(src_f, dst_f)

    # Copy templates
    for entry in templates_src.iterdir():
        if entry.is_file():
            target = templates_dest / entry.name
            if not target.exists():
                _copy_file(entry, target)

    # Copy static tree recursively
    def _copy_static(src: Traversable, dst_root: Path) -> None:
        for child in src.iterdir():
            if child.is_dir():
                child_dest = dst_root / child.name
                child_dest.mkdir(parents=True, exist_ok=True)
                _copy_static(child, child_dest)
            elif child.is_file():
                target = dst_root / child.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    _copy_file(child, target)

    _copy_static(static_src, static_dest)


def init_site(site_root: Path) -> None:
    """
    Initialize a new SimplicityPress site at the given path.

    Creates the directory structure, writes a default site.toml (if missing),
    copies scaffold templates/static assets, and creates example content.
    """
    site_root.mkdir(parents=True, exist_ok=True)

    content_dir = site_root / "content"
    posts_dir = content_dir / "posts"
    pages_dir = content_dir / "pages"

    for directory in (content_dir, posts_dir, pages_dir):
        directory.mkdir(parents=True, exist_ok=True)

    site_toml = site_root / "site.toml"
    if not site_toml.exists():
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


def build_site_api(
    site_root: Path,
    *,
    output_dir: Optional[Path] = None,
    include_drafts: bool = False,
    progress_cb: Optional[Callable[[ProgressEvent], None]] = None,
) -> None:
    """
    Build a SimplicityPress site for the given site_root.

    This wraps the core configuration loading and build pipeline and is
    suitable for use from CLI, GUI, or other Python callers.
    """
    config = load_config(site_root)

    if output_dir is not None:
        config.paths.output_dir = output_dir.resolve()

    if include_drafts:
        config.build["include_drafts"] = True

    build_site(config, progress_cb=progress_cb)


def serve_site(
    site_root: Path,
    *,
    output_dir: Optional[Path] = None,
    port: int = 8000,
    build_first: bool = True,
) -> None:
    """
    Serve the built site for local development.

    Optionally rebuilds the site first and then serves the configured
    output directory on the given port.
    """
    config = load_config(site_root)

    if output_dir is not None:
        config.paths.output_dir = output_dir.resolve()

    if build_first:
        build_site(config)

    root_dir = config.paths.output_dir
    if not root_dir.exists():
        msg = f"Output directory does not exist: {root_dir}"
        raise FileNotFoundError(msg)

    # Serve the directory until interrupted.
    os.chdir(root_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            # Allow clean shutdown when used from CLI.
            pass

