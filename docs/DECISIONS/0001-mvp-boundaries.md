# ADR 0001: explicit local content workflow

Status: accepted for the MVP foundation, 2026-10-21.

## Context

The repository was a README-only concept. A first implementation must demonstrate real state and review without API keys or infrastructure overhead.

## Decisions

- Python 3.12+, Pydantic contracts, FastAPI and CLI sharing one service.
- Three explicit synchronous steps instead of LangGraph/LangChain: no branching or resumable graph requirement exists yet.
- An extractive local provider demonstrates provenance and review without implying live AI research. Future adapters implement ContentProvider and the same validation.
- Standard-library SQLite instead of mandatory PostgreSQL; RunStore isolates persistence with conditional updates and schema versioning.
- Persist pending state; approve/reject with expected versions. Only persisted approval permits export.
- Separate proposed knowledge from workflow state. No vector database without retrieval requirements/evaluation.
- Define publishing port, ship no dummy n8n/MCP workflows.
- Adopt MIT for the new foundation. Maintainers should confirm licensing intent before release.

## Consequences

Small setup, offline after installation, basic drafts requiring editorial work. SQLite is local persistence, not distributed orchestration. Shared tokens cannot establish reviewer identity. Crash recovery, create idempotency and external tool security remain future requirements.

Revisit orchestration for branching/parallelism/durable resumption and persistence before multiple service instances. Replace a port only alongside an exercised end-to-end path.
