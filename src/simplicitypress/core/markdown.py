# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from markdown_it import MarkdownIt

_md = MarkdownIt()


def render_markdown(markdown_text: str) -> str:
    """
    Render Markdown to HTML using a shared MarkdownIt instance.
    """
    return _md.render(markdown_text)
