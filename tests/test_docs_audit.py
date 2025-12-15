# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

import textwrap

from tools import docs_audit


def test_remove_no_audit_sections() -> None:
    source = textwrap.dedent(
        """\
        keep
        <!-- no-audit -->
        skip me
        <!-- /no-audit -->
        final
        """,
    )
    result = docs_audit.remove_no_audit_sections(source)
    assert "skip me" not in result
    assert "keep" in result and "final" in result


def test_extract_cli_commands_ignores_options() -> None:
    text = "simplicitypress build --site-root demo\nsimplicitypress --help\n"
    commands = docs_audit.extract_cli_commands(text)
    assert commands == {"build"}


def test_extract_python_blocks_skips_no_run() -> None:
    text = textwrap.dedent(
        """\
        ```python
        print("run")
        ```

        ```python no-run
        print("skip")
        ```
        """,
    )
    blocks = docs_audit.extract_python_blocks(text)
    assert len(blocks) == 2
    assert blocks[0].should_run is True
    assert blocks[1].should_run is False


def test_find_missing_docstrings_reports_public_defs(tmp_path: Path) -> None:
    module = tmp_path / "example.py"
    module.write_text(
        textwrap.dedent(
            """\
            def public():
                pass

            def documented():
                \"\"\"Docstring.\"\"\"
                return None

            def _private():
                pass
            """,
        ),
        encoding="utf-8",
    )
    missing = docs_audit.find_missing_docstrings([module])
    assert any("public" in entry for entry in missing)
    assert not any("documented" in entry for entry in missing)
