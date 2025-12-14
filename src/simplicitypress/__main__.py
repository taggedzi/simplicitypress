# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

from .cli import app


def main() -> None:
    """
    Entry point for ``python -m simplicitypress``.
    """
    app()


if __name__ == "__main__":
    main()
