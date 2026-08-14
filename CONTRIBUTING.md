# Contributing Guide

Thanks for your interest in contributing to Katip Celebi! This project welcomes contributions from everyone. To keep the codebase consistent and maintainable, please follow the guidelines below.

## Following the Project Structure

When adding new code, please keep it within the existing folder structure. Place your code in the relevant module rather than creating new top-level folders.

```
KatipCelebi/
├── src/
│   ├── app.py              # entry point, main window — startup logic only
│   ├── books/               # everything related to books, cards, covers, lending
│   ├── people/              # borrower management
│   ├── settings/            # settings page, relocation
│   ├── stats/                # charts, goals, statistics
│   └── shared/               # theme, palette, icons, config — shared code
├── assets/
│   ├── lang/                  # language files (en, tr, ru, zh, es, fr)
│   ├── screenshots/
│   └── styles/                 # QSS theme files
```

**Guidelines:**

- **One feature, one module.** If you're adding something related to books, it goes in `books/`; if it's about borrowers, it goes in `people/`. If a feature touches multiple modules (e.g. lending a book updates both `books/` and `people/`), keep the business logic in the relevant module and connect them through explicit function/method calls — avoid creating hidden dependencies between modules.
- **`shared/` is only for code that is genuinely shared.** Theme, icons, and config used by multiple modules belong here. Don't put helpers specific to a single module into `shared/`.
- **Keep `app.py` thin.** When adding new windows, pages, or business logic, don't bloat `app.py` — define it as a class/function within the relevant module and call it from `app.py`.
- **Open an issue before adding a new top-level folder** so we can discuss it first. Structural changes shouldn't be a surprise in a small PR.
- **When adding a language file**, follow the "Adding a Language" steps in the README, and make sure translation keys match the corresponding `en.json` exactly.

## PEP 8 Compliance

All Python code must follow [PEP 8](https://peps.python.org/pep-0008/).

**Minimum expectations:**

- 4-space indentation (no tabs)
- Line length no more than 88–100 characters (consistent with Black's default)
- `snake_case` for function and variable names, `PascalCase` for class names
- `UPPER_CASE` for constants
- Two blank lines between top-level function/class definitions
- No unused imports — clean them up before submitting
- Every public function/method should have a short docstring describing what it does, its parameters, and its return value

**Check locally before submitting a PR:**

```bash
pip install ruff black
ruff check .                     # zero errors
black --check src/
```

If there are style issues, auto-fix with:

```bash
black src/
ruff check . --fix
```

Fix any logical issues flagged by `ruff` (unused variables, unnecessary imports, etc.) manually.

> Note: The project may not yet have automated lint checks via CI, so style compliance will currently be checked manually during review. Adding a GitHub Actions workflow for this would also be a valuable contribution.

## Pre-PR Checklist

- [ ] Does the code follow the folder structure of the relevant module?
- [ ] Does it pass `black` and `ruff` checks?
- [ ] Have docstrings been added?
- [ ] Has the app been manually run and the change tested (`python src/app.py`)?
- [ ] Does the PR description explain what changed and why?

## Running tests locally

Before opening a PR, run the test suite locally to ensure nothing regresses:

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate
pip install -r requirements.txt
python -m pytest -q
```

## PR checklist

- Keep changes focused: one feature or fix per PR.
- Provide a short description and reference any related issue.
- Include tests for new behaviour or bug fixes.
- Update `CHANGELOG.md` and `VERSION` as appropriate for releases.

## Commit messages and branching

- Use short, imperative commit messages (e.g. "fix: handle missing ISBN").
- Make small, atomic commits where each commit represents a single logical
	change that can be reviewed independently.

## Adding a language

When adding a new language file in `assets/lang/`, copy `assets/lang/en.json`
and translate the values. Keep the same keys and run the test suite to ensure
no JSON errors.

Contributions that follow these two guidelines will be reviewed and merged quickly. Feel free to open an issue if you have any questions.
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
