# Release Process

SimplicityPress uses a scripted release flow so every tag ships with matching
artifacts, SPDX metadata, an SBOM, and generated release notes.

Day-to-day development does **not** update `CHANGELOG.md`. The release script
regenerates it just before tagging so PRs stay focused on code changes.

## Prerequisites

- Install development tooling via `pip install .[dev]`.
- Ensure your git working tree is clean before starting.

## Cutting a release

1. Decide on the next semantic version (e.g. `0.8.0`).
2. Run the helper script:

   ```bash
   python tools/make_release.py 0.8.0
   ```

   The script will:

   - Verify the working tree is clean.
   - Update `pyproject.toml` with the new version.
   - Regenerate `CHANGELOG.md` via `tools/update_changelog.py`, including
     mojibake normalization (spaces and arrows are rewritten to clean Unicode).
   - Commit the updated files (if anything changed) with a message like
     `chore(release): update changelog for v0.8.0`.
   - Create the annotated git tag `v0.8.0`.

3. Push the commit and tag:

   ```bash
   git push
   git push --tags
   ```

GitHub Actions takes over from here. The release workflow runs the full test
matrix, builds artifacts, regenerates the SBOM, and publishes the tag to the
GitHub Releases page. Release notes are extracted automatically from the just
generated changelog, so no manual editing is required.

## Regenerating the changelog manually

`nox -s changelog` rewrites `CHANGELOG.md` based on the current commit
history. This is optional for day-to-day work; the release script and CI
generate the changelog right before tagging so regular PRs do not need to touch
the file. See `docs/changelog.md` for details on how the script groups commits,
the available CLI flags, and how to generate release notes for a specific tag.
