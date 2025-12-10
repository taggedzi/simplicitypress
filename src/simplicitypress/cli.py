from pathlib import Path
from textwrap import dedent
from typing import Optional
import http.server
import os
import socketserver

import typer

from .core import ProgressEvent, build_site, load_config

app = typer.Typer(help="SimplicityPress static site generator CLI.")


def _print_progress(event: ProgressEvent) -> None:
    """
    Simple progress callback used by the CLI to report build stages.
    """
    message = event.message or ""
    typer.echo(f"[{event.stage}] {message}")


@app.command()
def init(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
) -> None:
    """
    Initialize a new SimplicityPress site at the given path.
    """
    typer.echo(f"[init] Initializing site at: {site_root}")
    site_root.mkdir(parents=True, exist_ok=True)

    content_dir = site_root / "content"
    posts_dir = content_dir / "posts"
    pages_dir = content_dir / "pages"
    templates_dir = site_root / "templates"
    static_dir = site_root / "static"
    css_dir = static_dir / "css"

    for directory in (content_dir, posts_dir, pages_dir, templates_dir, css_dir):
        directory.mkdir(parents=True, exist_ok=True)

    site_toml = site_root / "site.toml"
    if site_toml.exists():
        typer.echo("site.toml already exists; leaving it unchanged.")
    else:
        site_toml.write_text(
            dedent(
                """\
                [site]
                title = "My SimplicityPress Site"
                subtitle = ""
                base_url = ""
                language = "en"
                timezone = "UTC"

                [paths]
                content_dir = "content"
                posts_dir = "content/posts"
                pages_dir = "content/pages"
                templates_dir = "templates"
                static_dir = "static"
                output_dir = "output"

                [build]
                posts_per_page = 10
                include_drafts = false

                [author]
                name = ""
                email = ""
                """,
            ),
            encoding="utf-8",
        )
        typer.echo("Created default site.toml")

    # Basic CSS
    css_path = css_dir / "style.css"
    if not css_path.exists():
        css_path.write_text(
            dedent(
                """\
                body {
                  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                  margin: 0;
                  padding: 0;
                  background: #f5f5f5;
                  color: #222;
                }

                main {
                  max-width: 42rem;
                  margin: 2rem auto;
                  padding: 0 1rem 3rem;
                  background: #ffffff;
                  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }

                header, footer {
                  max-width: 42rem;
                  margin: 0 auto;
                  padding: 1rem;
                }

                header h1 a {
                  text-decoration: none;
                  color: inherit;
                }

                nav a {
                  margin-right: 1rem;
                }

                .content {
                  margin-top: 1.5rem;
                }

                .pagination a {
                  margin-right: 1rem;
                }
                """,
            ),
            encoding="utf-8",
        )
        typer.echo("Created static/css/style.css")

    # Templates
    templates = {
        "base.html": """\
            <!doctype html>
            <html lang="{{ site.language | default('en') }}">
            <head>
              <meta charset="utf-8">
              <title>{{ site.title }}{% if site.subtitle %} - {{ site.subtitle }}{% endif %}</title>
              <link rel="stylesheet" href="/static/css/style.css">
            </head>
            <body>
              <header>
                <h1><a href="/">{{ site.title }}</a></h1>
                {% if site.subtitle %}
                  <p>{{ site.subtitle }}</p>
                {% endif %}
                <nav>
                  <a href="/">Home</a>
                  <a href="/tags/">Tags</a>
                </nav>
              </header>
              <main>
                {% block content %}{% endblock %}
              </main>
              <footer>
                <p>Powered by SimplicityPress.</p>
              </footer>
            </body>
            </html>
        """,
        "feed.xml": """\
            <?xml version="1.0" encoding="utf-8"?>
            <rss version="2.0">
              <channel>
                <title>{{ site.title }}</title>
                {% if site.subtitle %}
                <description>{{ site.subtitle }}</description>
                {% else %}
                <description>{{ site.title }}</description>
                {% endif %}
                {% if site.base_url %}
                <link>{{ site.base_url }}</link>
                {% else %}
                <link>http://localhost/</link>
                {% endif %}
                <language>{{ site.language or "en" }}</language>

                {% for post in posts %}
                <item>
                  <title>{{ post.title }}</title>
                  {% if site.base_url %}
                  <link>{{ site.base_url.rstrip("/") }}{{ post.url }}</link>
                  <guid>{{ site.base_url.rstrip("/") }}{{ post.url }}</guid>
                  {% else %}
                  <link>{{ post.url }}</link>
                  <guid>{{ post.url }}</guid>
                  {% endif %}
                  <pubDate>{{ post.date.strftime("%a, %d %b %Y %H:%M:%S %z") if post.date.tzinfo else post.date.strftime("%a, %d %b %Y 00:00:00 +0000") }}</pubDate>
                  {% if post.summary %}
                  <description>{{ post.summary }}</description>
                  {% endif %}
                </item>
                {% endfor %}
              </channel>
            </rss>
        """,
        "index.html": """\
            {% extends "base.html" %}
            {% block content %}
              <h2>Latest posts</h2>
              {% if posts %}
                <ul>
                  {% for post in posts %}
                    <li>
                      <article>
                        <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
                        <p><small>{{ post.date.date() }}</small></p>
                        {% if post.summary %}
                          <p>{{ post.summary }}</p>
                        {% endif %}
                      </article>
                    </li>
                  {% endfor %}
                </ul>

                <nav class="pagination">
                  {% if prev_url %}
                    <a href="{{ prev_url }}">&laquo; Newer posts</a>
                  {% endif %}
                  {% if next_url %}
                    <a href="{{ next_url }}">Older posts &raquo;</a>
                  {% endif %}
                </nav>
              {% else %}
                <p>No posts yet.</p>
              {% endif %}
            {% endblock %}
        """,
        "post.html": """\
            {% extends "base.html" %}
            {% block content %}
              <article>
                <h2>{{ post.title }}</h2>
                <p><small>{{ post.date.date() }}</small></p>
                {% if post.tags %}
                  <p>
                    Tags:
                    {% for tag in post.tags %}
                      <a href="/tags/{{ tag|lower|replace(' ', '-') }}/">{{ tag }}</a>
                      {% if not loop.last %}, {% endif %}
                    {% endfor %}
                  </p>
                {% endif %}
                <div class="content">
                  {{ post.content_html | safe }}
                </div>
              </article>
            {% endblock %}
        """,
        "page.html": """\
            {% extends "base.html" %}
            {% block content %}
              <article>
                <h2>{{ page.title }}</h2>
                <div class="content">
                  {{ page.content_html | safe }}
                </div>
              </article>
            {% endblock %}
        """,
        "tags.html": """\
            {% extends "base.html" %}
            {% block content %}
              <h2>Tags</h2>
              {% if tags %}
                <ul>
                  {% for tag in tags %}
                    <li>
                      <a href="{{ tag.url }}">{{ tag.name }}</a> ({{ tag.count }})
                    </li>
                  {% endfor %}
                </ul>
              {% else %}
                <p>No tags yet.</p>
              {% endif %}
            {% endblock %}
        """,
        "tag.html": """\
            {% extends "base.html" %}
            {% block content %}
              <h2>Posts tagged "{{ tag }}"</h2>
              {% if posts %}
                <ul>
                  {% for post in posts %}
                    <li>
                      <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
                      <p><small>{{ post.date.date() }}</small></p>
                      {% if post.summary %}
                        <p>{{ post.summary }}</p>
                      {% endif %}
                    </li>
                  {% endfor %}
                </ul>
              {% else %}
                <p>No posts for this tag yet.</p>
              {% endif %}
            {% endblock %}
        """,
    }

    for name, content in templates.items():
        path = templates_dir / name
        if not path.exists():
            path.write_text(dedent(content), encoding="utf-8")
            typer.echo(f"Created template: {path.relative_to(site_root)}")

    # Sample content
    sample_post = posts_dir / "example-post.md"
    if not sample_post.exists():
        sample_post.write_text(
            dedent(
                """\
                +++
                title = "Example Post"
                date = "2024-01-01"
                tags = ["example", "intro"]
                summary = "This is an example post created by SimplicityPress init."
                +++
                Welcome to **SimplicityPress**!

                This is your first post. Edit or delete it, then start writing.
                """,
            ),
            encoding="utf-8",
        )
        typer.echo("Created sample post at content/posts/example-post.md")

    sample_page = pages_dir / "about.md"
    if not sample_page.exists():
        sample_page.write_text(
            dedent(
                """\
                +++
                title = "About"
                +++
                This is an example *About* page created by SimplicityPress init.
                """,
            ),
            encoding="utf-8",
        )
        typer.echo("Created sample page at content/pages/about.md")

    typer.echo("Initialization complete.")


