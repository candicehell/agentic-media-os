# Integrations

No platform, MCP server or n8n workflow is implemented. PublishingAdapter defines a future effect boundary receiving an approved service export plus idempotency key and returning a receipt. A typed object alone is not an approval check: entry points must obtain payloads from persisted approved state.

To add an adapter:

1. Propose capability, auth scopes, schemas, privacy and failure behavior.
2. Keep SDKs, credentials, endpoints and platform formats inside the adapter.
3. Use configured allowlisted destinations, TLS, timeouts, bounded retries and response-size bounds. Redirects and supplied URLs are an SSRF boundary.
4. Require persisted approval, derive idempotency from workflow/version/destination, and durably reconcile receipts after ambiguous failures.
5. Test permission errors, rate limits, duplicates, timeouts and redaction using fakes.

Agentic Media OS owns intelligence, state and orchestration policy. n8n can connect external systems through authenticated APIs. MCP can standardize agent tool/context access. Neither replaces approval. Future webhooks need signatures, replay protection and schema validation. Do not expose generic tool execution or ship dummy workflows.
