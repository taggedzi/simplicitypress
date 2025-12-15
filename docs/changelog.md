# Changelog generation

`tools/update_changelog.py` owns `CHANGELOG.md`. It shells out to `git log`
directly, so it behaves the same on Linux, macOS, and Windows. The script writes
deterministic output (LF endings, one trailing newline, newest releases first)
and only needs the Git CLI that ships with the runner.

## CLI overview

| Flag | Description |
| ---- | ----------- |
| `--update` | Rewrite the changelog file (default `CHANGELOG.md`). |
| `--version vX.Y.Z` | Optional: generate a release section for a specific tag; if the tag does not yet exist the range defaults to the latest tag..HEAD and the section date is `today()`. |
| `--since <ref>` | Override the base reference for the “Unreleased” section or when emitting a pre-tagged release with `--version`. |
| `--[no-]include-unreleased` | Toggle the Unreleased section (default: included). |
| `--output-file <path>` | Write to a different file (handy for release notes). |

Examples:

```bash
# Update the repo changelog
python tools/update_changelog.py --update

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

- Day-to-day development does not touch `CHANGELOG.md`.
- Release automation (`nox -s release_local -- <version>`) rewrites the file,
  normalizes mojibake (U+202F, `â€¯`, `â†’`, etc.), and commits it as part of
  the release/tag process.
- Run `nox -s changelog` manually if you want to preview the upcoming release
  notes before cutting a release.

## Normalization guard rails

`normalize_text()` enforces LF endings and replaces common mojibake sequences:

- Non-breaking spaces and narrow no-break spaces (U+202F) are converted to ASCII
  spaces.
- `â€¯` becomes a regular space.
- `â†’` is rewritten to the Unicode right arrow (`→`).

This keeps the committed changelog stable across platforms and prevents release
notes from drifting when pasting text from different terminals.
