from __future__ import annotations

from pathlib import Path

from .models import Config, SitePaths


def load_config(site_root: Path) -> Config:
    """
    Load site.toml from the given site_root, merge with defaults,
    and construct a Config object including resolved SitePaths.

    This is currently a stub implementation and does not perform
    real configuration loading or validation.
    """
    if not site_root.exists():
        msg = f"Site root does not exist: {site_root}"
        raise FileNotFoundError(msg)

    # TODO: Implement real configuration loading from site.toml.
    raise NotImplementedError("Configuration loading is not implemented yet.")

