"""Pydantic models for the Chatwoot webhook payload shapes this bridge cares about.

Chatwoot's webhook payload has many more fields than modeled here; only the
fields this bridge reads are declared, and unknown fields are ignored (not
forbidden) so a Chatwoot version bump doesn't break the bridge on unrelated
payload additions.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ChatwootAttachment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    file_type: Optional[str] = None
    data_url: Optional[str] = None


class ChatwootSender(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    phone_number: Optional[str] = None


class ChatwootConversation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    labels: list[str] = []


class ChatwootContact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    phone_number: Optional[str] = None


class ChatwootWebhookPayload(BaseModel):
    """The subset of Chatwoot's `message_created` (and other) webhook events
    the bridge inspects to decide whether/how to process a message."""

    model_config = ConfigDict(extra="ignore")

    event: str
    message_type: Optional[str] = None
    private: bool = False
    content: Optional[str] = None
    conversation: Optional[ChatwootConversation] = None
    sender: Optional[ChatwootSender] = None
    attachments: list[ChatwootAttachment] = []

    def conversation_id(self) -> Optional[int]:
        return self.conversation.id if self.conversation else None

    def labels(self) -> list[str]:
        return self.conversation.labels if self.conversation else []

    def contact_phone(self) -> Optional[str]:
        return self.sender.phone_number if self.sender else None

    def contact_id(self) -> Optional[int]:
        return self.sender.id if self.sender else None
