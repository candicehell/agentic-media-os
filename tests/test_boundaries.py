import asyncio
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from starlette.types import Message

from agentic_media_os.api import BodyLimit, create_app
from agentic_media_os.config import Settings
from agentic_media_os.models import Brief, WorkflowRun
from agentic_media_os.providers import LocalProvider
from agentic_media_os.store import NotFound, SQLiteRunStore
from agentic_media_os.workflows import ContentWorkflow


def test_dotenv_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("AMOS_LOG_LEVEL=WARNING\nAMOS_API_TOKEN=\n", encoding="utf-8")
    monkeypatch.delenv("AMOS_API_TOKEN", raising=False)
    monkeypatch.delenv("AMOS_LOG_LEVEL", raising=False)
    assert Settings(_env_file=dotenv).log_level == "WARNING"
    monkeypatch.setenv("AMOS_LOG_LEVEL", "ERROR")
    assert Settings(_env_file=dotenv).log_level == "ERROR"
    assert Settings(_env_file=dotenv).api_token is None


def test_bounds_and_immutable_state(brief: Brief) -> None:
    data = brief.model_dump()
    data["sources"] = [{"id": str(i), "title": "large", "text": "x" * 20000} for i in range(3)]
    with pytest.raises(ValidationError, match="50000"):
        Brief.model_validate(data)
    with pytest.raises(ValidationError):
        brief.topic = "mutated"


def test_pending_state_checks_citations(brief: Brief) -> None:
    with pytest.raises(ValidationError, match="unknown source"):
        WorkflowRun.model_validate(
            {
                "brief": brief,
                "provider": "test",
                "research": {
                    "findings": [{"text": "x", "source_id": "unknown"}],
                    "limitations": ["unknown"],
                },
            }
        )


def test_storage_failure_is_not_misreported_as_generation_failure(
    brief: Brief, store: SQLiteRunStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_save(run: WorkflowRun, expected_version: int) -> None:
        raise sqlite3.OperationalError("storage unavailable")

    monkeypatch.setattr(store, "save", broken_save)
    with pytest.raises(sqlite3.OperationalError):
        ContentWorkflow(store, LocalProvider()).start(brief)


def test_missing_run(store: SQLiteRunStore) -> None:
    with pytest.raises(NotFound):
        store.get(uuid4())


def test_every_content_endpoint_requires_auth(tmp_path: Path, brief: Brief) -> None:
    token = "x" * 40
    client = TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "auth.sqlite3", api_token=SecretStr(token), _env_file=None
            )
        )
    )
    for headers in ({}, {"Authorization": "Bearer wrong"}, {"Authorization": f"Basic {token}"}):
        for method, path in (
            ("GET", f"/workflows/{uuid4()}"),
            ("GET", f"/workflows/{uuid4()}/export"),
            ("POST", f"/workflows/{uuid4()}/review"),
            ("POST", "/workflows/content"),
        ):
            assert client.request(method, path, headers=headers, json={}).status_code == 401


def test_stream_limit_without_content_length() -> None:
    called = False
    messages: list[Message] = []

    async def app(scope: object, receive: object, send: object) -> None:
        nonlocal called
        called = True

    chunks: list[Message] = [
        {"type": "http.request", "body": b"a" * 6, "more_body": True},
        {"type": "http.request", "body": b"b" * 6, "more_body": False},
    ]

    async def receive() -> Message:
        return chunks.pop(0)

    async def send(message: Message) -> None:
        messages.append(message)

    asyncio.run(
        BodyLimit(app, max_bytes=10)(
            {"type": "http", "method": "POST", "headers": [], "path": "/"}, receive, send
        )
    )
    assert not called
    assert messages[0]["status"] == 413


def test_local_provider_handles_maximum_sources(brief: Brief) -> None:
    data = brief.model_dump()
    data["sources"] = [{"id": str(i), "title": "source", "text": "x" * 5000} for i in range(10)]
    maximum = Brief.model_validate(data)
    provider = LocalProvider()
    research = provider.research(maximum)
    draft = provider.write(maximum, research, provider.plan(maximum, research))
    assert len(draft.body) < 20000 and len(draft.source_ids) == 10
    assert all(len(f.text) == 1000 for f in research.findings)


def test_review_validation_does_not_echo_private_text(tmp_path: Path, brief: Brief) -> None:
    token = "x" * 40
    client = TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "redaction.sqlite3",
                api_token=SecretStr(token),
                _env_file=None,
            )
        )
    )
    headers = {"Authorization": f"Bearer {token}"}
    run = client.post(
        "/workflows/content", headers=headers, json=brief.model_dump(mode="json")
    ).json()
    decision = json.loads(Path("examples/review.json").read_text())
    decision["edited_draft"] = {
        "title": "private",
        "body": "private-secret",
        "source_ids": ["fake"],
    }
    response = client.post(f"/workflows/{run['id']}/review", headers=headers, json=decision)
    assert response.status_code == 422 and "private-secret" not in response.text
