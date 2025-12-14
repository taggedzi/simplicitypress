
# 📘 **Document - theme_from_scratch.md**

## **How to Build a Theme From Scratch for SimplicityPress**

This guide walks you through designing a completely new theme for SimplicityPress.
It assumes you already understand basic HTML, CSS, and Jinja2 templating.

---

# 1. Overview

A SimplicityPress theme is a collection of:

* **Templates** (`.html`) using **Jinja2**
* **Static assets** - usually CSS, and optionally JS or images
* A folder structure recognized by SimplicityPress

Themes live inside a SimplicityPress site:

```
mysite/
  templates/
  static/
    css/
    img/
    js/
```

SimplicityPress does **not** enforce a special theme engine -
a theme is simply whatever HTML/CSS you place in these folders.

---

# 2. The Required Templates

A working theme must include:

| Template     | Purpose                                                 |
| ------------ | ------------------------------------------------------- |
| `base.html`  | Global layout: header, navigation, footer, main wrapper |
| `index.html` | Homepage showing list of posts + pagination             |
| `post.html`  | Single blog post                                        |
| `page.html`  | Standalone page (About, Contact, etc.)                  |
| `tags.html`  | Tag index                                               |
| `tag.html`   | Posts for a specific tag                                |

Feeds are emitted programmatically, so no `feed.xml` template is required.
Themes should instead surface links using the `site.*feed*` flags described in
`docs/template_context_tables.md`.

**Tip:** Always start with `base.html` - everything else extends it.

---

# 3. Building the Base Layout

Example structure:

```html
<!doctype html>
<html lang="{{ site.language }}">
<head>
  <meta charset="utf-8">
  <title>{{ site.title }}{% if site.subtitle %} - {{ site.subtitle }}{% endif %}</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <header>
    <h1><a href="/">{{ site.title }}</a></h1>
    {% if site.subtitle %}<p>{{ site.subtitle }}</p>{% endif %}
    <nav>
      <a href="/">Home</a>
      <a href="/tags/">Tags</a>
      {% for item in nav_items %}
        <a href="{{ item.url }}">{{ item.title }}</a>
      {% endfor %}
    </nav>
  </header>

  <main>
    {% block content %}{% endblock %}
  </main>

  <footer>
    <p>&copy; {{ site.title }} - Powered by SimplicityPress.</p>
  </footer>
</body>
</html>
```

This is your root layout.

---

# 4. Building Each Template

### index.html

```jinja2
{% extends "base.html" %}
{% block content %}
  <h1>Latest posts</h1>
  {% for post in posts %}
    <article>
      <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
      <time>{{ post.date.date() }}</time>
      <p>{{ post.summary }}</p>
    </article>
  {% endfor %}
{% endblock %}
```

### post.html

```jinja2
{% extends "base.html" %}
{% block content %}
  <article>
    <h1>{{ post.title }}</h1>
    <time>{{ post.date.date() }}</time>
    <div>{{ post.content_html | safe }}</div>
  </article>
{% endblock %}
```

### page.html, tags.html, tag.html

Follow the same pattern - see `template_context_tables.md` below for available variables.

---

# 5. Adding Styles

Themes must define a CSS file at:

```
static/css/style.css
```

You can use any styling approach:

* Pure CSS (recommended)
* CSS variables for themes
* Tailwind (compiled manually)
* Bootstrap
* A custom utility set

Keep it simple and avoid JS for the default theme.

---

# 6. Testing Your Theme

```
simplicitypress serve --site-root mysite
```

Modify templates → refresh browser.

---

# 7. Tips for Clean Theme Design

* Use **semantic HTML** - `<article>`, `<nav>`, `<header>`, `<footer>`.
* Keep CSS modular and readable.
* Use CSS variables so users can recolor easily.
* Avoid layout logic in templates - keep them presentation-focused.
* Ensure accessibility (contrast, font size, keyboard nav).
