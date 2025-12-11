"""Nox automation for SimplicityPress.

Sessions:
- tests: run pytest against the package
- lint: run ruff
- typecheck: run mypy
- build: build sdist+wheel via `python -m build`
"""

from __future__ import annotations
from pathlib import Path
import shutil
import nox

PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]

@nox.session
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest using the current interpreter."""
    session.install(".[dev]")
    session.run(
        "pytest",
        "--cov=simplicitypress",
        "--cov-report=term-missing",
    )


@nox.session
def lint(session: nox.Session) -> None:
    """Run ruff static checks."""
    session.install("ruff")
    # Add paths as you grow: tests/, noxfile.py, etc.
    session.run("ruff", "check", "src", "noxfile.py")


@nox.session
def typecheck(session: nox.Session) -> None:
    """Run mypy over the source tree."""
    session.install(".[dev]")
    session.run("mypy", "src")


@nox.session
def build(session: nox.Session) -> None:
    """Build sdist and wheel."""
    # `build` is already in your [project.optional-dependencies].:contentReference[oaicite:0]{index=0}
    session.install("build")
    session.run("python", "-m", "build")


@nox.session
def dist(session: nox.Session) -> None:
    """Build sdist and wheel into dist/ using python -m build."""
    session.install(".[dev]")
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    session.run("python", "-m", "build")


@nox.session
def build_exe(session: nox.Session) -> None:
    """Build a Windows GUI .exe for SimplicityPress using PyInstaller.

    This is intended to be run on Windows. It will create:
      dist/SimplicityPress/SimplicityPress.exe
    """

    # Install project with dev extras (includes PyInstaller)
    session.install(".[dev]")

    # Clean previous PyInstaller output
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("SimplicityPress.spec")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()

    # Run PyInstaller against the GUI entry point
    # Notes:
    # - --windowed: no console window
    # - --name SimplicityPress: final exe name
    # - --collect-data simplicitypress: include scaffold templates/static files
    # - -p src: ensure src/ is on the search path
    session.run(
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        # "--console",  # <-- For debug of binary
        "--name",
        "SimplicityPress",
        "--collect-data",
        "simplicitypress",
        "--collect-submodules",
        "simplicitypress",
        "-p",
        "src",
        "src/simplicitypress/gui.py",
    )
