from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# your existing imports:
from .build import build_site
from .config import load_config
from .models import Config, Page, Post, ProgressEvent, SitePaths, Stage

try:
    __version__ = version("simplicitypress")
except PackageNotFoundError:
    # Fallback for dev / frozen executables where metadata isn't available
    __version__ = "0.0.0"

__all__ = [
    "Config",
    "SitePaths",
    "Post",
    "Page",
    "ProgressEvent",
    "Stage",
    "load_config",
    "build_site",
    "__version__",
]
