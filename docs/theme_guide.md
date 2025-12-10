# 📘 **Theme Guide - SimplicityPress Default Theme & Customization**

> **For SimplicityPress users and theme designers**
> This document explains how the built-in theme works, how site owners can customize it safely, and how to create entirely new themes.

---

# 1. Overview

SimplicityPress includes a **clean, elegant default theme** designed to give new users a working, attractive site immediately.
This theme lives entirely in the **scaffold** directory bundled with the package:

```
simplicitypress/
    scaffold/
        templates/
        static/
```

When a user runs:

```bash
simplicitypress init --site-root mysite
```

SimplicityPress **copies** these scaffold templates into the new site’s folder:

```
mysite/
  templates/
  static/
```

Users may edit these files freely; they are *not* overwritten during future builds.

---

# 2. Theme Structure

### 📁 **Template Files**

Located under:

```
templates/
```

| File         | Purpose                                   |
| ------------ | ----------------------------------------- |
| `base.html`  | Global layout, header, navigation, footer |
| `index.html` | Home page (latest posts + pagination)     |
| `post.html`  | Individual blog posts                     |
| `page.html`  | Static content pages                      |
| `tags.html`  | Tag index page                            |
| `tag.html`   | Posts for a specific tag                  |
| `feed.xml`   | RSS/Atom feed template                    |

### 📁 **Static Files**

Located under:

```
static/css/style.css
```

This is the entire styling layer for the default theme. It uses **CSS custom properties** so users can easily change colors, spacing, fonts, etc.

---

# 3. How Rendering Works

SimplicityPress uses **Jinja2 templates**.

Each page type passes a specific context:

### Posts

```jinja2
{{ post.title }}
{{ post.content_html | safe }}
{{ post.tags }}
{{ post.date }}
```

### Pages

```jinja2
{{ page.title }}
{{ page.content_html | safe }}
```

### Global Context (available everywhere)

```jinja2
{{ site }}   # All site metadata from site.toml
{{ author }} # Site author information
{{ nav_items }} # Pages opted into navigation
```

If you modify templates, you can assume these variables always exist.

---

# 4. Customizing the Default Theme

Users generally customize themes in three ways:

---

## 4.1 🎨 **Changing Colors, Fonts, and Spacing**

All theme colors live at the top of `style.css`:

```css
:root {
  --sp-color-bg: #f5f5f7;
  --sp-color-surface: #ffffff;
  --sp-color-text: #111827;
  --sp-color-accent: #2563eb;
  ...
}
```

To change the accent color, for example:

```css
--sp-color-accent: #d6336c;
--sp-color-accent-soft: #f8d7e1;
```

This updates links, hover states, tags, and pagination buttons.

Fonts can be switched by editing:

```css
--sp-font-body: Georgia, serif;
--sp-font-mono: "Courier New", monospace;
```

Spacing values are controlled through padding and margin rules.

---

## 4.2 🧱 **Modifying Layout**

Every template extends `base.html`:

```jinja2
{% extends "base.html" %}
{% block content %}
...
{% endblock %}
```

To change:

* Header layout
* Navigation alignment
* Footer text
* Container width

…edit `base.html` and/or `style.css`.

---

## 4.3 🧩 **Adding New Blocks or Partials**

You can add your own Jinja blocks to `base.html`:

```html
{% block sidebar %}{% endblock %}
```

Then use them in:

```jinja2
{% block sidebar %}
  <p>This is my sidebar</p>
{% endblock %}
```

This allows extensions without creating entirely new templates.

---

# 5. Creating Your Own Theme

Creating a custom theme is simple: **replace the templates and CSS**.

A typical theme folder might look like:

```
mysite/
  templates/
    base.html
    index.html
    post.html
    ...
  static/
    css/
      style.css
    js/
      script.js
    img/
      logo.png
```

SimplicityPress does not enforce any structure beyond:

* Templates must exist and be valid Jinja2.
* CSS/images can be anything.
* Output paths will mirror the template names.

### Steps to build a new theme:

1. Copy the default templates into a separate folder.
2. Modify layout, markup, color scheme.
3. Add any CSS/JS/images as needed.
4. Keep required template blocks (`content`).
5. Ensure `<link rel="stylesheet">` paths remain correct.

---

# 6. Updating Themes Safely

Because SimplicityPress copies scaffold templates only during `init`, your theme files are **never overwritten**.

If a future version of SimplicityPress updates the default theme:

* Your site’s templates remain unchanged.
* You can copy over updated templates manually if desired.
* There is no risk of losing customizations.

---

# 7. Common Theme Customization Examples

### Change content width:

```css
.sp-container {
  max-width: 900px;
}
```

### Add a logo to the header:

In `base.html`:

```html
<img src="/static/img/logo.png" alt="Site logo" class="sp-logo">
```

In CSS:

```css
.sp-logo {
  height: 40px;
  margin-right: 0.75rem;
}
```

### Add dark mode:

Add variables:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --sp-color-bg: #1e1e1e;
    --sp-color-surface: #2a2a2a;
    --sp-color-text: #e5e5e5;
    --sp-color-border: #444;
  }
}
```

### Change homepage layout to a grid:

```css
.sp-post-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}
```

---

# 8. Recommended Workflow for Theme Designers

1. Create a test site:

   ```bash
   simplicitypress init --site-root theme-playground
   simplicitypress serve --site-root theme-playground
   ```

2. Edit templates/CSS while the server is running.

3. Refresh browser to preview changes.

4. Iterate until theme is fully designed.

5. Once finished, copy the theme into your real project.

---

# 9. Final Notes

* Themes are **completely decoupled** from program logic.
* Anything you can write in HTML/CSS/JS will work.
* SimplicityPress does not impose frameworks or build tools.
* All customization is done at the file level - simple, transparent, flexible.
