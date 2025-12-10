from pathlib import Path
from textwrap import dedent

from simplicitypress.core.frontmatter import parse_front_matter_and_body


def test_frontmatter_with_toml(tmp_path: Path) -> None:
    content = dedent(
        """\
        +++
        title = "Hello"
        tags = ["a", "b"]
        +++
        This is the body.

        Second line.
        """,
    )
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    meta, body = parse_front_matter_and_body(path)

    assert meta["title"] == "Hello"
    assert meta["tags"] == ["a", "b"]
    assert "This is the body." in body
    assert "Second line." in body


def test_frontmatter_without_toml(tmp_path: Path) -> None:
    content = "Just some markdown.\nNo front matter here."
    path = tmp_path / "post.md"
    path.write_text(content, encoding="utf-8")

    meta, body = parse_front_matter_and_body(path)

    assert meta == {}
    assert body.startswith("Just some markdown")

