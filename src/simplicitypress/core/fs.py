from __future__ import annotations

from pathlib import Path
import shutil


def ensure_directory(path: Path) -> None:
    """
    Ensure that the given directory exists, creating it if necessary.

    This implementation creates parent directories as needed and
    can be extended later to handle permissions, logging, and
    error reporting concerns.
    """
    path.mkdir(parents=True, exist_ok=True)


def copy_static_tree(static_dir: Path, output_static_dir: Path) -> None:
    """
    Copy the static assets tree from static_dir into output_static_dir.

    If static_dir does not exist or is not a directory, this function
    returns without performing any work. Any existing output_static_dir
    is removed before copying to ensure a clean tree.
    """
    if not static_dir.exists() or not static_dir.is_dir():
        return

    if output_static_dir.exists():
        shutil.rmtree(output_static_dir)

    shutil.copytree(static_dir, output_static_dir)
