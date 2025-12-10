from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import tomllib

from .default_config import default_config
from .fs import ensure_directory
from .models import Config, SitePaths


def _merge_dicts(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """
    Recursively merge two mapping objects, returning a new dict.

    Values from ``override`` take precedence over ``base``. When both
    values are mappings, they are merged recursively; otherwise the
    ``override`` value replaces the ``base`` value.
    """
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], Mapping)
            and isinstance(value, Mapping)
        ):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_config(site_root: Path) -> Config:
    """
    Load ``site.toml`` from the given ``site_root``, merge it with
    built-in defaults, resolve filesystem paths, validate required
    directories, and return a populated :class:`Config` object.
    """
    if not site_root.exists() or not site_root.is_dir():
        msg = f"site_root must be an existing directory: {site_root}"
        raise NotADirectoryError(msg)

    site_toml = site_root / "site.toml"
    if not site_toml.exists():
        raise FileNotFoundError("site.toml not found in site_root")

    with site_toml.open("rb") as f:
        user_config: dict[str, Any] = tomllib.load(f)

    merged = _merge_dicts(default_config, user_config)

    paths_cfg = merged.get("paths", {})

    content_dir = (site_root / paths_cfg.get("content_dir", "content")).resolve()
    posts_dir = (site_root / paths_cfg.get("posts_dir", "content/posts")).resolve()
    pages_dir = (site_root / paths_cfg.get("pages_dir", "content/pages")).resolve()
    templates_dir = (site_root / paths_cfg.get("templates_dir", "templates")).resolve()
    static_dir = (site_root / paths_cfg.get("static_dir", "static")).resolve()
    output_dir = (site_root / paths_cfg.get("output_dir", "output")).resolve()

    site_paths = SitePaths(
        site_root=site_root.resolve(),
        content_dir=content_dir,
        posts_dir=posts_dir,
        pages_dir=pages_dir,
        templates_dir=templates_dir,
        static_dir=static_dir,
        output_dir=output_dir,
    )

    # Validate required directories (must already exist).
    for required in (
        site_paths.content_dir,
        site_paths.posts_dir,
        site_paths.pages_dir,
        site_paths.templates_dir,
    ):
        if not required.exists() or not required.is_dir():
            raise FileNotFoundError(f"Missing required directory: {required}")

    # Static directory: create if missing, but do not fail.
    if not site_paths.static_dir.exists():
        ensure_directory(site_paths.static_dir)

    # Output directory: ensure it exists (create if needed).
    ensure_directory(site_paths.output_dir)

    return Config(
        site=merged.get("site", {}),
        build=merged.get("build", {}),
        author=merged.get("author", {}),
        paths=site_paths,
    )

