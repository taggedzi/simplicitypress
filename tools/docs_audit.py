# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
"""
Lightweight documentation correctness checks.

This module powers the ``docs_audit`` Nox session by verifying that:

* CLI commands referenced throughout the docs map to real Typer commands.
* Python examples in README.md execute successfully (unless marked ``no-run``).
* Public functions/classes in api.py and cli.py carry docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import os
import re
import subprocess
import sys
import tempfile
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
NO_AUDIT_BEGIN = "<!-- no-audit -->"
NO_AUDIT_END = "<!-- /no-audit -->"
CLI_PATTERN = re.compile(r"simplicitypress\s+([a-zA-Z0-9_-]+)")
PY_BLOCK_PATTERN = re.compile(r"```python(?P<info>[^\n]*)\n(?P<body>.*?)```", re.DOTALL)


@dataclass
class PythonBlock:
    """A Python fenced code block found in README.md."""

    code: str
    start_line: int
    metadata: str

    @property
    def should_run(self) -> bool:
        """True when the block should be executed."""
        meta_tokens = {token.strip().lower() for token in self.metadata.split() if token.strip()}
        return "no-run" not in meta_tokens


def remove_no_audit_sections(text: str) -> str:
    """
    Remove ``<!-- no-audit -->`` sections from text.

    Content between ``<!-- no-audit -->`` and ``<!-- /no-audit -->`` is ignored.
    """
    result: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find(NO_AUDIT_BEGIN, cursor)
        if start == -1:
            result.append(text[cursor:])
            break
        result.append(text[cursor:start])
        end = text.find(NO_AUDIT_END, start)
        if end == -1:
            # Unbalanced marker; drop the remainder.
            break
        cursor = end + len(NO_AUDIT_END)
    return "".join(result)


def extract_cli_commands(text: str) -> set[str]:
    """
    Extract CLI commands referenced via ``simplicitypress <command>``.

    Options such as ``--help`` are ignored.
    """
    commands: set[str] = set()
    for match in CLI_PATTERN.finditer(text):
        command = match.group(1)
        if not command or command.startswith("-"):
            continue
        commands.add(command)
    return commands


def read_markdown_commands(paths: Iterable[Path]) -> set[str]:
    """Return CLI commands referenced across provided Markdown files."""
    commands: set[str] = set()
    for file_path in paths:
        text = file_path.read_text(encoding="utf-8")
        cleaned = remove_no_audit_sections(text)
        commands.update(extract_cli_commands(cleaned))
    return commands


def get_cli_commands_from_help() -> set[str]:
    """
    Run ``simplicitypress --help`` and parse the Commands section.
    """
    env = os.environ.copy()
    src_entries = [str(SRC_DIR)]
    existing = env.get("PYTHONPATH")
    if existing:
        src_entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(src_entries)
    result = subprocess.run(
        [sys.executable, "-m", "simplicitypress", "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
    )
    commands: set[str] = set()
    in_commands = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() == "commands:":
            in_commands = True
            continue
        if in_commands:
            if not line.startswith(" "):
                break
            token = stripped.split()[0]
            commands.add(token)
    if not commands:
        msg = "Failed to parse commands from `simplicitypress --help` output."
        raise RuntimeError(msg)
    return commands


def extract_python_blocks(markdown: str) -> list[PythonBlock]:
    """Locate python fenced code blocks inside Markdown content."""
    blocks: list[PythonBlock] = []
    for match in PY_BLOCK_PATTERN.finditer(markdown):
        info = match.group("info").strip()
        code = match.group("body")
        before = markdown[: match.start()]
        start_line = before.count("\n") + 1
        blocks.append(PythonBlock(code=code, start_line=start_line, metadata=info))
    return blocks


def run_python_blocks(blocks: Sequence[PythonBlock]) -> None:
    """
    Execute python blocks in an isolated temporary directory.
    """
    if not blocks:
        return
    sys.path.insert(0, str(SRC_DIR))
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="simplicitypress-docs-") as tmp_dir:
        os.chdir(tmp_dir)
        try:
            for index, block in enumerate(blocks, start=1):
                if not block.should_run:
                    continue
                code = textwrap_dedent_preserve(block.code)
                namespace: dict[str, object] = {"__name__": "__main__"}
                try:
                    exec(compile(code, f"README.md:{block.start_line}", "exec"), namespace)  # noqa: S102
                except Exception as exc:  # noqa: BLE001
                    msg = (
                        "Python example failed "
                        f"(block #{index} starting line {block.start_line}): {exc}"
                    )
                    raise RuntimeError(msg) from exc
        finally:
            os.chdir(original_cwd)


def textwrap_dedent_preserve(code: str) -> str:
    """Dedent code blocks while preserving leading/trailing blank lines."""
    lines = code.splitlines()
    if not lines:
        return ""
    # Remove leading/trailing empty lines for consistent execution.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def gather_markdown_files() -> list[Path]:
    """Collect README.md plus any docs/*.md files."""
    files: list[Path] = [REPO_ROOT / "README.md"]
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        files.extend(sorted(docs_dir.rglob("*.md")))
    return files


def find_missing_docstrings(paths: Sequence[Path]) -> list[str]:
    """Return missing docstring descriptors for public definitions."""
    missing: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source, filename=str(path))
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                docstring = ast.get_docstring(node)
                if docstring and docstring.strip():
                    continue
                missing.append(f"{path}:{node.lineno}:{node.name}")
    return missing


def main() -> None:
    """Entry point for the docs audit helper."""
    markdown_files = gather_markdown_files()
    mentioned_commands = read_markdown_commands(markdown_files)
    cli_commands = get_cli_commands_from_help()
    unknown = sorted(mentioned_commands - cli_commands)
    if unknown:
        listed = ", ".join(sorted(unknown))
        msg = f"Unknown CLI commands referenced in docs: {listed}"
        raise SystemExit(msg)

    readme_path = REPO_ROOT / "README.md"
    readme_content = remove_no_audit_sections(readme_path.read_text(encoding="utf-8"))
    python_blocks = extract_python_blocks(readme_content)
    run_python_blocks(python_blocks)

    targets = [
        REPO_ROOT / "src" / "simplicitypress" / "api.py",
        REPO_ROOT / "src" / "simplicitypress" / "cli.py",
    ]
    missing_docstrings = find_missing_docstrings(targets)
    if missing_docstrings:
        formatted = "\n".join(missing_docstrings)
        msg = f"Missing docstrings detected:\n{formatted}"
        raise SystemExit(msg)

    print("Docs audit passed.")


if __name__ == "__main__":
    main()
