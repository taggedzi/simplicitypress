# SPDX-FileCopyrightText: 2025 SimplicityPress contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

import importlib.util
from types import SimpleNamespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "make_release.py"
SPEC = importlib.util.spec_from_file_location("make_release", MODULE_PATH)
assert SPEC and SPEC.loader
make_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(make_release)  # type: ignore[arg-type]


def test_collect_changed_files(monkeypatch):
    outputs: dict[str, str] = {
        str(make_release.PYPROJECT): " M pyproject.toml\n",
        str(make_release.CHANGELOG): "",
    }

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "status", "--porcelain"]:
            target = cmd[-1]
            return SimpleNamespace(stdout=outputs.get(target, ""), stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(make_release, "run", fake_run)
    changed = make_release.collect_changed_files([make_release.PYPROJECT, make_release.CHANGELOG])
    assert make_release.PYPROJECT in changed
    assert make_release.CHANGELOG not in changed


def test_git_commit_and_tag_skips_commit_when_no_files(monkeypatch):
    recorded: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        recorded.append(cmd)
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(make_release, "run", fake_run)
    make_release.git_commit_and_tag("0.1.0", [])
    commands = [" ".join(cmd[:2]) for cmd in recorded]
    assert not any(cmd.startswith("git commit") for cmd in commands)
    assert any(cmd.startswith("git tag") for cmd in commands)


def test_git_commit_and_tag_commits_when_files_present(monkeypatch):
    recorded: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        recorded.append(cmd)
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(make_release, "run", fake_run)
    make_release.git_commit_and_tag("0.2.0", [make_release.CHANGELOG])
    commands = [" ".join(cmd[:2]) for cmd in recorded]
    assert any(cmd.startswith("git add") for cmd in commands)
    assert any(cmd.startswith("git commit") for cmd in commands)
    assert any(cmd.startswith("git tag") for cmd in commands)
