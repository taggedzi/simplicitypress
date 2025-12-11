from __future__ import annotations

"""
SimplicityPress: a small, opinionated static site generator.

Public API:
- CLI entry points live in `simplicitypress.cli`.
- Programmatic API lives in `simplicitypress.api` and `simplicitypress.core.*`.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path

__all__ = ["__version__"]


def _read_version_from_pyproject() -> str:
    """Fallback for dev checkouts when package metadata isn't available."""
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover
        return "0.0.0"

    # src/simplicitypress/__init__.py -> project root
    root = Path(__file__).resolve().parents[2]
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return "0.0.0"

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    return str(version) if version is not None else "0.0.0"


try:
    # Preferred: version from installed package metadata
    __version__ = _pkg_version("simplicitypress")
except PackageNotFoundError:
    # Fallback for "run from source tree without install"
    __version__ = _read_version_from_pyproject()
