from pathlib import Path

import pytest

from agentic_media_os.models import Brief
from agentic_media_os.providers import LocalProvider
from agentic_media_os.store import SQLiteRunStore
from agentic_media_os.workflows import ContentWorkflow


@pytest.fixture
def brief() -> Brief:
    return Brief.model_validate_json(Path("examples/brief.json").read_text(encoding="utf-8"))


@pytest.fixture
def store(tmp_path: Path) -> SQLiteRunStore:
    return SQLiteRunStore(tmp_path / "runs.sqlite3")


@pytest.fixture
def workflow(store: SQLiteRunStore) -> ContentWorkflow:
    return ContentWorkflow(store, LocalProvider())
