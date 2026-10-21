"""Small durable snapshot store with optimistic concurrency, not semantic memory."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Protocol
from uuid import UUID

from agentic_media_os.models import WorkflowRun


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class RunStore(Protocol):
    def create(self, run: WorkflowRun) -> None: ...

    def get(self, run_id: UUID) -> WorkflowRun: ...

    def save(self, run: WorkflowRun, expected_version: int) -> None: ...


class SQLiteRunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError("Unsupported database schema version")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS runs "
                "(id TEXT PRIMARY KEY, version INTEGER NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute("PRAGMA user_version = 1")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def create(self, run: WorkflowRun) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO runs (id, version, payload) VALUES (?, ?, ?)",
                (str(run.id), run.version, run.model_dump_json()),
            )

    def get(self, run_id: UUID) -> WorkflowRun:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM runs WHERE id = ?", (str(run_id),)
            ).fetchone()
        if row is None:
            raise NotFound("Workflow not found")
        return WorkflowRun.model_validate_json(row[0])

    def save(self, run: WorkflowRun, expected_version: int) -> None:
        if run.version != expected_version + 1:
            raise ValueError("Saved version must advance exactly once")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "UPDATE runs SET version = ?, payload = ? WHERE id = ? AND version = ?",
                (run.version, run.model_dump_json(), str(run.id), expected_version),
            )
            if cursor.rowcount != 1:
                raise Conflict("Workflow changed; reload before retrying")
