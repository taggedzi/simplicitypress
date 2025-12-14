# Release Process

SimplicityPress uses a scripted release flow so every tag ships with matching
artifacts, SPDX metadata, an SBOM, and generated release notes.

## Prerequisites

- Install development tooling (including `git-cliff`) via `pip install .[dev]`
  or install `git-cliff` separately.
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
   - Regenerate `CHANGELOG.md` via `git-cliff`.
   - Commit both files with a message like
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

Two Nox sessions wrap the `git-cliff` invocation:

- `nox -s changelog` rewrites `CHANGELOG.md` based on the current commit
  history. Run this after rebasing or when you want to preview the next release
  notes.
- `nox -s changelog_check` is useful in CI to ensure that the committed
  changelog matches the state of the repository.

These sessions rely on `cliff.toml`, which maps Conventional Commit types to
high-level sections (Breaking, Features, Fixes, Docs, Maintenance) and creates
compare links between tags.
