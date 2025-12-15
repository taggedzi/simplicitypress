# Changelog

This file is generated from git history via tools/update_changelog.py.
Releases before v0.2.0 predate that workflow, so earlier sections may not list every historical commit.

## Unreleased

### Features

- feat(gui): add app icon loading and Help â†’ About dialog (8805aa9)

### Fixes

- fix: inspect CLI commands directly (1948e7f)
- fix: handle colored CLI help output (bdd1798)
- fix: adjusted git-cliff call to work with older messages. (999cccf)

### Documentation

- docs: add AI assistance disclosure (67fb7b5)
- docs: add AI assistance disclosure (b6f3253)

### Maintenance

- ci: add docs audit (28e3c1f)

## v0.2.2 - 2025-12-14

### Fixes

- Fix sbom to only include packages that are in distrobution. (061cf0c)

### Other

- Release v0.2.2 (d4de49e)

## v0.2.1 - 2025-12-14

### Other

- Release v0.2.1 (46de9b6)
- Error fix for sbom (f81e2ed)

## v0.2.0 - 2025-12-14

### Features

- feat: add optional sitemap generation with docs and tests (bba4253)

### Fixes

- bug(build.py): fixed type error. (605ebca)

### Documentation

- docs: surface search config template and scaffold defaults (4e44ef6)
- docs: document static search configuration and tuning options (0720689)

### Maintenance

- chore(security): generate CycloneDX SBOM in CI and releases (1c11058)

### Other

- Release v0.2.0 (4476534)
- Replaced the deprecated datetime.utcnow() call with datetime.now(datetime.UTC) in tools/add_spdx_headers.py (line 184), eliminating the warning during nox -s spdx runs. (89743a7)
- Add SPDX CI check via Nox (1a57719)
- Automate SPDX headers across Python files (875b1bc)
- Feeds: add optional RSS/Atom artifacts, config + docs + tests (61082ad)
- Added a proper search nav integration: (47e80c3)
- Phase 3 Search (de95364)
- Implemented the full Phase 2 pipeline so enabling search now emits metadata, an inverted index, and a working client. The new SearchAssetsBuilder compiles posts/pages into deterministic search_docs.json + search_terms.json, writes a lightweight JS client, and renders the themed search page only when search.enabled is set (src/simplicitypress/core/search_index.py (lines 18-507)). The default scaffold search page now ships the matching UI/inline config hook so the browser app can load the assets and render results (src/simplicitypress/scaffold/templates/search.html (lines 1-35)). (0d0b6f8)
- Implemented optional search scaffolding gated by search.enabled, so nothing changes unless the flag is set. Config now carries the new defaults for all tuning knobs (src/simplicitypress/core/default_config.py (lines 9-46), src/simplicitypress/core/models.py (lines 24-38), src/simplicitypress/core/config.py (lines 34-95)), and the build pipeline exposes search_enabled/search_url to templates while deferring all work when disabled (src/simplicitypress/core/build.py (lines 57-225)). (2df2ee4)

## v0.1.7 - 2025-12-13

### Documentation

- docs(readme): continued adding links in repo. (da4f9d9)
- docs(readme): add status badges and reorganize content (083bd69)
- docs: add support policy (5de0a08)
- docs: add security policy (9147dd9)

### Maintenance

- chore(github): added contributing.md (f341889)
- chore(github): add code of conduct (6cf11cf)
- chore(github): add PR auto-labeler workflow (3c37573)
- chore(github): add issue templates, PR template, and discussions welcome (0646ed6)

### Other

- Release v0.1.7 (f082dc4)
- Relocate release helper into tools and update references (e251ba6)
- Added tree_maker script to help with dev, AND modified labeler to better reflect project structure. (3fe2036)
- I'm so sick of license issues. Please let this fix it. (bc599dd)

## v0.1.6 - 2025-12-11

### Other

- Release v0.1.6 (7eb9197)
- Fixed tests. (b7efdb0)

## v0.1.5 - 2025-12-11

### Features

- feat: simplify package init and centralize version (0a33223)

### Other

- Release v0.1.5 (3084546)

## v0.1.4 - 2025-12-11

### Other

- Release v0.1.4 (104015d)
- changed call method of version (1cbdea1)

## v0.1.3 - 2025-12-11

### Other

- Release v0.1.3 (93d0e1d)
- Added build release files and attach to release. (f4600b3)

## v0.1.2 - 2025-12-11

### Other

- Release v0.1.2 (256abf1)
- Removed test_import.py flawed test. (a98492d)

## v0.1.1 - 2025-12-11

### Features

- feat: add Windows build_release packaging with legal files (3db139b)
- feat: add dist build tooling and release workflow (5f9de0a)

### Fixes

- fix 2 (7ce604b)
- Fix matrix to work with github workflows (7110d1f)

### Maintenance

- Refactor to shared library API and GUI task execution (67aef51)

### Other

- Release v0.1.1 (42389fd)
- Fixed make_release.py (e09accc)
- automattion for release builds. (ed4d19a)
- v1 (c6403ef)
- Added Release workflow (2315365)
- modified coverage to 94%, removed GUI from testing. (c5eb115)
- Added coverage to tests. Coverage at 43% (22cd979)
- Add pytest coverage support (ca1cb1b)
- Fixed Typecheck errors in gui (4a60d4e)
- Lint fixes (5c12a6d)
- Fixed Binary Crashes on 404 due to error suppression going to console that didn't exist in pyinstaller binary "--windowed" mode. (db2d6be)
- Gui Updates (ed7587a)
- gui and api changes (03aaedb)
- gitignore change for nox. (e0a05f0)
- Fixes. (943dc8d)
- Automation with nox and github ci workflow (67b08e9)
- Preview fix. (65b2235)
- First Pass. (ab46e0a)
- Theme documentation for users and devs. (b20fe4e)
- Created better base theme/template. (8b62c98)
- Add initial pytest suite for core SimplicityPress behavior (83b40de)
- License and metadata (7154d43)
- Updated readme with instructions and quickstart. (5d009ce)
- Add page-driven navigation and nav-aware default About page (19356dc)
- Add RSS feed generation and enhance CLI build/serve (3c5d8ea)
- Add Jinja2 rendering, site scaffolding, and full HTML output (ca09249)
- Implement content discovery, front matter parsing, and markdown rendering (d2ff455)
- Config loading and validation (ccb42a6)
- Project config (cd7fa1a)
