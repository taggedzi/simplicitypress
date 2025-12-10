from __future__ import annotations

from markdown_it import MarkdownIt

_md = MarkdownIt()


def render_markdown(markdown_text: str) -> str:
    """
    Render Markdown to HTML using a shared MarkdownIt instance.
    """
    return _md.render(markdown_text)
