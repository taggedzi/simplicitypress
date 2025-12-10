from __future__ import annotations

from typing import Callable, Optional

from .content import discover_content
from .models import Config, ProgressEvent, Stage


def build_site(
    config: Config,
    *,
    progress_cb: Optional[Callable[[ProgressEvent], None]] = None,
) -> None:
    """
    Orchestrate the site build:
    - Discover content (posts and pages)
    - Filter, sort, and organize metadata
    - Render templates
    - Copy static assets

    In this initial scaffold, emit a couple of fake ProgressEvent
    instances via progress_cb and then return.
    """
    if progress_cb is not None:
        progress_cb(ProgressEvent(stage=Stage.LOADING_CONFIG, current=0, total=1))

    posts, pages = discover_content(config)

    if progress_cb is not None:
        total_items = len(posts) + len(pages)
        message = f"Discovered {len(posts)} posts and {len(pages)} pages"
        progress_cb(
            ProgressEvent(
                stage=Stage.DISCOVERING_CONTENT,
                current=total_items,
                total=total_items or 1,
                message=message,
            ),
        )
        progress_cb(ProgressEvent(stage=Stage.DONE, current=1, total=1))
