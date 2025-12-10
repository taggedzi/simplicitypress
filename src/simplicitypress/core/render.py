from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_environment(templates_dir: Path) -> Environment:
    """
    Create and return a Jinja2 Environment for the given templates directory.
    """
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    # Optionally add filters/helpers later; keep minimal for now.
    return env


def render_to_file(
    env: Environment,
    template_name: str,
    context: Mapping[str, Any],
    target_path: Path,
) -> None:
    """
    Render the given template with the provided context and write it to target_path.
    Ensures the parent directory exists.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    template = env.get_template(template_name)
    html = template.render(**context)
    target_path.write_text(html, encoding="utf-8")

