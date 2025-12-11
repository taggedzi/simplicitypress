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
    for name in [
        "LICENSE",
        "THIRD-PARTY-NOTICES.txt",
        "QT-ATTRIBUTION.txt",
        "LICENSE-LGPLv3.txt",
    ]:
        src = root / name
        if not src.exists():
            session.error(f"Required file {src} is missing.")
        dst = exe_dir / name
        shutil.copy2(src, dst)

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
