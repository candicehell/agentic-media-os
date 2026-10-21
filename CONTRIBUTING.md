# Contributing

Start with the README and architecture, then run the example. Small, tested vertical changes are more useful than speculative frameworks. Open a focused issue before changing public contracts or adding dependencies.

## Environment and checks

Requires Python 3.12+. Create/activate a venv and install `python -m pip install -e ".[dev]"` for a simple install. For reproducible development install uv 0.13.4, then `uv sync --frozen --extra dev`. The committed uv.lock pins transitive dependencies; do not edit it by hand. Use `uv run --frozen --extra dev` before the commands below when using uv.

```sh
ruff check .
ruff format --check .
mypy src
pytest
```

Run the CLI example and inspect its draft, approve it and export it. Tests use temporary SQLite files and fakes, never paid APIs. Keep source text, secrets and database files out of fixtures and commits.

## Conventions

Use typed Python, explicit dependency injection and immutable Pydantic contracts. Keep generation in providers, task validation in agents, transitions in workflows, and persistence in stores. Add regression tests for state, security and failure behavior. Avoid speculative directories, broad refactors and dummy adapters. Explain schema changes in an ADR and provide a migration before changing persisted data. Do not log private content or raw provider errors.

Keep documentation truthful: label proposed interfaces and unsupported operations. Run meaningful checks after changes. Do not add dependencies solely because they appear in the vision.

## Pull requests

Describe the problem, resulting behavior, validation, and limits. Use the PR template. Keep changes reviewable. Contributions are under the repository's MIT license; submit only code/content you have rights to contribute. Maintainers decide merges and releases. No CLA, paid support, response SLA, or formal governance body is currently established.

## Dependency updates

Change pyproject constraints intentionally, regenerate with `uv lock`, run `uv sync --frozen --extra dev`, and rerun checks. `uv run --frozen --extra dev pip-audit` checks the installed environment against public advisories and requires network. It cannot prove dependency safety. Dependabot proposes updates; maintainers review behavior changes.
