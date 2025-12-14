# SPDX headers in SimplicityPress

SimplicityPress uses machine-readable SPDX headers in its Python source files. These
headers make it easy for tooling (including downstream builders and distributors) to
determine the license for each file without scanning large license texts.

## Which files receive headers?

All tracked Python files get headers:

- `src/simplicitypress/**/*.py`
- `tests/**/*.py`
- `tools/*.py`
- `noxfile.py`

No other file types (templates, static assets, docs, etc.) should include these
comments.

## Enforcing headers

Use the helper script to verify or insert headers:

```bash
python tools/add_spdx_headers.py --check
python tools/add_spdx_headers.py --fix
```

The `--check` mode fails if any file is missing the standard lines or if a conflicting
license tag is present. The `--fix` mode inserts missing headers while still reporting
conflicts.

If you use Nox, two convenience sessions are available:

```bash
nox -s spdx
nox -s spdx_fix
```

These wrap the script in check and fix mode respectively.
