"""Nox automation for SimplicityPress.

Sessions:
- tests: run pytest against the package
- lint: run ruff
- typecheck: run mypy
- build: build sdist+wheel via `python -m build`
"""

from __future__ import annotations

import nox


@nox.session
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest using the current interpreter."""
    session.install(".[dev]")
    session.run("pytest")


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
