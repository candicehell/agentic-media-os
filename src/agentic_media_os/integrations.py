"""Future publishing port; there is deliberately no live publishing adapter."""

from typing import Protocol

from agentic_media_os.models import ApprovedContent, Model, ShortText


class PublicationReceipt(Model):
    external_id: ShortText
    platform: ShortText


class PublishingAdapter(Protocol):
    def publish(self, content: ApprovedContent, *, idempotency_key: str) -> PublicationReceipt:
        """Consume a service-issued export; implement timeout and idempotency handling."""
        ...
