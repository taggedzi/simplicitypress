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

        show_in_nav = bool(metadata.get("show_in_nav", False))
        nav_title = metadata.get("nav_title")
        nav_order_raw = metadata.get("nav_order", 1000)
        try:
            nav_order = int(nav_order_raw)
        except (TypeError, ValueError):
            nav_order = 1000

        raw_page_date = metadata.get("date")
        page_date = None
        if raw_page_date:
            try:
                page_date = datetime.fromisoformat(str(raw_page_date))
            except (TypeError, ValueError) as exc:
                msg = f"Invalid 'date' value in page front matter for {path}: {raw_page_date!r}"
                raise ValueError(msg) from exc

        pages.append(
            Page(
                title=str(title),
                slug=str(slug),
                content_html=body_html,
                source_path=path,
                url=url,
                date=page_date,
                show_in_nav=show_in_nav,
                nav_title=str(nav_title) if nav_title is not None else None,
                nav_order=nav_order,
            ),
        )

    return posts, pages
