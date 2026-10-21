from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from agentic_media_os.agents import ResearchAgent
from agentic_media_os.config import Settings
from agentic_media_os.models import Brief, Finding, Research, Review, WorkflowRun
from agentic_media_os.providers import LocalProvider


def test_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AMOS_DATABASE_PATH", str(tmp_path / "state.sqlite3"))
    monkeypatch.setenv("AMOS_API_TOKEN", "x" * 40)
    config = Settings(_env_file=None)
    assert config.database_path == tmp_path / "state.sqlite3"
    assert "x" * 40 not in repr(config)


@pytest.mark.parametrize("value", ["short", "x" * 31, " " * 40, "é" * 40])
def test_invalid_token(value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(api_token=SecretStr(value), _env_file=None)


def test_unknown_provider() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"provider": "unimplemented"})


def test_schema_limits_and_duplicate_ids(brief: Brief) -> None:
    data = brief.model_dump()
    data["sources"] = [data["sources"][0]] * 2
    with pytest.raises(ValidationError):
        Brief.model_validate(data)
    with pytest.raises(ValidationError):
        Brief.model_validate(brief.model_dump() | {"topic": "  "})
    with pytest.raises(ValidationError):
        Brief.model_validate(brief.model_dump() | {"extra": "unexpected"})
    with pytest.raises(ValidationError):
        WorkflowRun(brief=brief, provider="local", status="approved")


def test_local_agent_has_source_provenance(brief: Brief) -> None:
    result = ResearchAgent(LocalProvider()).run(brief)
    assert result.findings[0].text == brief.sources[0].text
    assert result.findings[0].source_id == brief.sources[0].id
    assert "no web research" in result.limitations[0]


def test_agent_rejects_invented_citations(brief: Brief) -> None:
    class InventedSource(LocalProvider):
        def research(self, brief: Brief) -> Research:
            return Research(
                findings=(Finding(text="Unsupported", source_id="invented"),),
                limitations=("Not verified",),
            )

    with pytest.raises(ValueError, match="unknown source"):
        ResearchAgent(InventedSource()).run(brief)


def test_review_reject_does_not_accept_edits() -> None:
    with pytest.raises(ValidationError):
        Review.model_validate(
            {
                "expected_version": 2,
                "decision": "reject",
                "reviewer": "editor",
                "note": "revise",
                "edited_draft": {"title": "x", "body": "y", "source_ids": ["s"]},
            }
        )
