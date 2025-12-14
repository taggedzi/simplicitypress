
# 📘 **Document - theme_api_stability.md**

## **Theme API Stability Policy (SimplicityPress)**

This document defines what theme authors can rely on and what may change in future versions.

---

# 1. Purpose

To provide:

* Predictable behavior for theme creators
* Safe upgrade paths
* Clear boundaries between stable and unstable APIs

---

# 2. What is Stable?

The following are **guaranteed stable** across 0.x and 1.x versions:

### ✔ Template Names

These files will always exist:

```
base.html
index.html
post.html
page.html
tags.html
tag.html
```

### ✔ Template Context Contracts

Each template will always receive the variables documented in:

```
docs/template_context_tables.md
```

### ✔ Content Model Fields

`Post` and `Page` objects will always include:

* `title`
* `slug`
* `url`
* `date` (posts only)
* `summary` (posts)
* `tags` (posts)
* `content_html`
* `show_in_nav`
* `nav_order`
* `nav_title`

### ✔ Scaffold Behavior

`init` will always copy a functional theme into:

```
templates/
static/
```

---

# 3. What May Change?

The following may evolve (but changes will be announced clearly):

### ⚠ HTML structure of default theme

Your custom themes are unaffected.

### ⚠ Additional template variables

New variables may be added, but never removed without deprecation.

### ⚠ CSS class names in the *default* theme

Only applies to bundled theme, not user themes.

### ⚠ Build pipeline internal details

Does not affect templates unless documented.

---

# 4. What Will Never Change

* Themes are pure HTML/CSS + Jinja2
* No front-end frameworks will be required
* No JavaScript will be mandatory
* User themes will never be overwritten by upgrades
* Template filenames will not be renamed or removed
* Feeds will continue to be emitted via the built-in generator (no separate template required)

---

# 5. Versioning Policy

SimplicityPress follows **semantic versioning** with added guarantees:

| Change Type                 | Allowed in Patch? | Minor?     | Major? |
| --------------------------- | ----------------- | ---------- | ------ |
| New template variables      | Yes               | Yes        | Yes    |
| Removing template variables | No                | No         | Yes    |
| Behavior-breaking changes   | No                | Yes (rare) | Yes    |
| Template name changes       | No                | No         | Yes    |
