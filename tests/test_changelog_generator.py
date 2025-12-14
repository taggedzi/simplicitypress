# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "update_changelog.py"
SPEC = importlib.util.spec_from_file_location("update_changelog", MODULE_PATH)
assert SPEC and SPEC.loader
update_changelog = importlib.util.module_from_spec(SPEC)
sys.modules["update_changelog"] = update_changelog
SPEC.loader.exec_module(update_changelog)  # type: ignore[arg-type]


def test_categorize_subject_conventional():
    assert update_changelog.categorize_subject("feat(ui): add wizard") == "Features"
    assert update_changelog.categorize_subject("fix: patch bug") == "Fixes"
    assert update_changelog.categorize_subject("docs: explain usage") == "Documentation"
    assert update_changelog.categorize_subject("chore(ci): update workflow") == "Maintenance"


def test_categorize_subject_fallback_other():
    assert update_changelog.categorize_subject("improve handling of foo") == "Other"


def test_should_skip_subject_filters():
    assert update_changelog.should_skip_subject("Merge pull request #1")
    assert update_changelog.should_skip_subject("chore(release): cut v0.1.0")
    assert update_changelog.should_skip_subject("Update changelog")
    assert update_changelog.should_skip_subject("docs: tweak changelog wording")
    assert not update_changelog.should_skip_subject("feat: normal commit")
