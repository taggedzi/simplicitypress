# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "add_spdx_headers.py"
MODULE_SPEC = importlib.util.spec_from_file_location("add_spdx_headers", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
add_spdx_headers = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules["add_spdx_headers"] = add_spdx_headers
MODULE_SPEC.loader.exec_module(add_spdx_headers)

apply_spdx_to_text = add_spdx_headers.apply_spdx_to_text
SPDX_LICENSE_LINE = add_spdx_headers.SPDX_LICENSE_LINE


DEFAULT_HOLDER = "SimplicityPress contributors"
DEFAULT_YEAR = 2024


def test_insert_at_file_start() -> None:
    text = "print('hi')\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert conflict is False
    assert new_text == (
        "# SPDX-FileCopyrightText: 2024 SimplicityPress contributors\n"
        "# SPDX-License-Identifier: MIT\n"
        "print('hi')\n"
    )


def test_insert_after_shebang() -> None:
    text = "#!/usr/bin/env python3\nprint('hi')\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert new_text.startswith("#!/usr/bin/env python3\n# SPDX-File")


def test_insert_after_encoding_cookie() -> None:
    text = "# -*- coding: utf-8 -*-\nprint('hi')\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert "# -*- coding: utf-8 -*-\n# SPDX-File" in new_text


def test_insert_after_shebang_and_encoding_cookie() -> None:
    text = "#!/usr/bin/python\n# -*- coding: latin-1 -*-\nprint('hi')\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert "# -*- coding: latin-1 -*-\n# SPDX-File" in new_text


def test_insert_before_module_docstring() -> None:
    text = '"""Module docstring."""\nVALUE = 1\n'
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert new_text.splitlines()[0].startswith("# SPDX-File")
    assert '"""Module docstring."""' in new_text.splitlines()[2]


def test_string_literal_reference_does_not_block_insertion() -> None:
    text = "MESSAGE = 'SPDX-License-Identifier: MIT inside string'\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is True
    assert conflict is False
    assert new_text.startswith("# SPDX-File")


def test_existing_mit_spdx_is_preserved() -> None:
    text = (
        "# SPDX-FileCopyrightText: 2023 Someone else\n"
        f"{SPDX_LICENSE_LINE}\n"
        "print('hi')\n"
    )
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is False
    assert conflict is False
    assert new_text == text


def test_conflict_detected_for_non_mit_license() -> None:
    text = "# SPDX-License-Identifier: Apache-2.0\nprint('hi')\n"
    new_text, added, conflict = apply_spdx_to_text(text, DEFAULT_YEAR, DEFAULT_HOLDER)

    assert added is False
    assert conflict is True
    assert new_text == text
