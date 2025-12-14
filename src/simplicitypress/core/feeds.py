# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree.ElementTree import Element, SubElement, ElementTree
import html
import re

from .models import Page, Post


@dataclass(frozen=True)
class FeedSettings:
    """
    Normalized feed configuration values with resolved output paths.
    """

    rss_output: Path | None
    atom_output: Path | None
    rss_href: str | None
    atom_href: str | None
    max_items: int
    include_posts: bool
    include_pages: bool
    include_drafts: bool
    include_tags: set[str]
    summary_mode: str
    summary_max_chars: int
    site_url: str


@dataclass(frozen=True)
class FeedEntry:
    """
    Representation of a single feed entry ready for serialization.
    """

    title: str
    url: str
    guid: str
    summary: str | None
    published: datetime
    updated: datetime | None


class FeedConfigError(ValueError):
    """
    Raised when feed configuration values are invalid.
    """


def _strip_html(value: str) -> str:
    """
    Remove markup tags and collapse whitespace into single spaces.
    """
    text = re.sub(r"<[^>]+>", "", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _truncate(value: str, max_chars: int) -> str:
    """
    Truncate value to ``max_chars`` characters, appending ``...`` if needed.
    """
    if len(value) <= max_chars:
        return value
    truncated = value[: max(0, max_chars - 3)].rstrip()
    return f"{truncated}..."


def _ensure_datetime(value: datetime) -> datetime:
    """
    Normalize datetime values to UTC with timezone information.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_rfc3339(value: datetime) -> str:
    """
    Format datetime in RFC 3339 (ISO-8601) with UTC timezone.
    """
    normalized = _ensure_datetime(value)
    return normalized.isoformat().replace("+00:00", "Z")


def _format_rfc2822(value: datetime) -> str:
    """
    Format datetime in RFC 2822 format for RSS ``pubDate``.
    """
    normalized = _ensure_datetime(value)
    return format_datetime(normalized, usegmt=True)


def _ensure_relative_output(raw_value: str, *, label: str) -> Path:
    """
    Validate that the provided path is relative and does not escape the output dir.
    """
    candidate = Path(raw_value.strip() or "")
    if str(candidate) in ("", "."):
        raise FeedConfigError(f"{label} cannot be empty")
    if candidate.is_absolute():
        raise FeedConfigError(f"{label} must be relative to the output directory")
    if any(part == ".." for part in candidate.parts):
        raise FeedConfigError(f"{label} cannot traverse outside the output directory")
    return candidate


def resolve_feed_settings(
    feeds_cfg: Mapping[str, Any],
    *,
    output_dir: Path,
    site_url: str,
) -> FeedSettings | None:
    """
    Normalize the feeds configuration block and return resolved paths.
    """
    enabled = bool(feeds_cfg.get("enabled", False))
    if not enabled:
        return None

    site_url = site_url.strip()
    if not site_url:
        raise FeedConfigError("feeds.enabled = true requires site.url to be set")
    site_url = site_url.rstrip("/")

    rss_enabled = bool(feeds_cfg.get("rss_enabled", True))
    atom_enabled = bool(feeds_cfg.get("atom_enabled", True))
    if not rss_enabled and not atom_enabled:
        raise FeedConfigError("At least one of feeds.rss_enabled or feeds.atom_enabled must be true")

    rss_output: Path | None = None
    atom_output: Path | None = None
    rss_href: str | None = None
    atom_href: str | None = None

    if rss_enabled:
        rss_raw = str(feeds_cfg.get("rss_output", "rss.xml") or "rss.xml")
        rel_path = _ensure_relative_output(rss_raw, label="feeds.rss_output")
        rss_output = (output_dir / rel_path).resolve()
        rss_href = f"/{rel_path.as_posix()}"
    if atom_enabled:
        atom_raw = str(feeds_cfg.get("atom_output", "atom.xml") or "atom.xml")
        rel_path = _ensure_relative_output(atom_raw, label="feeds.atom_output")
        atom_output = (output_dir / rel_path).resolve()
        atom_href = f"/{rel_path.as_posix()}"

    max_items_raw = feeds_cfg.get("max_items", 20)
    try:
        max_items = int(max_items_raw)
    except (TypeError, ValueError) as exc:
        raise FeedConfigError("feeds.max_items must be an integer") from exc
    if max_items <= 0:
        raise FeedConfigError("feeds.max_items must be greater than zero")

    include_posts = bool(feeds_cfg.get("include_posts", True))
    include_pages = bool(feeds_cfg.get("include_pages", False))
    include_drafts = bool(feeds_cfg.get("include_drafts", False))

    raw_tags = feeds_cfg.get("include_tags", [])
    if raw_tags is None:
        include_tags: set[str] = set()
    elif isinstance(raw_tags, (list, tuple, set)):
        include_tags = {str(tag) for tag in raw_tags}
    else:
        raise FeedConfigError("feeds.include_tags must be a list of strings")

    summary_cfg_raw = feeds_cfg.get("summary", {}) or {}
    if not isinstance(summary_cfg_raw, Mapping):
        raise FeedConfigError("feeds.summary must be a mapping")
    summary_cfg: Mapping[str, Any] = summary_cfg_raw
    summary_mode = str(summary_cfg.get("mode", "excerpt")).strip().lower()
    if summary_mode not in {"excerpt", "text"}:
        raise FeedConfigError("feeds.summary.mode must be 'excerpt' or 'text'")

    summary_max_raw = summary_cfg.get("max_chars", 240)
    try:
        summary_max_chars = int(summary_max_raw)
    except (TypeError, ValueError) as exc:
        raise FeedConfigError("feeds.summary.max_chars must be an integer") from exc
    if summary_max_chars <= 0:
        raise FeedConfigError("feeds.summary.max_chars must be greater than zero")

    return FeedSettings(
        rss_output=rss_output,
        atom_output=atom_output,
        rss_href=rss_href,
        atom_href=atom_href,
        max_items=max_items,
        include_posts=include_posts,
        include_pages=include_pages,
        include_drafts=include_drafts,
        include_tags=include_tags,
        summary_mode=summary_mode,
        summary_max_chars=summary_max_chars,
        site_url=site_url,
    )


def _post_summary(post: Post, *, summary_mode: str, max_chars: int) -> str | None:
    if summary_mode == "excerpt":
        summary = post.summary or ""
        summary = summary.strip()
    else:
        summary = _strip_html(post.content_html) or post.summary
    if not summary:
        return None
    return _truncate(summary.strip(), max_chars)


def _page_summary(page: Page, *, max_chars: int) -> str | None:
    return _truncate(_strip_html(page.content_html), max_chars) if page.content_html else None


def _collect_entries(
    *,
    settings: FeedSettings,
    posts: Sequence[Post],
    pages: Sequence[Page],
) -> list[FeedEntry]:
    site_url = settings.site_url
    entries: list[FeedEntry] = []

    def to_absolute(url: str) -> str:
        return f"{site_url}{url}"

    if settings.include_posts:
        for post in posts:
            if post.draft and not settings.include_drafts:
                continue
            if settings.include_tags:
                if not any(tag in settings.include_tags for tag in post.tags):
                    continue
            abs_url = to_absolute(post.url)
            summary = _post_summary(
                post,
                summary_mode=settings.summary_mode,
                max_chars=settings.summary_max_chars,
            )
            entries.append(
                FeedEntry(
                    title=post.title,
                    url=abs_url,
                    guid=abs_url,
                    summary=summary,
                    published=post.date,
                    updated=post.date,
                ),
            )

    if settings.include_pages:
        for page in pages:
            if page.date is None:
                continue
            abs_url = to_absolute(page.url)
            summary = _page_summary(page, max_chars=settings.summary_max_chars)
            entries.append(
                FeedEntry(
                    title=page.title,
                    url=abs_url,
                    guid=abs_url,
                    summary=summary,
                    published=page.date,
                    updated=page.date,
                ),
            )

    entries.sort(key=lambda e: (e.published, e.url), reverse=True)
    return entries[: settings.max_items]


def _write_rss(
    *,
    entries: Sequence[FeedEntry],
    settings: FeedSettings,
    site: Mapping[str, object],
    author: Mapping[str, object],
) -> None:
    channel = Element("channel")
    title = str(site.get("title") or "SimplicityPress Site")
    subtitle = str(site.get("subtitle") or title)
    SubElement(channel, "title").text = title
    SubElement(channel, "description").text = subtitle
    SubElement(channel, "link").text = settings.site_url
    language = str(site.get("language") or "en")
    SubElement(channel, "language").text = language

    if author.get("email"):
        email = str(author.get("email"))
        name = str(author.get("name") or title)
        SubElement(channel, "managingEditor").text = f"{email} ({name})"

    for entry in entries:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = entry.title
        SubElement(item, "link").text = entry.url
        SubElement(item, "guid").text = entry.guid
        SubElement(item, "pubDate").text = _format_rfc2822(entry.published)
        if entry.summary:
            SubElement(item, "description").text = entry.summary

    rss_root = Element("rss", {"version": "2.0"})
    rss_root.append(channel)

    tree = ElementTree(rss_root)
    if settings.rss_output is None:
        raise FeedConfigError("RSS output path not resolved")
    settings.rss_output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(settings.rss_output, encoding="utf-8", xml_declaration=True)


def _write_atom(
    *,
    entries: Sequence[FeedEntry],
    settings: FeedSettings,
    site: Mapping[str, object],
    author: Mapping[str, object],
) -> None:
    ns = "http://www.w3.org/2005/Atom"
    feed_el = Element("feed", {"xmlns": ns})
    title = str(site.get("title") or "SimplicityPress Site")
    subtitle = str(site.get("subtitle") or title)
    SubElement(feed_el, "title").text = title
    SubElement(feed_el, "subtitle").text = subtitle
    SubElement(feed_el, "id").text = settings.site_url

    updated = entries[0].updated if entries else None
    if updated is None:
        updated_value = datetime(1970, 1, 1, tzinfo=timezone.utc)
    else:
        updated_value = updated
    SubElement(feed_el, "updated").text = _format_rfc3339(updated_value)

    SubElement(feed_el, "link", {"rel": "alternate", "href": settings.site_url})
    if settings.atom_href:
        SubElement(
            feed_el,
            "link",
            {
                "rel": "self",
                "href": f"{settings.site_url}{settings.atom_href}",
            },
        )

    if author.get("name"):
        author_el = SubElement(feed_el, "author")
        SubElement(author_el, "name").text = str(author.get("name"))
        if author.get("email"):
            SubElement(author_el, "email").text = str(author.get("email"))

    language = str(site.get("language") or "en")
    feed_el.set("{http://www.w3.org/XML/1998/namespace}lang", language)

    for entry in entries:
        entry_el = SubElement(feed_el, "entry")
        SubElement(entry_el, "title").text = entry.title
        SubElement(entry_el, "id").text = entry.guid
        SubElement(entry_el, "link", {"href": entry.url})
        SubElement(entry_el, "published").text = _format_rfc3339(entry.published)
        SubElement(entry_el, "updated").text = _format_rfc3339(entry.updated or entry.published)
        if entry.summary:
            summary_el = SubElement(entry_el, "summary", {"type": "html"})
            summary_el.text = entry.summary

    tree = ElementTree(feed_el)
    if settings.atom_output is None:
        raise FeedConfigError("Atom output path not resolved")
    settings.atom_output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(settings.atom_output, encoding="utf-8", xml_declaration=True)


def generate_feeds(
    *,
    settings: FeedSettings,
    posts: Sequence[Post],
    pages: Sequence[Page],
    site: Mapping[str, object],
    author: Mapping[str, object],
) -> None:
    """
    Generate RSS and Atom feeds according to the provided settings.
    """
    entries = _collect_entries(settings=settings, posts=posts, pages=pages)

    if settings.rss_output is not None:
        _write_rss(entries=entries, settings=settings, site=site, author=author)
    if settings.atom_output is not None:
        _write_atom(entries=entries, settings=settings, site=site, author=author)
