"""Synchronous content orchestration with a persisted human review boundary."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from agentic_media_os.agents import (
    ContentPlannerAgent,
    ContentWriterAgent,
    ResearchAgent,
    validate_citations,
)
from agentic_media_os.models import ApprovedContent, Brief, Review, WorkflowRun
from agentic_media_os.providers import ContentProvider
from agentic_media_os.store import Conflict, RunStore

logger = logging.getLogger(__name__)


def advance(run: WorkflowRun, **changes: object) -> WorkflowRun:
    # model_copy(update=...) bypasses validation; revalidate every state transition instead.
    return WorkflowRun.model_validate(
        run.model_dump() | changes | {"version": run.version + 1, "updated_at": datetime.now(UTC)}
    )


class ContentWorkflow:
    def __init__(self, store: RunStore, provider: ContentProvider) -> None:
        self.store = store
        self.provider = provider

    def start(self, brief: Brief) -> WorkflowRun:
        run = WorkflowRun(brief=brief, provider=self.provider.name)
        self.store.create(run)
        logger.info("workflow_started id=%s version=%s", run.id, run.version)
        try:
            research = ResearchAgent(self.provider).run(brief)
            plan = ContentPlannerAgent(self.provider).run((brief, research))
            draft = ContentWriterAgent(self.provider).run((brief, research, plan))
            completed = advance(
                run, status="pending_approval", research=research, plan=plan, draft=draft
            )
        except Exception:
            # Provider exceptions may contain prompts, credentials or private source notes.
            # Persist and log only a fixed code. Storage failures propagate separately.
            completed = advance(run, status="failed", error_code="generation_failed")
        self.store.save(completed, run.version)
        logger.info("workflow_finished id=%s status=%s", completed.id, completed.status)
        return completed

    def review(self, run_id: UUID, review: Review) -> WorkflowRun:
        run = self.store.get(run_id)
        if run.version != review.expected_version or run.status != "pending_approval":
            raise Conflict("Only the current pending draft can be reviewed")
        draft = review.edited_draft or run.draft
        if draft is None:
            raise Conflict("Pending workflow has no draft")
        validate_citations(run.brief, draft.source_ids)
        completed = advance(
            run,
            status="approved" if review.decision == "approve" else "rejected",
            draft=draft,
            original_draft=run.draft,
            review=review,
        )
        self.store.save(completed, review.expected_version)
        logger.info("workflow_reviewed id=%s status=%s", completed.id, completed.status)
        return completed

    def export(self, run_id: UUID) -> ApprovedContent:
        run = self.store.get(run_id)
        if run.status != "approved" or run.draft is None or run.review is None:
            raise Conflict("Export requires an approved workflow")
        return ApprovedContent(
            workflow_id=run.id,
            version=run.version,
            draft=run.draft,
            sources=run.brief.sources,
            reviewer=run.review.reviewer,
            approved_at=run.updated_at,
        )
