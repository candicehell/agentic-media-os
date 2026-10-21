"""Future knowledge port. Workflow persistence is separately implemented in store.py."""

from typing import Literal, Protocol

from agentic_media_os.models import Model, ShortText, Text


class KnowledgeRecord(Model):
    key: ShortText
    project: ShortText
    kind: Literal[
        "business_profile", "knowledge", "previous_content", "preference", "project_context"
    ]
    text: Text


class KnowledgeStore(Protocol):
    """Explicit project scope; adapters must never return another project's records."""

    def get(self, project: str, key: str) -> KnowledgeRecord | None: ...

    def put(self, record: KnowledgeRecord) -> None: ...
