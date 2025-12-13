from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import re
from pathlib import Path, PurePosixPath
from textwrap import dedent
from typing import Mapping, Sequence

from jinja2 import Environment

from .models import Config, Page, Post
from .render import render_to_file

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
WHITESPACE_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"<[^>]+>")

SEARCH_APP_JS = dedent(
    """\
    (() => {
      const TOKEN_RE = /[A-Za-z0-9]+/g;

      function normalizeBase(value) {
        if (!value) {
          return "";
        }
        let base = value.trim();
        if (!base.startsWith("/")) {
          base = "/" + base;
        }
        base = base.replace(/\\/+/g, "/");
        if (base.endsWith("/")) {
          base = base.slice(0, -1);
        }
        if (base === "/") {
          return "";
        }
        return base;
      }

      function assetUrl(base, filename) {
        if (!base) {
          return `/${filename}`;
        }
        return `${base}/${filename}`;
      }

      function fetchJson(url) {
        return fetch(url, { cache: "no-cache" }).then((resp) => {
          if (!resp.ok) {
            throw new Error(`Failed to load ${url}: ${resp.status}`);
          }
          return resp.json();
        });
      }

      function tokenize(text, minLength) {
        if (!text) {
          return [];
        }
        const matches = text.toLowerCase().match(TOKEN_RE);
        if (!matches) {
          return [];
        }
        return matches.filter((token) => token.length >= minLength);
      }

      function escapeHtml(text) {
        return text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }

      function renderMessage(container, message) {
        container.innerHTML = `<p>${escapeHtml(message)}</p>`;
      }

      const config = window.__SP_SEARCH__ || {};
      const assetsBase = normalizeBase(config.assetsBase || "/assets/search");
      const minTokenLength = Number(config.minTokenLength) || 2;
      const docsUrl = assetUrl(assetsBase, "search_docs.json");
      const termsUrl = assetUrl(assetsBase, "search_terms.json");

      const input = document.getElementById("sp-search-input");
      const form = document.getElementById("sp-search-form");
      const resultsContainer = document.getElementById("sp-search-results");

      if (!input || !form || !resultsContainer) {
        console.warn("[SimplicityPress] Search UI elements are missing.");
        return;
      }

      let docsData = null;
      let docsById = new Map();
      let termsIndex = null;
      let ready = false;

      renderMessage(resultsContainer, "Loading search index...");

      Promise.all([fetchJson(docsUrl), fetchJson(termsUrl)])
        .then(([docs, terms]) => {
          docsData = docs;
          docsById = new Map();
          for (const doc of docs.docs || []) {
            docsById.set(doc.id, doc);
          }
          termsIndex = terms;
          ready = true;
          renderMessage(resultsContainer, "Enter a search query to see results.");
        })
        .catch((error) => {
          console.error("[SimplicityPress] Failed to load search index", error);
          renderMessage(resultsContainer, "Search index failed to load.");
        });

      function renderResults(entries) {
        if (!entries.length) {
          renderMessage(resultsContainer, "No matches found.");
          return;
        }
        const list = document.createElement("ul");
        list.className = "sp-search-results-list";
        entries.slice(0, 20).forEach((entry) => {
          if (!entry.doc) {
            return;
          }
          const item = document.createElement("li");
          item.className = "sp-search-result";

          const link = document.createElement("a");
          link.href = entry.doc.url;
          link.textContent = entry.doc.title;
          link.className = "sp-search-result-link";

          const excerpt = document.createElement("p");
          excerpt.textContent = entry.doc.excerpt || "";
          excerpt.className = "sp-search-result-excerpt";

          item.appendChild(link);
          if (entry.doc.excerpt) {
            item.appendChild(excerpt);
          }
          list.appendChild(item);
        });

        resultsContainer.innerHTML = "";
        resultsContainer.appendChild(list);
      }

      function runSearch(query) {
        if (!ready || !termsIndex) {
          renderMessage(resultsContainer, "Search index is still loading...");
          return;
        }
        const tokens = tokenize(query, minTokenLength);
        if (!tokens.length) {
          renderMessage(resultsContainer, "Enter a search query to see results.");
          return;
        }

        const scores = new Map();
        tokens.forEach((token) => {
          const postings = termsIndex[token];
          if (!postings) {
            return;
          }
          postings.forEach(([docId, value]) => {
            const current = scores.get(docId) || 0;
            scores.set(docId, current + value);
          });
        });

        const entries = Array.from(scores.entries())
          .map(([docId, score]) => ({ doc: docsById.get(docId), score }))
          .filter((entry) => entry.doc)
          .sort((a, b) => {
            if (b.score === a.score) {
              return a.doc.id - b.doc.id;
            }
            return b.score - a.score;
          });

        renderResults(entries);
      }

      form.addEventListener("submit", (event) => {
        event.preventDefault();
        runSearch(input.value);
      });

      input.addEventListener("input", () => {
        runSearch(input.value);
      });
    })();
    """,
)


