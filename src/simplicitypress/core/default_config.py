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
    },
    "author": {
        "name": "",
        "email": "",
    },
}

