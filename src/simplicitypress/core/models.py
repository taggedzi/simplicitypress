from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


@dataclass
class SitePaths:
    """
    Resolved filesystem paths for the various parts of a SimplicityPress site.
    """

    site_root: Path
    content_dir: Path
    posts_dir: Path
    pages_dir: Path
    templates_dir: Path
    static_dir: Path
    output_dir: Path


@dataclass
class Config:
    """
    Top-level configuration for a SimplicityPress site.

    Values are loaded from ``site.toml`` in the site root and
    merged over a built-in set of defaults. Nested mapping keys
    in the user configuration override the corresponding defaults.
    """

    site: dict
    build: dict
    author: dict
    paths: SitePaths


@dataclass
class Post:
    """
    Represents a single blog post with metadata and rendered HTML content.
    """

    title: str
    date: datetime
    slug: str
    tags: list[str]
    draft: bool
    summary: str
    cover_image: str | None
    cover_alt: str | None
    content_html: str
    source_path: Path
    url: str


@dataclass
class Page:
    """
    Represents a single static page with rendered HTML content.
    """

    title: str
    slug: str
    content_html: str
    source_path: Path
    url: str


class Stage(str, Enum):
    """
    High-level stages of the site build process.
    """

    LOADING_CONFIG = "loading_config"
    DISCOVERING_CONTENT = "discovering_content"
    RENDERING_TEMPLATES = "rendering_templates"
    COPYING_STATIC = "copying_static"
    DONE = "done"


@dataclass
class ProgressEvent:
    """
    Progress information emitted by long-running operations such as builds.
    """

    stage: Stage
    current: int
    total: int
    message: str = ""
