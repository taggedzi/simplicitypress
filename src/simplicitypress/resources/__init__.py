# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
"""
Packaged assets for the SimplicityPress GUI.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def get_icon_path() -> Path:
    """
    Return the filesystem path to the packaged SimplicityPress icon.
    """
    resource = files(__name__).joinpath("icons", "simplicitypress.ico")
    return Path(resource)
