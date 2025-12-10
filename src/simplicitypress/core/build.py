from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

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
    # NOTE: The config parameter is currently unused, but kept to
    # establish the public API surface for future implementation.
    if progress_cb is not None:
        progress_cb(ProgressEvent(stage=Stage.LOADING_CONFIG, current=0, total=1))
        progress_cb(ProgressEvent(stage=Stage.DONE, current=1, total=1))

