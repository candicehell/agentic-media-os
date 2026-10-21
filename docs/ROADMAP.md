# Roadmap

## NOW — foundation

This branch implements the typed three-agent workflow, local no-key path, SQLite state, review/edit/reject, approved export, CLI/API, tests, checks and documentation. Acceptance: install, generate, inspect, approve and export without paid services.

Before release: confirm MIT and project policies, run GitHub CI, validate Docker with Docker Engine.

## NEXT — one useful creator operation

1. Implement one model adapter with structured output, timeouts/cost budgets, no-key contract tests and source-support evaluation. Measure quality against the local baseline.
2. Add attempt records, create idempotency, bounded workers and crash recovery before slow external providers. Test termination and duplicate requests.
3. Implement project-scoped Markdown knowledge with explicit context selection. Test bounded files, traversal, symlinks and retention.
4. Add authenticated identities before shared approval; derive reviewer identity from authentication and test permissions.
5. Validate with human editors; document acceptance criteria and measure source quality and editorial friction.

## LATER — extend against demonstrated needs

- PostgreSQL/migrations for shared persistence; test upgrades and backup restore.
- Evaluated podcast/repurposing agents with concrete task contracts.
- n8n/MCP with least privilege and signed, replay-safe ingress.
- One publisher with durable receipts, idempotency and reconciliation.
- Metrics, traces, rate limits, deadlines, secret storage and operational runbooks before hosting.
- Multiple workspaces only after isolation is enforced/tested across state, knowledge and integrations.

No delivery-date or traction claims. LangGraph is a candidate when branching/durable resumption justifies it.
