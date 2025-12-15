# Documentation Policy

This repo treats documentation as part of the product. Automated checks (via
`nox -s docs_audit`) keep the README and supporting guides aligned with the
actual CLI/API implementation. Follow the guidelines below when authoring docs
so the audit stays meaningful.

## CLI References

- Prefer using the full command form (`simplicitypress build --site-root example`)
- Only mention commands that exist in `simplicitypress --help`
- If you need to document a future/experimental command, wrap that section
  between `<!-- no-audit -->` and `<!-- /no-audit -->` to skip validation

## Python Examples

- Use fenced blocks with ` ```python ` for runnable code
- Examples run inside an empty temporary directory; include any required imports
- To skip execution (e.g., when showing pseudo code), add `no-run` to the fence:

  ````
  ```python no-run
  # Doc snippet that should not execute during docs_audit
  ```
  ````

- Avoid non-deterministic behavior (network calls, random data, etc.)
- Keep snippets short—treat them like doctests

## Other Notes

- The audit also checks that exported functions/classes in `simplicitypress.api`
  and the Typer CLI entry points have docstrings. Add a concise docstring for
  every public definition to describe intent rather than implementation details.
- Sections that genuinely cannot be verified (CLI or otherwise) may be wrapped
  with the `no-audit` comment markers described above.
