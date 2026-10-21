"""Immutable domain contracts shared by agents, persistence, CLI and API."""

from datetime import UTC, datetime
from typing import Annotated, Literal, Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
SourceId = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(Model):
    id: SourceId
    title: ShortText
    text: Text


class Brief(Model):
    topic: ShortText
    audience: ShortText
    goal: ShortText
    sources: tuple[Source, ...] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("Source IDs must be unique")
        if sum(len(s.text) for s in self.sources) > 50000:
            raise ValueError("Combined source text must not exceed 50000 characters")
        return self


class Finding(Model):
    text: Text
    source_id: SourceId


class Research(Model):
    findings: tuple[Finding, ...] = Field(min_length=1, max_length=10)
    limitations: tuple[ShortText, ...] = Field(min_length=1, max_length=10)


class Plan(Model):
    title: ShortText
    audience: ShortText
    sections: tuple[ShortText, ...] = Field(min_length=1, max_length=10)


class Draft(Model):
    title: ShortText
    body: Text
    source_ids: tuple[SourceId, ...] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def unique_citations(self) -> Self:
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Draft source IDs must be unique")
        return self


class Review(Model):
    expected_version: int = Field(ge=1)
    decision: Literal["approve", "reject"]
    reviewer: ShortText
    note: ShortText
    edited_draft: Draft | None = None

    @model_validator(mode="after")
    def edit_only_on_approval(self) -> Self:
        if self.decision == "reject" and self.edited_draft is not None:
            raise ValueError("Edits are only accepted with approval")
        return self


Status = Literal["running", "pending_approval", "approved", "rejected", "failed"]


class WorkflowRun(Model):
    id: UUID = Field(default_factory=uuid4)
    version: int = Field(default=1, ge=1)
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Status = "running"
    brief: Brief
    provider: ShortText
    research: Research | None = None
    plan: Plan | None = None
    draft: Draft | None = None
    review: Review | None = None
    original_draft: Draft | None = None
    error_code: Literal["generation_failed"] | None = None

    @model_validator(mode="after")
    def coherent_state(self) -> Self:
        if self.status in {"pending_approval", "approved", "rejected"}:
            if self.research is None or self.plan is None or self.draft is None:
                raise ValueError("Completed generation requires research, plan and draft")
        if self.status in {"approved", "rejected"}:
            expected = "approve" if self.status == "approved" else "reject"
            if self.review is None or self.review.decision != expected:
                raise ValueError("Terminal review state requires matching review")
            if self.original_draft is None or self.review.expected_version != self.version - 1:
                raise ValueError("Reviewed state requires original draft and matching version")
        elif self.review is not None or self.original_draft is not None:
            raise ValueError("Unreviewed state cannot contain a review")
        if (self.status == "failed") != (self.error_code is not None):
            raise ValueError("Only failed runs contain an error code")
        if self.updated_at < self.created_at:
            raise ValueError("Update time precedes creation time")
        source_ids = {s.id for s in self.brief.sources}
        if self.research is not None:
            if any(f.source_id not in source_ids for f in self.research.findings):
                raise ValueError("Research references unknown source")
        for draft in (self.draft, self.original_draft):
            if draft is not None and not set(draft.source_ids).issubset(source_ids):
                raise ValueError("Draft references unknown source")
        return self


class ApprovedContent(Model):
    workflow_id: UUID
    version: int
    draft: Draft
    sources: tuple[Source, ...]
    reviewer: ShortText
    approved_at: AwareDatetime
