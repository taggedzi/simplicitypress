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
        "feed_items": 20,
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
}
