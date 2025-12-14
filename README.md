# SimplicityPress

<!-- Badges -->
[![CI](https://github.com/taggedzi/simplicitypress/actions/workflows/ci.yml/badge.svg)](https://github.com/taggedzi/simplicitypress/actions/workflows/ci.yml) [![Release](https://github.com/taggedzi/simplicitypress/actions/workflows/release.yml/badge.svg)](https://github.com/taggedzi/simplicitypress/actions/workflows/release.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/) [![Ruff lint](https://img.shields.io/badge/lint%20with-ruff-informational)](https://github.com/astral-sh/ruff) [![Mypy](https://img.shields.io/badge/type%20checking-mypy-informational)](https://mypy-lang.org/) [![Issues](https://img.shields.io/github/issues/taggedzi/simplicitypress.svg)](https://github.com/taggedzi/simplicitypress/issues) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/taggedzi/simplicitypress/pulls)

SimplicityPress is a **minimal, library-first static site generator** designed for people who want a clean, predictable Markdown → HTML workflow without the complexity of full CMS platforms or heavyweight SSG ecosystems.

If your needs are simple - posts, pages, tags, basic navigation, and clean output - SimplicityPress gives you a lightweight, transparent tool that is easy to understand, customize, and automate.

## ✨ What does SimplicityPress do?

- Converts **Markdown files** into static HTML pages using Jinja2 templates.
- Supports:
  - **Blog posts** (with dates, tags, summaries)
  - **Static pages** (About, Contact, FAQ, Projects…)
  - **Optional top navigation for pages**
  - **Optional sitemap.xml output** (disabled by default)
  - **Automatic tag index and tag detail pages**
  - **Pagination** for large post archives
- Outputs simple, portable HTML you can host anywhere:
  - GitHub Pages  
  - Netlify  
  - Cloudflare Pages  
  - A static web server  
- Ships with a **working default theme** so you can publish immediately.
- Includes a **local development server** for previewing builds.
- Optional **fully static search** that runs entirely in the browser (no backend).
- Optional **RSS + Atom feeds** with configurable scopes and output paths.
- Written to be **library-first**, so you can:
  - Integrate it into other Python applications
  - Wrap it with a GUI (future feature)
  - Script builds programmatically

If you want a system that’s powerful enough to build a clean blog or microsite, yet simple enough to fully understand, SimplicityPress aims to be the perfect middle ground.

---

## 🚀 Quick Start

Install in editable mode:

```bash
python -m pip install -e .
```

Create a new site:

```bash
simplicitypress init --site-root test-site
```

Build the site:

```bash
simplicitypress build --site-root test-site
```

Serve it locally:

```bash
simplicitypress serve --site-root test-site --port 8000
```

## 🔍 Static Search

SimplicityPress ships an optional, fully static search experience. When enabled, the build emits a search page plus three small artifacts:

- `assets/search/search_docs.json` – document metadata for rendering results
- `assets/search/search_terms.json` – a compact inverted index
- `assets/search/search.js` – the browser-side search engine

Enable it in `site.toml`:

```toml
[search]
enabled = true
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

Fine-tune the index with these keys:

| Key | Description |
| --- | --- |
| `max_terms_per_doc` | Keep only the top N tokens per document (default `300`). |
| `min_token_len` | Minimum token length (default `2`). |
| `drop_df_ratio` / `drop_df_min` | Drop tokens that appear in too many (`ratio`) or too few (`min`) documents. |
| `weight_body`, `weight_title`, `weight_tags` | Control how much each field contributes before TF-IDF scoring. |
| `normalize_by_doc_len` | When `true`, divide scores by `sqrt(body_token_count)` so short/long posts are comparable. |

See `docs/static_search.md` or `docs/search_spec.md` for a deeper walkthrough.

## 🗺️ Sitemap

Prefer crawlable archives? Enable the optional sitemap builder to emit a static
`sitemap.xml` alongside the rest of your output. Just provide a canonical site
URL and flip the feature switch:

```toml
[site]
url = "https://example.com"

[sitemap]
enabled = true
output = "sitemap.xml"
include_index = true
include_posts = true
include_pages = true
include_tags = true
```

The sitemap lists every published post, page, tag view, and search page (when
enabled), sorted for stable diffs. Drafts are automatically skipped, and the
default theme exposes a footer link when the feature is on. See `docs/sitemap.md`
for full configuration details, including exclusion globs and custom output
paths.

## 📣 Feeds

Ship RSS 2.0 and Atom 1.0 feeds for your readers. Feeds are disabled by
default, require a canonical `site.url`, and only include posts unless you opt
into pages.

```toml
[site]
url = "https://example.com"

[feeds]
enabled = true
rss_enabled = true
atom_enabled = true
max_items = 20
include_posts = true
include_pages = false
include_tags = []
[feeds.summary]
mode = "excerpt"
max_chars = 240
```

Additional knobs let you adjust output filenames, include drafts, or filter to
specific tags. The default theme automatically adds `<link rel="alternate">`
tags plus footer links when feeds are enabled. See `docs/feeds.md` for all
options and examples.

Build with overrides:

```bash
simplicitypress build --site-root test-site --output test-site/public --include-drafts
```

Serve a custom output directory without rebuilding:

```bash
simplicitypress serve --site-root test-site --output test-site/public --no-build
```

---

## 📄 Pages

SimplicityPress treats **pages** as standalone, non-blog content - perfect for:

- About
- Contact
- Projects
- FAQ
- Resume
- Privacy Policy

Pages live under:

```bash
content/pages/
```

Each page uses Markdown with TOML front matter. At minimum, pages require a `title`:

```markdown
+++
title = "About"
slug = "about"          # optional; defaults to filename
show_in_nav = true      # optional; add this page to the top navigation
nav_title = "About"     # optional; label shown in navigation
nav_order = 10          # optional; lower numbers appear earlier
+++

This is the **About** page body.
```

**Fields:**

- `title` *(required)*
  Human-readable title.

- `slug` *(optional)*
  Defaults to filename (`about` → `/about/`).

- `show_in_nav` *(optional)*
  Adds this page to the top navigation bar.

- `nav_title` *(optional)*
  Override display label in navigation.

- `nav_order` *(optional)*
  Controls global nav ordering (lower = earlier).
- `date` *(optional)*
  Provide a publish timestamp if you plan to include pages in feeds.

Output:

- URL → `/<slug>/`
- File → `output/<slug>/index.html`

---

## 📝 Posts

Posts appear on the blog index and support dates, tags, summaries, and optional cover images.

Posts live under:

```bash
content/posts/
```

Example:

```markdown
+++
title = "My First Post"
date = "2025-12-10"
slug = "my-first-post"
tags = ["meta", "intro"]
draft = false
summary = "A short teaser."
cover_image = "/static/img/posts/first-cover.jpg"
cover_alt = "Abstract purple shapes"
+++

This is the **post body**, written in Markdown.
```

**Post features:**

- Must include a `date`.
- Casually support tags → generate:

  - `/tags/`
  - `/tags/<tag>/`
- Appear in:

  - Home page
  - Pagination pages
  - Tag listings

Output:

- URL → `/posts/<slug>/`
- File → `output/posts/<slug>/index.html`

---

## 🧭 Navigation

The default theme includes:

- **Home** (`/`)
- **Tags** (`/tags/`)
- Any **pages that opt in** with `show_in_nav = true`

Navigation is intentionally simple - no dropdowns or multi-level menus.

To include a page:

```toml
show_in_nav = true
nav_title = "About"
nav_order = 10
```

After building, navigation might look like:

```html
<nav>
  <a href="/">Home</a>
  <a href="/tags/">Tags</a>
  <a href="/about/">About</a>
  <a href="/contact/">Contact</a>
</nav>
```

Pages without `show_in_nav = true` remain accessible but unlisted.

---

## 📚 Documentation

See the `docs/` directory for in-depth guides:

- Theme API & stability
- Template variables & context
- Writing templates from scratch
- SPDX header policy (`docs/spdx.md`)
- CycloneDX SBOM generation (`docs/sbom.md`)
- Release workflow & changelog automation (`docs/release.md`)

---

## 📦 Licensing

- **SimplicityPress** is licensed under the **MIT License**.  
  See the [`LICENSE`](./LICENSE) file in the repository root.

- SimplicityPress depends on third-party libraries which may be licensed under different terms
  (for example, **PySide6**, which is available under the **LGPL**).  
  See the [`LICENSES/`](./LICENSES/) directory for third-party license notices.

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to get involved, coding standards, and contribution guidelines.

---

## 🛡 Security

See [`SECURITY.md`](SECURITY.md) for reporting vulnerabilities.
