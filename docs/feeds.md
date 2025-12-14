# 📣 Feeds Guide

SimplicityPress can emit fully static **RSS 2.0** and **Atom 1.0** feeds. Both
formats are optional, disabled by default, and generated as part of the normal
build pipeline so they stay deterministic and easy to test.

---

## 1. Enabling feeds

Feeds require a canonical site URL because every entry uses absolute links. Add
`site.url` and flip the `[feeds]` switch in `site.toml`:

```toml
[site]
url = "https://example.com"

[feeds]
enabled = true
rss_enabled = true
atom_enabled = true
rss_output = "rss.xml"
atom_output = "atom.xml"
max_items = 20
include_posts = true
include_pages = false
include_drafts = false
include_tags = []
[feeds.summary]
mode = "excerpt"   # or "text"
max_chars = 240
```

If feeds are disabled, the build output is unchanged and no `site.url` is
required. When `feeds.enabled = true` but both `rss_enabled` and
`atom_enabled` are `false`, the build fails with a configuration error.

---

## 2. Output paths

- `rss_output` and `atom_output` are relative to the build output directory.
- Both paths must stay inside the output directory (no `..` segments or
  absolute paths).
- Defaults are `rss.xml` and `atom.xml`.

The generator writes UTF-8 XML with stable ordering so repeated builds produce
identical files.

---

## 3. Content selection

| Key              | Default | Notes                                                                 |
| ---------------- | ------- | --------------------------------------------------------------------- |
| `include_posts`  | `true`  | Primary feed content. Drafts obey `include_drafts`.                   |
| `include_pages`  | `false` | Pages must include a `date` front matter field to be eligible.        |
| `include_drafts` | `false` | Only affects posts; pages do not have a draft flag.                   |
| `include_tags`   | `[]`    | When non-empty, only posts that match at least one listed tag appear. |
| `max_items`      | `20`    | Applies after sorting newest → oldest (ties break on URL).            |

Pages without a `date` stay out of feeds even when `include_pages = true`. Add
an ISO-8601 timestamp to the page front matter to opt in.

---

## 4. Summaries

```
[feeds.summary]
mode = "excerpt"   # use post.summary (default)
max_chars = 240    # applies to either mode
```

- `mode = "excerpt"` uses the post front-matter summary (or the auto-generated
  excerpt) and truncates to `max_chars`.
- `mode = "text"` strips HTML tags from the full body before truncating.

Summaries are optional. If a post lacks summary content, the entry omits the
`<description>` (RSS) or `<summary>` (Atom) element.

---

## 5. Template hooks

When feeds are enabled the template context gains:

- `site.feeds_enabled`
- `site.rss_feed_enabled`
- `site.atom_feed_enabled`
- `site.rss_feed_url`
- `site.atom_feed_url`

The default scaffold uses these flags to add `<link rel="alternate">` entries
in the `<head>` plus footer links. Custom themes can do the same.

---

## 6. Validation & errors

- `site.url` must be present when feeds are enabled.
- `max_items` and `summary.max_chars` must be positive integers.
- Output paths must be relative.
- If configuration is invalid the build fails early with a descriptive
  `ValueError`.

See `tests/test_feeds.py` for additional usage examples.
