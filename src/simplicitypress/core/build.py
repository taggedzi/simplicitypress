from __future__ import annotations

import re
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Callable, Optional, Sequence

from .content import discover_content
from .fs import copy_static_tree
from .models import Config, Page, Post, ProgressEvent, Stage
from .render import create_environment, render_to_file
from .search_index import SearchAssetsBuilder
from .sitemap import SitemapEntry, generate_sitemap


INDEX_FILENAME = "index.html"


def _build_tag_index(posts: list[Post]) -> dict[str, list[Post]]:
    """
    Build a mapping of tag name to the list of posts with that tag.
    """
    tag_index: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            tag_index.setdefault(tag, []).append(post)
    return tag_index


def _slugify_tag(tag: str) -> str:
    """
    Convert a tag value into a URL-friendly slug.
    """
    tag = tag.strip().lower()
    tag = tag.replace(" ", "-")
    return re.sub(r"[^a-z0-9_-]", "", tag)


def _build_nav_items(
    pages: list[Page],
    extra: Sequence[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """
    Build a list of navigation items from pages that opt into the nav.
    """
    items: list[dict[str, object]] = []
    for page in pages:
        if not page.show_in_nav:
            continue
        title = page.nav_title or page.title
        items.append(
            {
                "title": title,
                "url": page.url,
                "order": page.nav_order,
            },
        )
    if extra:
        items.extend(extra)
    items.sort(key=lambda item: (item["order"], str(item["title"]).lower()))
    return items


def build_site(
    config: Config,
    *,
    progress_cb: Optional[Callable[[ProgressEvent], None]] = None,
) -> None:
    """
    Orchestrate the full site build:
    - Discover content (posts and pages)
    - Filter drafts and sort posts
    - Build tag index
    - Render templates for index, posts, pages, and tags
    - Copy static assets
    """

    def emit(stage: Stage, current: int = 0, total: int = 1, message: str = "") -> None:
        if progress_cb is not None:
            progress_cb(ProgressEvent(stage=stage, current=current, total=total, message=message))

    emit(Stage.LOADING_CONFIG, current=0, total=1, message="Loading configuration")

    posts, pages = discover_content(config)

    total_items = len(posts) + len(pages)
    emit(
        Stage.DISCOVERING_CONTENT,
        current=total_items,
        total=total_items or 1,
        message=f"Discovered {len(posts)} posts and {len(pages)} pages",
    )

    # Filter drafts according to configuration.
    include_drafts = bool(config.build.get("include_drafts", False))
    if not include_drafts:
        posts = [p for p in posts if not p.draft]

    # Sort posts by date descending.
    posts = sorted(posts, key=lambda p: p.date, reverse=True)

    # Build tag index.
    tag_index = _build_tag_index(posts)

    # Pagination for the home page.
    posts_per_page = int(config.build.get("posts_per_page", 10)) or 10
    total_pages = max(1, ceil(len(posts) / posts_per_page))

    env = create_environment(config.paths.templates_dir)

    sitemap_cfg = config.sitemap or {}
    sitemap_enabled = bool(sitemap_cfg.get("enabled", False))
    sitemap_include_posts = bool(sitemap_cfg.get("include_posts", True))
    sitemap_include_pages = bool(sitemap_cfg.get("include_pages", True))
    sitemap_include_tags = bool(sitemap_cfg.get("include_tags", True))
    sitemap_include_index = bool(sitemap_cfg.get("include_index", True))
    sitemap_site_url: str | None = None
    sitemap_output_path: Path | None = None
    sitemap_exclude_patterns: Sequence[str] | None = None
    sitemap_entries: list[SitemapEntry] = []

    if sitemap_enabled:
        site_url = str(config.site.get("url", "")).strip()
        if not site_url:
            raise ValueError("sitemap.enabled = true requires site.url to be set")
        sitemap_site_url = site_url

        raw_output = str(sitemap_cfg.get("output", "sitemap.xml") or "sitemap.xml").strip()
        if not raw_output:
            raw_output = "sitemap.xml"
        output_path = Path(raw_output)
        if output_path.is_absolute():
            raise ValueError("sitemap.output must be relative to the output directory")
        if any(part == ".." for part in output_path.parts):
            raise ValueError("sitemap.output cannot traverse outside the output directory")
        if str(output_path) in ("", "."):
            output_path = Path("sitemap.xml")
        sitemap_output_path = config.paths.output_dir / output_path

        raw_excludes = sitemap_cfg.get("exclude_paths")
        if raw_excludes is None:
            sitemap_exclude_patterns = []
        elif isinstance(raw_excludes, (list, tuple)):
            sitemap_exclude_patterns = list(raw_excludes)
        else:
            raise TypeError("sitemap.exclude_paths must be a list of strings")

    def add_sitemap_entry(path: str, lastmod: datetime | None = None) -> None:
        if not sitemap_enabled:
            return
        sitemap_entries.append(SitemapEntry(path=path, lastmod=lastmod))

    search_builder: SearchAssetsBuilder | None = None
    search_nav_extra: list[dict[str, object]] = []
    if bool(config.search.get("enabled", False)):
        search_builder = SearchAssetsBuilder(config)
        search_nav_extra.append(
            {
                "title": "Search",
                "url": search_builder.page_url,
                "order": 0,
                "is_search": True,
            },
        )

    nav_items = _build_nav_items(pages, extra=search_nav_extra if search_nav_extra else None)

    site_context = dict(config.site)
    site_context["sitemap_enabled"] = sitemap_enabled

    base_context: dict[str, object] = {
        "site": site_context,
        "author": config.author,
        "nav_items": nav_items,
        "search_enabled": search_builder is not None,
        "search_url": search_builder.page_url if search_builder else None,
    }

    emit(Stage.RENDERING_TEMPLATES, current=0, total=1, message="Rendering templates")

    # Home and pagination pages.
    for page_number in range(1, total_pages + 1):
        start = (page_number - 1) * posts_per_page
        end = start + posts_per_page
        posts_page = posts[start:end]

        if page_number == 1:
            output_path = config.paths.output_dir / INDEX_FILENAME
            url = "/"
        else:
            output_path = config.paths.output_dir / "page" / str(page_number) / INDEX_FILENAME
            url = f"/page/{page_number}/"

        if page_number > 1:
            prev_url = "/" if page_number == 2 else f"/page/{page_number - 1}/"
        else:
            prev_url = None

        if page_number < total_pages:
            next_url = f"/page/{page_number + 1}/"
        else:
            next_url = None

        context: dict[str, object] = {
            **base_context,
            "posts": posts_page,
            "page_number": page_number,
            "total_pages": total_pages,
            "prev_url": prev_url,
            "next_url": next_url,
            "url": url,
        }
        render_to_file(env, INDEX_FILENAME, context, output_path)

        if sitemap_include_index:
            add_sitemap_entry(url)

    # Individual post pages.
    for post in posts:
        target = config.paths.output_dir / "posts" / post.slug / INDEX_FILENAME
        context = {
            **base_context,
            "post": post,
        }
        render_to_file(env, "post.html", context, target)

        if sitemap_include_posts and not post.draft:
            add_sitemap_entry(post.url, lastmod=post.date)

    # Static pages.
    for page in pages:
        target = config.paths.output_dir / page.slug / INDEX_FILENAME
        context = {
            **base_context,
            "page": page,
        }
        render_to_file(env, "page.html", context, target)

        if sitemap_include_pages:
            add_sitemap_entry(page.url)

    # Tags index and detail pages.
    tags_data: list[dict[str, object]] = []
    for tag_name, posts_for_tag in sorted(tag_index.items(), key=lambda kv: kv[0].lower()):
        tag_slug = _slugify_tag(tag_name)
        tag_url = f"/tags/{tag_slug}/"
        tags_data.append(
            {
                "name": tag_name,
                "slug": tag_slug,
                "url": tag_url,
                "count": len(posts_for_tag),
            },
        )

    # Tags index.
    tags_index_target = config.paths.output_dir / "tags" / INDEX_FILENAME
    render_to_file(
        env,
        "tags.html",
        {**base_context, "tags": tags_data},
        tags_index_target,
    )

    if sitemap_include_tags:
        add_sitemap_entry("/tags/")

    # Tag detail pages.
    for tag_entry in tags_data:
        tag_name = str(tag_entry["name"])
        tag_slug = str(tag_entry["slug"])
        tag_posts = tag_index[tag_name]
        target = config.paths.output_dir / "tags" / tag_slug / INDEX_FILENAME
        context = {
            **base_context,
            "tag": tag_name,
            "tag_slug": tag_slug,
            "posts": tag_posts,
        }
        render_to_file(env, "tag.html", context, target)

        if sitemap_include_tags:
            add_sitemap_entry(tag_entry["url"])

    # RSS/Atom-style feed (RSS 2.0 for now).
    feed_items = int(config.build.get("feed_items", 20)) or 20
    recent_posts = posts[:feed_items]
    feed_target = config.paths.output_dir / "feed.xml"
    feed_context: dict[str, object] = {
        "site": site_context,
        "author": config.author,
        "posts": recent_posts,
    }
    render_to_file(env, "feed.xml", feed_context, feed_target)
    emit(Stage.RENDERING_TEMPLATES, current=1, total=1, message="Rendering feed.xml")

    if search_builder is not None:
        search_builder.build_assets(posts, pages, env, base_context)
        if sitemap_include_pages:
            add_sitemap_entry(search_builder.page_url)

    # Static assets.
    emit(Stage.COPYING_STATIC, current=0, total=1, message="Copying static assets")
    static_dir = config.paths.static_dir
    output_static_dir = config.paths.output_dir / "static"
    copy_static_tree(static_dir, output_static_dir)

    if sitemap_enabled and sitemap_site_url and sitemap_output_path:
        generate_sitemap(
            sitemap_entries,
            site_url=sitemap_site_url,
            output_path=sitemap_output_path,
            exclude_patterns=sitemap_exclude_patterns,
        )

    emit(Stage.DONE, current=1, total=1, message="Build completed")
