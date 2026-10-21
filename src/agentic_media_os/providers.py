"""Replaceable generation boundary. The shipped provider performs no network calls."""

from typing import Protocol

from agentic_media_os.models import Brief, Draft, Finding, Plan, Research


class ContentProvider(Protocol):
    @property
    def name(self) -> str: ...

    def research(self, brief: Brief) -> Research: ...

    def plan(self, brief: Brief, research: Research) -> Plan: ...

    def write(self, brief: Brief, research: Research, plan: Plan) -> Draft: ...


class LocalProvider:
    """Deterministic extractive baseline, not an LLM or independent fact checker."""

    name = "local-extractive-v1"

    def research(self, brief: Brief) -> Research:
        return Research(
            findings=tuple(
                Finding(text=source.text[:1000], source_id=source.id) for source in brief.sources
            ),
            limitations=(
                "Only supplied notes were considered; no web research or fact checking was "
                "performed.",
                "Each source is excerpted to its first 1000 characters; review the complete notes.",
            ),
        )

    def plan(self, brief: Brief, research: Research) -> Plan:
        return Plan(
            title=brief.topic,
            audience=brief.audience,
            sections=("Context", "Source-backed notes", "Next step"),
        )

    def write(self, brief: Brief, research: Research, plan: Plan) -> Draft:
        notes = "\n\n".join(f"{f.text} [{f.source_id}]" for f in research.findings)
        body = (
            f"## {plan.sections[0]}\n\n"
            f"{brief.topic}\n\nFor: {brief.audience}\n\n"
            f"## {plan.sections[1]}\n\n{notes}\n\n"
            f"## {plan.sections[2]}\n\n{brief.goal}"
        )
        return Draft(
            title=plan.title,
            body=body,
            source_ids=tuple(dict.fromkeys(f.source_id for f in research.findings)),
        )
