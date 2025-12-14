
# 📘 **Document - template_variables.md**

## **Developer’s Guide to Template Variables & Context**

Every template receives a **context object** from SimplicityPress.

This guide describes every variable available to theme developers.

---

# 1. Global Template Variables

Available in **every template**:

### `site`

A dictionary reflecting `[site]` from `site.toml`.

Example fields:

```json
{
  "title": "My Blog",
  "subtitle": "thoughts & notes",
  "base_url": "",
  "url": "https://example.com",
  "language": "en",
  "timezone": "UTC",
  "sitemap_enabled": true
}
```

SimplicityPress adds the boolean `sitemap_enabled` at build time so themes can
toggle links (the default footer hides the sitemap link until generation is
enabled).

### `author`

From `[author]` in `site.toml`:

```json
{
  "name": "Matthew Craig",
  "email": "example@gmail.com"
}
```

### `nav_items`

A list of user-defined pages that opted into navigation:

```json
[
  { "title": "About", "url": "/about/", "order": 10 }
]
```

---

# 2. Home Page Context (`index.html`)

Variables:

* `posts`: list of `Post` objects
* `page_number`: int
* `total_pages`: int
* `prev_url`: str or None
* `next_url`: str or None

Post object fields include:

```json
{
  "title": "...",
  "slug": "...",
  "summary": "...",
  "tags": ["..."],
  "date": datetime,
  "url": "/posts/my-post/"
}
```

---

# 3. Post Page Context (`post.html`)

Variables:

* `post`: Post object (see above)
* `site`
* `author`
* `nav_items`

---

# 4. Page Context (`page.html`)

Variables:

* `page` object:

```json
{
  "title": "...",
  "slug": "...",
  "content_html": "<p>Rendered HTML...</p>",
  "url": "/about/",
  "show_in_nav": true,
  "nav_title": "About",
  "nav_order": 10
}
```

---

# 5. Tag Index (`tags.html`)

Variables:

* `tags`: list of dictionaries:

```json
[
  { "name": "python", "count": 5, "url": "/tags/python/" },
  { "name": "life",   "count": 2, "url": "/tags/life/" }
]
```

---

# 6. Per-Tag Page (`tag.html`)

Variables:

* `tag`: string (tag name)
* `posts`: list of posts with that tag
