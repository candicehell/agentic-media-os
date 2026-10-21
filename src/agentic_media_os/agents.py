"""Agents own task validation; providers own generation; workflows own transitions."""

from typing import Protocol, TypeVar

from agentic_media_os.models import Brief, Draft, Plan, Research
from agentic_media_os.providers import ContentProvider

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)


class Agent(Protocol[InputT, OutputT]):
    def run(self, task: InputT) -> OutputT: ...


def validate_citations(brief: Brief, source_ids: tuple[str, ...]) -> None:
    if not set(source_ids).issubset({s.id for s in brief.sources}):
        raise ValueError("Output cited an unknown source")


class ResearchAgent:
    def __init__(self, provider: ContentProvider) -> None:
        self.provider = provider

    def run(self, task: Brief) -> Research:
        result = Research.model_validate(self.provider.research(task).model_dump())
        validate_citations(task, tuple(f.source_id for f in result.findings))
        return result


class ContentPlannerAgent:
    def __init__(self, provider: ContentProvider) -> None:
        self.provider = provider

    def run(self, task: tuple[Brief, Research]) -> Plan:
        return Plan.model_validate(self.provider.plan(*task).model_dump())


class ContentWriterAgent:
    def __init__(self, provider: ContentProvider) -> None:
        self.provider = provider

    def run(self, task: tuple[Brief, Research, Plan]) -> Draft:
        result = Draft.model_validate(self.provider.write(*task).model_dump())
        validate_citations(task[0], result.source_ids)
        researched = {f.source_id for f in task[1].findings}
        if not set(result.source_ids).issubset(researched):
            raise ValueError("Draft cited a source absent from research")
        return result
