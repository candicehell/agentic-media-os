# Validation record

Validated on Windows with CPython 3.12.14 on 2026-10-21. This records evidence from implementation, not a claim of production certification.

| Check | Result |
| --- | --- |
| Clean `uv sync --frozen --extra dev` | Passed in an isolated task-local environment |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed |
| `mypy src` (strict) | Passed, 11 source files |
| `pytest` | 30 passed, no warnings in the locked environment |
| `python -m pip check` | No broken requirements |
| `pip-audit --local` | No known third-party dependency vulnerabilities; unpublished local project skipped by the advisory service |
| Source distribution and wheel build | Passed; wheel built from sdist |
| Frozen non-editable runtime-only install | Passed |
| Actual `amos` console processes | Generate, show, review and export passed |
| Real localhost Uvicorn HTTP server | Authentication, generation, unapproved export rejection, review and export passed |
| Server restart | Approved export survived restart unchanged |
| GitHub Linux matrix (Python 3.12 and 3.13) | Passed in both push and pull-request CI |
| Docker build and running-container smoke test | Passed in GitHub CI |
| Local Markdown links | Checked for existing targets |
| YAML and issue-template metadata | Parsed; CI action pins, read permissions, loopback binding and read-only container configuration inspected |
| Diff whitespace and basic credential-pattern scan | Clean; test tokens are synthetic |

Tests cover configuration and dotenv precedence, schema bounds and immutability, citation validation, agent behavior with fakes, workflow success/failure, durable state, edited/rejected/stale reviews, competing conditional updates, unknown database schemas, storage failure propagation, all content endpoint authentication, API validation/redaction, streamed body bounds and CLI behavior.

## Limits of verification

Docker Engine was unavailable locally. After repository access was configured, the Linux Python 3.12/3.13 matrix and actual Docker build/container smoke test passed for implementation commit `acbc93108512de9874999f3b4c1e471e20852114` in both [push CI](https://github.com/candicehell/agentic-media-os/actions/runs/39678437595) and [pull-request CI](https://github.com/candicehell/agentic-media-os/actions/runs/39678463811). The published implementation tree was verified identical to the locally tested tree. These remote results complement the Windows checks above.

The first advisory scan found the initial virtual environment's old bundled pip. It was upgraded; the clean locked environment was scanned again without vulnerability ignores. The initial test-client deprecation was fixed by using the supported httpx2 development dependency.

No live model, external research, n8n, MCP, platform publication, multi-user security or load testing was performed because those capabilities are not implemented.

## Changed file groups

- `README.md`: replaces concept/recruitment-first description with runnable scope and credible collaboration positioning.
- `src/agentic_media_os/`: domain models, settings, provider/agent boundaries, workflow service, SQLite store, CLI/API and proposed knowledge/publishing ports.
- `tests/`: configuration, domain, workflow, persistence, API, CLI and boundary regression cases.
- `examples/`: synthetic brief and explicit review request.
- `docs/`: original audit, architecture, setup, agents, workflows, memory, integrations, roadmap and ADR.
- `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore`: packaging, reproducible dependencies and local configuration.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: optional local container deployment.
- `.github/`: CI, Dependabot, four issue templates and PR template.
- `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `VALIDATION.md`: project policies and validation evidence.

## Maintainer actions before release

Review and merge the branch, confirm MIT licensing intent, enable GitHub private vulnerability reporting, and check that the latest PR checks remain green. Generate a private API token before API startup. Shared/remote production operation requires the hardening and recovery work in the roadmap.
