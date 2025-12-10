# SimplicityPress

SimplicityPress is a **minimal, library-first static site generator** designed for people who want a clean, predictable Markdown → HTML workflow without the complexity of full CMS platforms or heavyweight SSG ecosystems.

If your needs are simple - posts, pages, tags, basic navigation, and clean output - SimplicityPress gives you a lightweight, transparent tool that is easy to understand, customize, and automate.

## ✨ What does SimplicityPress do?

- Converts **Markdown files** into static HTML pages using Jinja2 templates.
- Supports:
  - **Blog posts** (with dates, tags, summaries)
  - **Static pages** (About, Contact, FAQ, Projects…)
  - **Optional top navigation for pages**
  - **Automatic tag index and tag detail pages**
  - **Pagination** for large post archives
- Outputs simple, portable HTML you can host anywhere:
  - GitHub Pages  
  - Netlify  
  - Cloudflare Pages  
  - A static web server  
- Ships with a **working default theme** so you can publish immediately.
- Includes a **local development server** for previewing builds.
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
````

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

* About
* Contact
* Projects
* FAQ
* Resume
* Privacy Policy

Pages live under:

```
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

* `title` *(required)*
  Human-readable title.

* `slug` *(optional)*
  Defaults to filename (`about` → `/about/`).

* `show_in_nav` *(optional)*
  Adds this page to the top navigation bar.

* `nav_title` *(optional)*
  Override display label in navigation.

* `nav_order` *(optional)*
  Controls global nav ordering (lower = earlier).

Output:

* URL → `/<slug>/`
* File → `output/<slug>/index.html`

---

## 📝 Posts

Posts appear on the blog index and support dates, tags, summaries, and optional cover images.

Posts live under:

```
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

* Must include a `date`.
* Casually support tags → generate:

  * `/tags/`
  * `/tags/<tag>/`
* Appear in:

  * Home page
  * Pagination pages
  * Tag listings

Output:

* URL → `/posts/<slug>/`
* File → `output/posts/<slug>/index.html`

---

## 🧭 Navigation

The default theme includes:

* **Home** (`/`)
* **Tags** (`/tags/`)
* Any **pages that opt in** with `show_in_nav = true`

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

## License

SimplicityPress is released under the [MIT License](./LICENSE).
