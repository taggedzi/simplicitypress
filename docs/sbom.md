# CycloneDX SBOM

SimplicityPress publishes a Software Bill of Materials (SBOM) so downstream
users can audit the precise runtime dependencies that ship with every build.
We emit the SBOM in the [CycloneDX](https://cyclonedx.org/) JSON format, a
widely adopted machine-readable standard.

## What is included?

- All runtime dependencies required by `pip install simplicitypress`
- Project metadata (name, version, homepage)
- Generated at build time for deterministic diffs

What is *not* included:

- Development-only tooling (tests, linters, release helpers)
- Optional extras that are not part of the runtime install
- Security or vulnerability findings (this is an inventory only)

## Generating locally

Use the dedicated Nox session to install the project (runtime deps only) and
emit the SBOM to `dist/sbom.cdx.json`:

```bash
nox -s sbom
```

The command prints the final path; you can check it into release artifacts or
archive it with other build outputs. The file is rewritten each time so you
always get a fresh dependency snapshot.

## CI & releases

- GitHub Actions runs `nox -s sbom` on every push and pull request. The
  resulting `dist/sbom.cdx.json` file is uploaded as a workflow artifact named
  `sbom`.
- Tagged releases regenerate the SBOM alongside wheels and sdists, then attach
  it to the published GitHub Release. End users can always download the SBOM
  that corresponds to a release tag.

The SBOM is intentionally simple: it describes *what* ships with SimplicityPress,
so that auditors or downstream packagers have a trustworthy dependency manifest.***
