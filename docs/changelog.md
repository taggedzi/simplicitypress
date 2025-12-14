# Changelog generation

`tools/update_changelog.py` owns `CHANGELOG.md`. It shells out to `git log`
directly, so it behaves the same on Linux, macOS, and Windows. The script writes
deterministic output (LF endings, one trailing newline, newest releases first)
and only needs the Git CLI that ships with the runner.

## CLI overview

| Flag | Description |
| ---- | ----------- |
| `--update` | Rewrite the changelog file (default `CHANGELOG.md`). |
| `--check` | Exit with status 1 if the changelog would change. |
| `--version vX.Y.Z` | Optional: generate a release section for a specific tag; if the tag does not yet exist the range defaults to the latest tag..HEAD and the section date is `today()`. |
| `--since <ref>` | Override the base reference for the “Unreleased” section or when emitting a pre-tagged release with `--version`. |
| `--[no-]include-unreleased` | Toggle the Unreleased section (default: included). |
| `--output-file <path>` | Write to a different file (handy for release notes). |

Examples:

```bash
# Update the repo changelog
python tools/update_changelog.py --update

# CI-style verification
python tools/update_changelog.py --check

# Generate release notes for v0.2.3 (written to CHANGELOG_LATEST.md)
python tools/update_changelog.py --update --version v0.2.3 \
  --include-unreleased=false --output-file CHANGELOG_LATEST.md
```

## Commit grouping

Commits are listed newest-first. Merge commits are ignored, along with subjects
matching any of the filters below:

- `chore(release): ...`
- `Update changelog`
- Anything containing `changelog`

If a commit follows a Conventional Commit prefix it is grouped into a section.
Prefixes map to sections as follows:

- `feat` → Features
- `fix`/`bug` → Fixes
- `docs` → Documentation
- `chore`, `ci`, `refactor`, `test`, `build`, `perf` → Maintenance

Commits without a recognized prefix land in the “Other” section, so non
Conventional Commit histories still render cleanly.

## Typical workflow

- Run `nox -s changelog` locally to rewrite `CHANGELOG.md` after merging a PR.
- CI runs `nox -s changelog_check` to ensure the file is committed.
- Release automation calls `python tools/update_changelog.py --update --version vX.Y.Z`
  so that the release commit contains the new section and the GitHub Release
  job can reuse the same generator to populate release notes.