@dataclass(slots=True)
class SearchSettings:
    max_terms_per_doc: int
    min_token_len: int
    drop_df_ratio: float
    drop_df_min: int
    weight_body: float
    weight_title: float
    weight_tags: float
    normalize_by_doc_len: bool
    version: int = 1

    @classmethod
    def from_config(cls, cfg: Mapping[str, object]) -> SearchSettings:
        def _float(key: str, default: float) -> float:
            try:
                return float(cfg.get(key, default))
            except (TypeError, ValueError):
                return default

        def _int(key: str, default: int, *, minimum: int | None = None) -> int:
            try:
                value = int(cfg.get(key, default))
            except (TypeError, ValueError):
                value = default
            if minimum is not None:
                value = max(minimum, value)
            return value

        max_terms = _int("max_terms_per_doc", 300, minimum=1)
        min_len = _int("min_token_len", 2, minimum=1)
        drop_ratio_raw = _float("drop_df_ratio", 0.70)
        drop_ratio = min(max(drop_ratio_raw, 0.0), 1.0)
        drop_min = max(0, _int("drop_df_min", 0, minimum=0))

        return cls(
            max_terms_per_doc=max_terms,
            min_token_len=min_len,
            drop_df_ratio=drop_ratio,
            drop_df_min=drop_min,
            weight_body=_float("weight_body", 1.0),
            weight_title=_float("weight_title", 8.0),
            weight_tags=_float("weight_tags", 6.0),
            normalize_by_doc_len=bool(cfg.get("normalize_by_doc_len", True)),
        )


@dataclass(slots=True)
class SearchDocument:
    id: int
    url: str
    title: str
    tags: list[str]
    date: str | None
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "tags": self.tags,
            "date": self.date,
            "excerpt": self.excerpt,
        }


@dataclass(slots=True)
class DocumentRecord:
    document: SearchDocument
    token_weights: dict[str, float]
    body_token_count: int


class SearchAssetsBuilder:
    """
    Build-time coordinator for generating search assets (docs, term index, JS bundle, page).
    """

    __slots__ = (
        "config",
        "output_subpath",
        "page_subpath",
        "assets_base_url",
        "page_url",
        "_settings",
    )

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
        self._settings = SearchSettings.from_config(search_cfg)

    def build_assets(
        self,
        posts: Sequence[Post],
        pages: Sequence[Page],
        env: Environment,
        base_context: Mapping[str, object],
    ) -> None:
        """
        Emit search metadata, inverted index JSON, and the search page/assets.
        """
        output_dir = self.config.paths.output_dir / self.output_subpath
        output_dir.mkdir(parents=True, exist_ok=True)

        records = self._collect_documents(posts, pages)
        docs_payload = self._build_docs_payload(records)
        terms_payload = _build_terms_index(records, self._settings)

        _write_json(output_dir / "search_docs.json", docs_payload)
        _write_json(output_dir / "search_terms.json", terms_payload)
        _write_search_js(output_dir / "search.js")

        page_target = self.config.paths.output_dir / self.page_subpath
        context = {
            **base_context,
            "search_assets_base": self.assets_base_url,
            "search_bundle_path": f"{self.assets_base_url}/search.js",
            "search_min_token_len": self._settings.min_token_len,
        }
        render_to_file(env, "search.html", context, page_target)

    def _collect_documents(self, posts: Sequence[Post], pages: Sequence[Page]) -> list[DocumentRecord]:
        records: list[DocumentRecord] = []
        next_id = 0
        settings = self._settings

        for post in posts:
            body_text = _html_to_text(post.content_html)
            summary_source = post.summary or body_text
            excerpt = _normalize_excerpt(_html_to_text(summary_source), limit=200)
            doc = SearchDocument(
                id=next_id,
                url=post.url,
                title=post.title,
                tags=post.tags,
                date=post.date.date().isoformat(),
                excerpt=excerpt,
            )
            token_weights, body_count = _collect_token_weights(post.title, post.tags, body_text, settings)
            records.append(
                DocumentRecord(document=doc, token_weights=token_weights, body_token_count=body_count),
            )
            next_id += 1

        sorted_pages = sorted(pages, key=lambda page: (page.slug, page.title.lower()))
        for page in sorted_pages:
            body_text = _html_to_text(page.content_html)
            excerpt = _normalize_excerpt(body_text, limit=200)
            doc = SearchDocument(
                id=next_id,
                url=page.url,
                title=page.title,
                tags=[],
                date=None,
                excerpt=excerpt,
            )
            token_weights, body_count = _collect_token_weights(page.title, [], body_text, settings)
            records.append(
                DocumentRecord(document=doc, token_weights=token_weights, body_token_count=body_count),
            )
            next_id += 1

        return records

    def _build_docs_payload(self, records: Sequence[DocumentRecord]) -> dict[str, object]:
        generated_at = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        docs_list = [record.document.to_dict() for record in records]
        return {
            "version": self._settings.version,
            "generated_at": generated_at,
            "doc_count": len(docs_list),
            "docs": docs_list,
        }


