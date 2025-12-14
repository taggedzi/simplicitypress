# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

"""
Default configuration values for SimplicityPress sites.

User-provided values in ``site.toml`` are merged over these defaults.
"""

default_config: dict = {
    "site": {
        "title": "My Site",
        "subtitle": "",
        "base_url": "",
        "url": "",
        "language": "en",
        "timezone": "UTC",
    },
    "paths": {
        "content_dir": "content",
        "posts_dir": "content/posts",
        "pages_dir": "content/pages",
        "templates_dir": "templates",
        "static_dir": "static",
        "output_dir": "output",
    },
    "build": {
        "posts_per_page": 10,
        "include_drafts": False,
    },
    "author": {
        "name": "",
        "email": "",
    },
    "search": {
        "enabled": False,
        "output_dir": "assets/search",
        "page_path": "search/index.html",
        "max_terms_per_doc": 300,
        "min_token_len": 2,
        "drop_df_ratio": 0.70,
        "drop_df_min": 0,
        "weight_body": 1.0,
        "weight_title": 8.0,
        "weight_tags": 6.0,
        "normalize_by_doc_len": True,
    },
    "sitemap": {
        "enabled": False,
        "output": "sitemap.xml",
        "include_tags": True,
        "include_pages": True,
        "include_posts": True,
        "include_index": True,
        "exclude_paths": [],
    },
    "feeds": {
        "enabled": False,
        "rss_enabled": True,
        "atom_enabled": True,
        "rss_output": "rss.xml",
        "atom_output": "atom.xml",
        "max_items": 20,
        "include_drafts": False,
        "include_pages": False,
        "include_posts": True,
        "include_tags": [],
        "summary": {
            "mode": "excerpt",
            "max_chars": 240,
        },
    },
}
