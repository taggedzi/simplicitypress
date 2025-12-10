from __future__ import annotations

import re
from math import ceil
from typing import Callable, Optional

from .content import discover_content
from .fs import copy_static_tree
from .models import Config, Post, ProgressEvent, Stage
from .render import create_environment, render_to_file


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

    base_context = {
        "site": config.site,
        "author": config.author,
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

        context = {
            **base_context,
            "posts": posts_page,
            "page_number": page_number,
            "total_pages": total_pages,
            "prev_url": prev_url,
            "next_url": next_url,
            "url": url,
        }
        render_to_file(env, INDEX_FILENAME, context, output_path)

    # Individual post pages.
    for post in posts:
        target = config.paths.output_dir / "posts" / post.slug / INDEX_FILENAME
        context = {
            **base_context,
            "post": post,
        }
        render_to_file(env, "post.html", context, target)

    # Static pages.
    for page in pages:
        target = config.paths.output_dir / page.slug / INDEX_FILENAME
        context = {
            **base_context,
            "page": page,
        }
        render_to_file(env, "page.html", context, target)

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

    # Static assets.
    emit(Stage.COPYING_STATIC, current=0, total=1, message="Copying static assets")
    static_dir = config.paths.static_dir
    output_static_dir = config.paths.output_dir / "static"
    copy_static_tree(static_dir, output_static_dir)

    emit(Stage.DONE, current=1, total=1, message="Build completed")
