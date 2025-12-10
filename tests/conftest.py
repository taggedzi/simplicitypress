from __future__ import annotations

import sys
from pathlib import Path
import types


def _ensure_src_on_path() -> None:
    """Ensure the src/ directory is on sys.path for imports."""
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    src_str = str(src)
    if src.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


def _ensure_tomllib() -> None:
    """
    Provide a tomllib-compatible module on older Python versions
    by delegating to tomli, if available.
    """
    try:
        import tomllib  # type: ignore[import]
    except ModuleNotFoundError:
        try:
            import tomli  # type: ignore[import]
        except ModuleNotFoundError:
            return

        shim = types.ModuleType("tomllib")
        shim.loads = tomli.loads
        shim.load = tomli.load
        shim.TOMLDecodeError = tomli.TOMLDecodeError
        sys.modules["tomllib"] = shim


def _ensure_importlib_resources_abc() -> None:
    """
    Ensure importlib.resources.abc.Traversable can be imported even if
    a backport interferes with the standard library layout.
    """
    try:
        from importlib.resources.abc import Traversable  # type: ignore[import]  # noqa: F401
        return
    except Exception:
        pass

    import types as _types

    abc_module = _types.ModuleType("importlib.resources.abc")

    class Traversable:  # type: ignore[override]
        """Minimal stand-in for typing purposes in tests."""

    abc_module.Traversable = Traversable  # type: ignore[attr-defined]
    sys.modules["importlib.resources.abc"] = abc_module


_ensure_src_on_path()
_ensure_tomllib()
_ensure_importlib_resources_abc()

