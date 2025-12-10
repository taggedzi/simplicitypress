from simplicitypress.core.markdown import render_markdown


def test_render_markdown_basic() -> None:
    html = render_markdown("# Hello\n\nThis is **bold**.")
    assert "<h1>" in html
    assert "Hello" in html
    # markdown-it-py uses <strong> for bold by default
    assert "<strong>" in html or "<b>" in html

