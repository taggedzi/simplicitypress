from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib


def parse_front_matter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    """
    Read a Markdown file, extract TOML front matter enclosed in +++ fences
    at the top of the file, and return (metadata_dict, markdown_body).

    If no TOML front matter is found at the very beginning of the file,
    an empty metadata dict and the full file contents are returned.
    """
    text = path.read_text(encoding="utf-8")

    lines = text.splitlines(keepends=True)
    if not lines:
        return {}, ""

    # Front matter must start at the first line with a +++ fence.
    if lines[0].strip() != "+++":
        return {}, text

    closing_index: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "+++":
            closing_index = idx
            break

    # If no closing fence is found, treat as no front matter.
    if closing_index is None:
        return {}, text

    front_matter_lines = lines[1:closing_index]
    front_matter_text = "".join(front_matter_lines)

    try:
        metadata: dict[str, Any] = tomllib.loads(front_matter_text)
    except tomllib.TOMLDecodeError as exc:
        msg = f"Failed to parse TOML front matter in {path}: {exc}"
        raise ValueError(msg) from exc

    body_lines = lines[closing_index + 1 :]

    # Optionally strip a single leading blank line after the closing fence.
    if body_lines and body_lines[0].strip() == "":
        body_lines = body_lines[1:]

    body = "".join(body_lines)
    return metadata, body
