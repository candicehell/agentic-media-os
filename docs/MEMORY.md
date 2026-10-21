# State and knowledge

Implemented: SQLiteRunStore persists brief, source notes, outputs, review, original draft and fixed failure code. This is execution state, not semantic or adaptive memory. No retrieval or learning occurs.

KnowledgeStore is a proposed port with explicit project/key lookup and upsert. KnowledgeRecord kinds distinguish business profile, persistent knowledge, previous content, preferences and project context. No backend or workflow consumer is implemented. Briefs explicitly supply context.

Future Markdown stores must bound file sizes and reject symlink/path traversal escapes. PostgreSQL needs migrations, workspace-scoped access and backup/retention. Add pgvector only with evaluated retrieval requirements. Obsidian can edit Markdown; it is not a runtime dependency.

Do not mix transient run state with preferences. Current SQLite is plaintext and has no deletion endpoint or automated retention. Operators must manage file access, backups and deletion.