def tokenize_text(text: str, min_len: int) -> list[str]:
    """
    Tokenize text by extracting alphanumeric sequences and applying a minimum length filter.
    """
    if not text:
        return []
    tokens = TOKEN_RE.findall(text.lower())
    return [token for token in tokens if len(token) >= min_len]


def _collect_token_weights(
    title: str,
    tags: Sequence[str],
    body_text: str,
    settings: SearchSettings,
) -> tuple[dict[str, float], int]:
    weights: dict[str, float] = {}

    body_tokens = tokenize_text(body_text, settings.min_token_len)
    body_counts = Counter(body_tokens)
    body_token_count = sum(body_counts.values())
    for token, count in body_counts.items():
        weights[token] = weights.get(token, 0.0) + count * settings.weight_body

    title_counts = Counter(tokenize_text(title, settings.min_token_len))
    for token, count in title_counts.items():
        weights[token] = weights.get(token, 0.0) + count * settings.weight_title

    tag_counts: Counter[str] = Counter()
    for tag in tags:
        tag_counts.update(tokenize_text(tag, settings.min_token_len))

    for token, count in tag_counts.items():
        weights[token] = weights.get(token, 0.0) + count * settings.weight_tags

    return weights, body_token_count


def _build_terms_index(records: Sequence[DocumentRecord], settings: SearchSettings) -> dict[str, list[list[float | int]]]:
    doc_count = len(records)
    if doc_count == 0:
        return {}

    df_counter: Counter[str] = Counter()
    for record in records:
        df_counter.update(record.token_weights.keys())

    terms: dict[str, list[tuple[int, float]]] = {}
    for record in records:
        scored_tokens = _score_document_tokens(
            record.token_weights,
            df_counter,
            doc_count,
            settings.max_terms_per_doc,
            record.body_token_count,
            settings,
        )
        for token, score in scored_tokens:
            terms.setdefault(token, []).append((record.document.id, score))

    ordered: dict[str, list[list[float | int]]] = {}
    for token in sorted(terms.keys()):
        postings = terms[token]
        postings.sort(key=lambda item: (-item[1], item[0]))
        ordered[token] = [[doc_id, round(score, 6)] for doc_id, score in postings]

    return ordered


def _score_document_tokens(
    token_weights: Mapping[str, float],
    df_counter: Mapping[str, int],
    doc_count: int,
    max_terms: int,
    body_token_count: int,
    settings: SearchSettings,
) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for token, weight in token_weights.items():
        if weight <= 0:
            continue
        df = df_counter.get(token, 0)
        if should_drop_token(df, doc_count, settings):
            continue
        tf = 1.0 + math.log(weight)
        idf = math.log((doc_count + 1) / (df + 1)) + 1.0
        score = tf * idf
        if settings.normalize_by_doc_len and body_token_count > 0:
            score /= math.sqrt(body_token_count)
        scored.append((token, score))

    scored.sort(key=lambda item: (-item[1], item[0]))
    if len(scored) > max_terms:
        return scored[:max_terms]
    return scored


def should_drop_token(df: int, doc_count: int, settings: SearchSettings) -> bool:
    if df <= 0:
        return settings.drop_df_min > 0
    if doc_count <= 0:
        return True
    if df <= settings.drop_df_min:
        return True
    if df == doc_count:
        return True
    ratio = df / doc_count
    if ratio >= settings.drop_df_ratio:
        return True
    return False


def _normalize_excerpt(text: str, *, limit: int) -> str:
    cleaned = WHITESPACE_RE.sub(" ", text or "").strip()
    if len(cleaned) > limit:
        trimmed = cleaned[:limit].rstrip()
        if not trimmed.endswith("..."):
            trimmed = f"{trimmed}..."
        return trimmed
    return cleaned


def _html_to_text(html: str) -> str:
    without_tags = TAG_RE.sub(" ", html or "")
    return WHITESPACE_RE.sub(" ", without_tags).strip()


def _write_json(target: Path, payload: Mapping[str, object]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    target.write_text(serialized, encoding="utf-8")


def _write_search_js(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SEARCH_APP_JS, encoding="utf-8")


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
