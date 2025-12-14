
# 📘 **Document - template_context_tables.md**

## **Template Context Reference Tables**

This is a quick-reference guide for theme designers, showing exactly which variables each template receives.

---

# 1. Global Variables (All Templates)

| Variable    | Type | Description                                        |
| ----------- | ---- | -------------------------------------------------- |
| `site`      | dict | Values from `[site]` in site.toml                  |
| `author`    | dict | Values from `[author]` in site.toml                |
| `nav_items` | list | Pages that opted into navigation via `show_in_nav` |

`site` also receives runtime flags such as:

- `sitemap_enabled`
- `feeds_enabled`
- `rss_feed_enabled`
- `atom_feed_enabled`
- `rss_feed_url`
- `atom_feed_url`

These allow templates to toggle footer/head links when artifacts exist.

---

# 2. index.html (Home Page)

| Variable      | Type        | Description           |
| ------------- | ----------- | --------------------- |
| `posts`       | list[Post]  | List of recent posts  |
| `page_number` | int         | Current page number   |
| `total_pages` | int         | Number of index pages |
| `prev_url`    | str or None | Link to newer posts   |
| `next_url`    | str or None | Link to older posts   |

---

# 3. post.html (Single Post)

| Variable | Type | Description                  |
| -------- | ---- | ---------------------------- |
| `post`   | Post | The currently displayed post |

---

# 4. page.html (Static Page)

| Variable | Type | Description        |
| -------- | ---- | ------------------ |
| `page`   | Page | The displayed page |

---

# 5. tags.html (All Tags)

| Variable | Type       | Description                         |
| -------- | ---------- | ----------------------------------- |
| `tags`   | list[dict] | `{ name, count, url }` for each tag |

---

# 6. tag.html (Posts For a Tag)

| Variable | Type       | Description                 |
| -------- | ---------- | --------------------------- |
| `tag`    | str        | Tag name (e.g., "python")   |
| `posts`  | list[Post] | Posts that include this tag |

---

