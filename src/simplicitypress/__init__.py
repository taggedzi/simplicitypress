"""
SimplicityPress is a simple, library-first static site generator
focused on posts and pages.
"""

from __future__ import annotations

from pathlib import Path
import tomllib

__all__ = ["__version__"]


def _read_version() -> str:
    """Read the project version from pyproject.toml."""
    # Project root is two levels up from this file: src/simplicitypress/__init__.py
    root = Path(__file__).resolve().parents[2]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


__version__ = _read_version()
