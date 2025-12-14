from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Sequence

from xml.etree.ElementTree import Element, ElementTree, SubElement


@dataclass(frozen=True)
class SitemapEntry:
    """
    Represents a single URL that should be emitted into sitemap.xml.
    """

    path: str
    lastmod: date | datetime | None = None


def generate_sitemap(
    entries: Iterable[SitemapEntry],
    *,
    site_url: str,
    output_path: Path,
    exclude_patterns: Sequence[str] | None = None,
) -> None:
    """
    Generate a sitemap.xml document that includes the provided entries.

    ``site_url`` must be an absolute base URL without a trailing slash.
    """
    base_url = _normalize_site_url(site_url)
    normalized_patterns = _normalize_patterns(exclude_patterns)

    deduped = _deduplicate_entries(entries)
    filtered = [
        entry for entry in deduped if not _is_excluded(entry.path, normalized_patterns)
    ]

    serialized: list[tuple[str, str, str | None]] = []
    for entry in filtered:
        normalized_path = _normalize_path(entry.path)
        loc = _build_absolute_url(base_url, normalized_path)
        lastmod_text = _format_lastmod(entry.lastmod)
        serialized.append((loc, normalized_path, lastmod_text))

    serialized.sort(key=lambda item: item[0])

    root = Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
    for loc, _, lastmod_text in serialized:
        url_el = SubElement(root, "url")
        loc_el = SubElement(url_el, "loc")
        loc_el.text = loc
        if lastmod_text:
            lastmod_el = SubElement(url_el, "lastmod")
            lastmod_el.text = lastmod_text

    tree = ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def _normalize_site_url(raw_value: str) -> str:
    if raw_value is None:
        msg = "site_url is required for sitemap generation"
        raise ValueError(msg)
    text = str(raw_value).strip()
    if not text:
        msg = "site_url is required for sitemap generation"
        raise ValueError(msg)
    normalized = text.rstrip("/")
    if not normalized:
        msg = "site_url must not be the root path"
        raise ValueError(msg)
    return normalized


def _normalize_patterns(patterns: Sequence[str] | None) -> list[str]:
    if not patterns:
        return []
    normalized: list[str] = []
    for pattern in patterns:
        if pattern is None:
            continue
        if not isinstance(pattern, str):
            msg = "sitemap.exclude_paths must be a list of strings"
            raise TypeError(msg)
        text = pattern.strip()
        if text:
            normalized.append(text)
    return normalized


def _deduplicate_entries(entries: Iterable[SitemapEntry]) -> list[SitemapEntry]:
    deduped: dict[str, SitemapEntry] = {}
    for entry in entries:
        path = _normalize_path(entry.path)
        lastmod = entry.lastmod
        existing = deduped.get(path)
        if existing is None:
            deduped[path] = SitemapEntry(path=path, lastmod=lastmod)
            continue
        if existing.lastmod is None and lastmod is not None:
            deduped[path] = SitemapEntry(path=path, lastmod=lastmod)
    return list(deduped.values())


def _normalize_path(raw_path: str) -> str:
    if raw_path is None:
        return "/"
    path = str(raw_path).strip()
    if not path:
        return "/"
    normalized = path.replace("\\", "/")
    if not normalized.startswith("/"):
        normalized = "/" + normalized.lstrip("/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if normalized == "":
        return "/"
    return normalized


def _is_excluded(path: str, patterns: Sequence[str]) -> bool:
    if not patterns:
        return False
    normalized = path.lstrip("/")
    for pattern in patterns:
        normalized_pattern = pattern.lstrip("/")
        if fnmatch(normalized, normalized_pattern):
            return True
    return False


def _build_absolute_url(base_url: str, path: str) -> str:
    if path == "/":
        return f"{base_url}/"
    return f"{base_url}{path}"


def _format_lastmod(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()
