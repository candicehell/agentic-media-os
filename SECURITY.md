# Security policy

This is an early local single-operator MVP, not a hardened hosted service. Only the latest main branch receives best-effort security fixes; no response-time or maintenance SLA is promised.

## Reporting

Use the repository's GitHub **Security → Advisories → Report a vulnerability** when enabled. Do not put exploit details, tokens or private source notes in public issues. Private vulnerability reporting has not been verified as enabled; if unavailable, ask the owner to enable it without disclosing details, or use a private contact channel listed on their GitHub profile. No dedicated security mailbox is currently established.

Include affected revision, minimal synthetic reproduction, impact and proposed mitigation. Coordinate disclosure privately where possible.

## Current boundary

- API requires a random bearer token; health and schema are public. Keep host binding on loopback.
- One token grants access to every workflow; reviewer labels are self-reported. No users, roles or tenant isolation.
- CLI and filesystem access are trusted operator access. Database edits can bypass application approval.
- SQLite, drafts, sources and backups are plaintext. Manage file permissions and retention.
- No source URLs are fetched, shell commands executed or arbitrary tools invoked by the application.
- Input bounds, source-reference validation, parameterized SQL, conditional review writes and fixed provider error codes reduce the current attack surface.
- Authentication is not rate limiting. Remote deployment needs TLS, identities, authorization, request deadlines and ingress controls.
- Dependency advisories are checked separately; scanning does not guarantee safety.
- Treat exported source text and Markdown as untrusted content. A future UI must escape/sanitize rendering.

Do not commit .env, API keys, private notes or databases. Rotate exposed tokens. Future providers/tools need least privilege, prompt-injection defenses, timeout/cost limits and secret redaction tests before use with real data.
