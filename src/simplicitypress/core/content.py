from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .frontmatter import parse_front_matter_and_body
from .markdown import render_markdown
from .models import Config, Page, Post


def _normalize_tags(raw: Any, *, source: Path) -> list[str]:
    """
    Normalize the tags value from front matter into a list of strings.
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(tag) for tag in raw]
    msg = f"Invalid 'tags' value in front matter for {source!s}: {raw!r}"
    raise ValueError(msg)


def discover_content(config: Config) -> tuple[list[Post], list[Page]]:
    """
    Scan the site's content directories and return lists of Post and Page
    instances with rendered HTML content.
    """
    posts: list[Post] = []
    pages: list[Page] = []

    posts_dir = config.paths.posts_dir
    pages_dir = config.paths.pages_dir

    # Discover posts
    for path in posts_dir.glob("*.md"):
        metadata, body = parse_front_matter_and_body(path)
        body_html = render_markdown(body)

        title = metadata.get("title")
        if not title:
            msg = f"Missing required 'title' in post front matter: {path}"
            raise ValueError(msg)

        raw_date = metadata.get("date")
        if not raw_date:
            msg = f"Missing required 'date' in post front matter: {path}"
            raise ValueError(msg)
        try:
            date = datetime.fromisoformat(str(raw_date))
        except (TypeError, ValueError) as exc:
            msg = f"Invalid 'date' value in post front matter for {path}: {raw_date!r}"
            raise ValueError(msg) from exc

        slug = metadata.get("slug") or path.stem

        tags = _normalize_tags(metadata.get("tags"), source=path)
        draft = bool(metadata.get("draft", False))

        summary = metadata.get("summary")
        if summary is None:
            summary = body[:200].strip()

        cover_image = metadata.get("cover_image")
        cover_alt = metadata.get("cover_alt")

        url = f"/posts/{slug}/"

        posts.append(
            Post(
                title=str(title),
                date=date,
                slug=str(slug),
                tags=tags,
                draft=draft,
                summary=str(summary),
                cover_image=str(cover_image) if cover_image is not None else None,
                cover_alt=str(cover_alt) if cover_alt is not None else None,
                content_html=body_html,
                source_path=path,
                url=url,
            ),
        )

    # Discover pages
    for path in pages_dir.glob("*.md"):
        metadata, body = parse_front_matter_and_body(path)
        body_html = render_markdown(body)

        title = metadata.get("title")
        if not title:
            msg = f"Missing required 'title' in page front matter: {path}"
            raise ValueError(msg)

        slug = metadata.get("slug") or path.stem
        url = f"/{slug}/"

        pages.append(
            Page(
                title=str(title),
                slug=str(slug),
                content_html=body_html,
                source_path=path,
                url=url,
            ),
        )

    return posts, pages

