import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agentic_media_os.models import Brief, Draft, Research, Review
from agentic_media_os.providers import LocalProvider
from agentic_media_os.store import Conflict, SQLiteRunStore
from agentic_media_os.workflows import ContentWorkflow, advance


def decision(version: int = 2, choice: str = "approve", draft: Draft | None = None) -> Review:
    return Review.model_validate(
        {
            "expected_version": version,
            "decision": choice,
            "reviewer": "editor",
            "note": "Read and reviewed",
            "edited_draft": draft,
        }
    )


def test_happy_path_with_edit_and_restart(
    brief: Brief, workflow: ContentWorkflow, store: SQLiteRunStore
) -> None:
    run = workflow.start(brief)
    assert run.status == "pending_approval" and run.version == 2
    assert run.research and run.plan and run.draft
    with pytest.raises(Conflict):
        workflow.export(run.id)
    edited = Draft(title="Edited title", body="Editor checked this.", source_ids=("style-guide",))
    approved = workflow.review(run.id, decision(draft=edited))
    assert approved.version == 3 and approved.original_draft == run.draft
    restarted = ContentWorkflow(SQLiteRunStore(store.path), LocalProvider())
    exported = restarted.export(run.id)
    assert exported.draft == edited
    assert exported.reviewer == "editor"
    with pytest.raises(Conflict):
        workflow.review(run.id, decision(version=3))


def test_rejected_is_terminal(brief: Brief, workflow: ContentWorkflow) -> None:
    run = workflow.start(brief)
    assert workflow.review(run.id, decision(choice="reject")).status == "rejected"
    with pytest.raises(Conflict):
        workflow.export(run.id)


def test_stale_review_and_unknown_source(brief: Brief, workflow: ContentWorkflow) -> None:
    run = workflow.start(brief)
    with pytest.raises(Conflict):
        workflow.review(run.id, decision(version=1))
    with pytest.raises(ValueError):
        workflow.review(run.id, decision(draft=Draft(title="x", body="y", source_ids=("unknown",))))
    assert workflow.store.get(run.id).status == "pending_approval"


def test_failure_is_durable_and_redacted(
    brief: Brief, store: SQLiteRunStore, caplog: pytest.LogCaptureFixture
) -> None:
    class Failing(LocalProvider):
        def research(self, brief: Brief) -> Research:
            raise RuntimeError("secret-provider-key-and-private-prompt")

    with caplog.at_level(logging.INFO):
        result = ContentWorkflow(store, Failing()).start(brief)
    assert result.status == "failed" and result.error_code == "generation_failed"
    assert store.get(result.id) == result
    assert "secret-provider" not in result.model_dump_json() + caplog.text


def test_competing_storage_updates(brief: Brief, store: SQLiteRunStore) -> None:
    run = ContentWorkflow(store, LocalProvider()).start(brief)
    updated = advance(run, status="failed", error_code="generation_failed")

    def save() -> str:
        try:
            store.save(updated, run.version)
            return "saved"
        except Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: save(), range(2))) == ["conflict", "saved"]


def test_unsupported_schema(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 99")
    with pytest.raises(RuntimeError, match="Unsupported"):
        SQLiteRunStore(path)
