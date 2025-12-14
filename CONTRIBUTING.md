# Contributing to SimplicityPress

Thanks for your interest in contributing! 🎉  
Contributions of all kinds are welcome: bug reports, documentation improvements, ideas, and code.

This project aims to stay **simple, readable, and predictable**, so a few guidelines help keep things consistent.

---

## Ways to Contribute

### 🐞 Reporting Bugs

- Use the **Bug report** issue template
- Include:
  - Steps to reproduce
  - Expected vs actual behavior
  - OS (Windows/Linux/macOS)
  - CLI / GUI / API (if relevant)
  - Logs or tracebacks (redact secrets)

### 💡 Feature Requests

- Use the **Feature request** issue template
- Clearly describe the problem being solved
- Keep scope focused and aligned with the project’s goals

### ❓ Questions

- Use **GitHub Discussions** for questions or ideas
- If it turns out to be a bug, we may ask you to open an issue

---

## Development Setup

### Requirements

- Python **3.11+**
- Git
- A virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
pip install -e .[dev]
```

### Running Tests

This project uses **pytest** and **nox**.

```bash
pytest
# OR 
nox -s tests
```

---

## Code Style & Quality

- Follow existing project patterns and structure
- Prefer clarity over cleverness
- Keep functions focused and well-named
- Add or update tests when behavior changes
- Use type hints where practical

Automated checks may include:

- Formatting and linting
- Type checking
- Unit tests

---

## Pull Requests

1. Create a feature branch from `main`
2. Make focused, incremental commits
3. Use **Conventional Commit** messages where possible:

   - `feat:`
   - `fix:`
   - `docs:`
   - `chore:`
4. Open a Pull Request and fill out the PR template

Pull requests are reviewed for:

- Correctness
- Readability
- Test coverage (where appropriate)
- Alignment with project scope

## AI-Assisted Contributions

Maintainers sometimes rely on AI tools (for example, ChatGPT/Codex) to prototype ideas, but every change is reviewed and owned by a human before merging. If AI assistance significantly shaped your contribution, include a brief note in the pull request so reviewers understand the context.

---

## Licensing

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

## Code of Conduct

This project follows the **Contributor Covenant Code of Conduct**.
By participating, you agree to uphold it. Please report unacceptable behavior to the project maintainer(s).

---

Thanks again for contributing — your help makes this project better! 🚀
