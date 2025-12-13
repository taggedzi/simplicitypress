# Static Search Guide

SimplicityPress can generate a fully static search page that works on any host. Everything happens at build time, so you do not need a database, API, or client-side indexing library.

## Enabling Search

In your `site.toml`, add a `[search]` section:

```toml
[search]
enabled = true                   # default: false
output_dir = "assets/search"     # relative to output_dir
page_path = "search/index.html"  # relative to output_dir
```

When `enabled` is false (the default) the build pipeline ignores search entirely and no extra files are written. When true, a themed search page and companion assets are generated automatically.

For convenience, you can copy this full template into `site.toml` and tweak as needed:

```toml
[search]
enabled = false
output_dir = "assets/search"
page_path = "search/index.html"
max_terms_per_doc = 300
min_token_len = 2
drop_df_ratio = 0.70
drop_df_min = 0
weight_body = 1.0
weight_title = 8.0
weight_tags = 6.0
normalize_by_doc_len = true
```

## Output Files

With search enabled, the build emits:

| File | Description |
| --- | --- |
| `assets/search/search_docs.json` | Metadata for each page/post (id, title, excerpt, tags, date, URL). |
| `assets/search/search_terms.json` | Compact inverted index keyed by token → `[doc_id, score]` pairs. |
| `assets/search/search.js` | Lightweight client script that loads both JSON files and handles user queries. |
| `search/index.html` | A search page that matches the scaffold theme, including form + results area. |

You can change `output_dir` or `page_path` if your theme organizes assets differently, provided the paths remain inside `output_dir`.

## Tuning the Index

The `[search]` section also accepts several knobs for fine-tuning relevance and file size:

| Key | Default | Purpose |
| --- | --- | --- |
| `max_terms_per_doc` | `300` | Keep only the top N scoring tokens from each document before inversion. |
| `min_token_len` | `2` | Shorter tokens are dropped during tokenization. |
| `drop_df_ratio` | `0.70` | Drop tokens that appear in ≥ 70% of documents (stop-words). |
| `drop_df_min` | `0` | Drop tokens whose document frequency is ≤ this number if you want to remove rare words too. |
| `weight_body` | `1.0` | Weight for tokens that come from Markdown body text. |
| `weight_title` | `8.0` | Weight for tokens found in titles. |
| `weight_tags` | `6.0` | Weight for tokens derived from tags. |
| `normalize_by_doc_len` | `true` | When true, scores are divided by `sqrt(body_token_count)` so short posts remain competitive with long posts. |

All weights are applied before TF-IDF scoring. Adjust them to emphasize the fields most relevant for your site (e.g., increase `weight_tags` if you use tags heavily).

## Theming

The scaffolded `search.html` extends `base.html`, so custom themes can override the layout, copy, or styling just like any other template. If you ship your own templates, ensure the search page includes:

- A form containing `#sp-search-form` and an input with `#sp-search-input`.
- A container with `#sp-search-results`.
- An inline `window.__SP_SEARCH__` config block that specifies `assetsBase` and `minTokenLength`.
- A `<script src="{{ search_bundle_path }}" defer></script>` tag to load `search.js`.

Those hooks allow the bundled `search.js` to initialize without extra configuration.
