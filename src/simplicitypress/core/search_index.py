from __future__ import annotations

from pathlib import Path, PurePosixPath
from textwrap import dedent
from typing import Mapping, Sequence

from jinja2 import Environment

from .models import Config, Page, Post
from .render import render_to_file

PLACEHOLDER_JS = dedent(
    """\
    (() => {
      const root = document.getElementById("sp-search-root");
      if (root) {
        root.innerHTML = "<p>Search is enabled, but indexing will be available in a future update.</p>";
      } else {
        console.warn("[SimplicityPress] Search placeholder is active without a #sp-search-root element.");
      }
    })();
    """,
)

PLACEHOLDER_MESSAGE = "Search is enabled, but the index will be generated in a future release."


class SearchAssetsBuilder:
    """
    Build-time coordinator for generating search assets.

    For phase 1 this only emits placeholder files when search is enabled.
    """

    __slots__ = ("config", "output_subpath", "page_subpath", "assets_base_url", "page_url")

    def __init__(self, config: Config) -> None:
        search_cfg = config.search or {}
        enabled = bool(search_cfg.get("enabled"))
        if not enabled:
            msg = "SearchAssetsBuilder requires search.enabled = true"
            raise ValueError(msg)

        output_subpath = _sanitize_relative_path(search_cfg.get("output_dir"), default="assets/search")
        page_subpath = _sanitize_relative_path(search_cfg.get("page_path"), default="search/index.html")

        self.config = config
        self.output_subpath = output_subpath
        self.page_subpath = page_subpath
        self.assets_base_url = _path_to_url(output_subpath)
        self.page_url = _page_url_from_path(page_subpath)

    def build_assets(
        self,
        posts: Sequence[Post],
        pages: Sequence[Page],
        env: Environment,
        base_context: Mapping[str, object],
    ) -> None:
        """
        Emit placeholder search assets. Posts and pages arguments are reserved for later phases.
        """
        # Future phases will use posts/pages; keep the parameters to avoid churn.
        _ = posts, pages

        output_dir = self.config.paths.output_dir / self.output_subpath
        output_dir.mkdir(parents=True, exist_ok=True)

        _write_placeholder_js(output_dir / "search.js")

        page_target = self.config.paths.output_dir / self.page_subpath
        context = {
            **base_context,
            "search_assets_base": self.assets_base_url,
            "search_bundle_path": f"{self.assets_base_url}/search.js",
            "search_placeholder_message": PLACEHOLDER_MESSAGE,
        }
        render_to_file(env, "search.html", context, page_target)


def _write_placeholder_js(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(PLACEHOLDER_JS, encoding="utf-8")


def _sanitize_relative_path(raw_value: object, *, default: str) -> Path:
    """
    Normalize a config path so it is safely relative to the output directory.
    """
    text = _coerce_path_string(raw_value, default=default)
    text = text.replace("\\", "/")
    if text.startswith("./"):
        while text.startswith("./"):
            text = text[2:]
    text = text.lstrip("/")
    if not text:
        text = default

    path = PurePosixPath(text)
    if path.is_absolute():
        raise ValueError("Search paths must be relative to the output directory")
    if any(part == ".." for part in path.parts):
        raise ValueError("Search paths cannot traverse outside the output directory")

    normalized = str(path)
    if normalized in ("", "."):
        normalized = default

    return Path(normalized)


def _coerce_path_string(raw_value: object, *, default: str) -> str:
    if raw_value is None:
        return default
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        return stripped or default
    msg = "Search path configuration values must be strings"
    raise TypeError(msg)


def _path_to_url(subpath: Path) -> str:
    posix = subpath.as_posix()
    if posix in ("", "."):
        return "/"
    return "/" + posix.lstrip("/")


def _page_url_from_path(subpath: Path) -> str:
    url = _path_to_url(subpath)
    if url.endswith("index.html"):
        trimmed = url[: -len("index.html")]
        return trimmed or "/"
    return url
