# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
"""Nox automation for SimplicityPress.

Sessions:
- tests: run pytest against the package
- lint: run ruff
- typecheck: run mypy
- build: build sdist+wheel via `python -m build`
"""

from __future__ import annotations
from pathlib import Path
import hashlib
import shutil
import tomllib
import os
import nox

PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]


def _read_version() -> str:
    """Read the project version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data["project"]["version"]

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
def spdx(session: nox.Session) -> None:
    """Verify that SPDX headers are present."""
    session.run("python", "tools/add_spdx_headers.py", "--check")


@nox.session
def spdx_fix(session: nox.Session) -> None:
    """Insert SPDX headers where missing."""
    session.run("python", "tools/add_spdx_headers.py", "--fix")


@nox.session
def changelog(session: nox.Session) -> None:
    """Regenerate CHANGELOG.md via git-cliff."""
    session.install("git-cliff")
    session.run("git", "cliff", "--output", "CHANGELOG.md", external=True)


@nox.session
def changelog_check(session: nox.Session) -> None:
    """Verify CHANGELOG.md is up to date."""
    session.install("git-cliff")
    session.run("git", "cliff", "--output", "CHANGELOG.md", external=True)
    session.run("git", "diff", "--exit-code", "CHANGELOG.md", external=True)


@nox.session
def sbom(session: nox.Session) -> None:
    """Generate a CycloneDX SBOM covering runtime dependencies only."""
    dist_dir = Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)
    output = dist_dir / "sbom.cdx.json"

    # Create a clean runtime-only virtual environment
    runtime_env = Path(".nox") / "sbom-runtime"
    if runtime_env.exists():
        shutil.rmtree(runtime_env)

    session.run(
        "python",
        "-m",
        "venv",
        str(runtime_env),
        external=True,
    )

    runtime_python = runtime_env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    # Install runtime dependencies only
    session.run(runtime_python, "-m", "pip", "install", ".", external=True)

    # Install SBOM tool in the *nox* environment (not runtime env)
    session.install("cyclonedx-bom")

    # Generate SBOM by scanning the runtime env
    session.run(
        "python",
        "-m",
        "cyclonedx_py",
        "environment",
        str(runtime_env),
        "--output-format",
        "JSON",
        "--output-file",
        str(output),
        "--output-reproducible",
        "--pyproject",
        "pyproject.toml",
    )

    session.log(f"SBOM written to {output}")

    session.run(
        "python",
        "tools/filter_sbom.py",
        str(output),
    )


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


@nox.session
def build_release(session: nox.Session) -> None:
    """Package the Windows build into a versioned zip + SHA256 checksum."""
    dist_dir = Path("dist")
    exe_dir = dist_dir / "SimplicityPress"

    if not exe_dir.exists():
        session.error(
            "PyInstaller output not found at dist/SimplicityPress. "
            "Run 'nox -s build_exe' first."
        )

    # Copy license / attribution files into the exe folder
    root = Path(".")
    mappings = [
        ("LICENSE", exe_dir / "LICENSE"),
        ("THIRD-PARTY-NOTICES.txt", exe_dir / "THIRD-PARTY-NOTICES.txt"),
        ("QT-ATTRIBUTION.txt", exe_dir / "QT-ATTRIBUTION.txt"),
        ("LICENSES/pyside_lgpl.txt", exe_dir / "licenses" / "pyside_lgpl.txt"),
    ]
    for src_name, dst_path in mappings:
        src = root / src_name
        if not src.exists():
            session.error(f"Required file {src} is missing.")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_path)

    version = _read_version()
    base_name = f"simplicitypress-v{version}-win64"
    zip_path = dist_dir / f"{base_name}.zip"
    sha_path = dist_dir / f"{base_name}.zip.sha256"

    if zip_path.exists():
        zip_path.unlink()
    if sha_path.exists():
        sha_path.unlink()

    # Create zip from contents of dist/SimplicityPress
    shutil.make_archive(
        base_name=str(dist_dir / base_name),
        format="zip",
        root_dir=exe_dir,
        base_dir=".",
    )

    # Compute SHA256
    hasher = hashlib.sha256()
    with zip_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            if not chunk:
                break
            hasher.update(chunk)
    digest = hasher.hexdigest()
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")

    session.log(f"Created {zip_path}")
    session.log(f"Created {sha_path}")


# in noxfile.py
@nox.session
def release_local(session: nox.Session) -> None:
    """
    Convenience wrapper around tools/make_release.py.

    Usage:
        nox -s release_local -- 0.5.0
    """
    if not session.posargs:
        session.error("Usage: nox -s release_local -- <version>")

    version = session.posargs[0]
    session.run("python", "tools/make_release.py", version, external=True)
