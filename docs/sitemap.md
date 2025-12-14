# 🗺️ Sitemap Support

SimplicityPress can emit a standards-compliant `sitemap.xml` so crawlers can
find every public page you publish. Generation is **off by default** and
produces no files unless explicitly enabled.

## Enable the sitemap

Set a canonical site URL (protocol + host, optional sub-path) and turn on the
feature in `site.toml`:

```toml
[site]
title = "Example"
url = "https://example.com"

[sitemap]
enabled = true
output = "sitemap.xml"      # relative to output_dir
include_index = true        # home + pagination
include_posts = true        # /posts/<slug>/
include_pages = true        # content pages + search.html (if enabled)
include_tags = true         # /tags/ and per-tag detail pages
exclude_paths = []          # optional glob-style filters
```

If `sitemap.enabled = true` but `site.url` is empty, the build fails fast with a
clear error. Disabling the feature restores the old behavior—no `sitemap.xml`
is emitted and the build output is unchanged.

## What gets listed?

- Home page + pagination URLs (`/page/2/`, etc.) when `include_index` is true.
- Every published post that is not marked as a draft.
- Every Markdown page under `content/pages`.
- Tag pages (`/tags/` and `/tags/<slug>/`) when `include_tags` is true.
- The static search page if search is enabled (counts as a “page”).

Entries are sorted by final URL for deterministic diffs. Posts include a
`<lastmod>` tag using the post’s date (`YYYY-MM-DD`). Pages without a reliable
timestamp simply omit `<lastmod>`.

## Filtering unwanted paths

Use `sitemap.exclude_paths` to drop generated URLs that do not belong in the
sitemap—preview sections, draft sandboxes, etc.

```
exclude_paths = [
  "posts/drafts/*",
  "tags/secret/*",
]
```

Patterns are matched against the output path (no leading slash) with basic glob
rules (`*`, `?`, etc.).

## Output location & templates

`output` controls where the XML is written relative to your `output_dir`. The
default theme links to `/sitemap.xml` from the footer, guarded by the runtime
flag `site.sitemap_enabled`. If you move the file elsewhere, update your
templates to point at the new path or hide the footer link.