@app.command()
def new(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the existing site root directory.",
    ),
) -> None:
    """
    Create a new content item (post or page) within the site.
    """
    typer.echo(f"[new] Would create new content in site at: {site_root}")


@app.command()
def build(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Override the site's configured output directory.",
    ),
    include_drafts: bool = typer.Option(
        False,
        "--include-drafts",
        help="Include draft posts in the build.",
    ),
) -> None:
    """
    Build the static site from the given site root.
    """
    try:
        typer.echo(f"[build] Loading config from: {site_root}")
        config = load_config(site_root)

        # Apply CLI overrides.
        if output is not None:
            config.paths.output_dir = output.resolve()
        if include_drafts:
            config.build["include_drafts"] = True

        typer.echo(f"[build] Writing output to: {config.paths.output_dir}")
        build_site(config, progress_cb=_print_progress)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during build: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def serve(
    site_root: Path = typer.Option(
        Path("."),
        help="Path to the site root directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory to serve (defaults to config.paths.output_dir).",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to serve on.",
    ),
    no_build: bool = typer.Option(
        False,
        "--no-build",
        help="Serve without rebuilding the site first.",
    ),
) -> None:
    """
    Serve the generated static site for local development.
    """
    try:
        typer.echo(f"[serve] Loading config from: {site_root}")
        config = load_config(site_root)

        if output is not None:
            config.paths.output_dir = output.resolve()

        if not no_build:
            typer.echo("[serve] Building site before serving...")
            build_site(config, progress_cb=_print_progress)

        output_dir = config.paths.output_dir
        if not output_dir.exists():
            typer.echo(f"Output directory does not exist: {output_dir}")
            raise typer.Exit(code=1)

        typer.echo(f"[serve] Serving {output_dir} at http://localhost:{port}/")
        typer.echo("[serve] Press Ctrl+C to stop.")

        os.chdir(output_dir)

        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                typer.echo("\n[serve] Stopping server.")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error during serve: {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
