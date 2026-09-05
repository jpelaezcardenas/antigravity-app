"""
Gmail API client — read inbox, download attachments, mark processed.

Uses OAuth2 with a locally-stored token (token.json). The credentials.json is
obtained once from the Google Cloud Console (OAuth 2.0 Client ID, Desktop app type).
Run `python gmail_client.py --auth` to perform the one-time OAuth2 flow.

Never stores credentials in Railway or any cloud env var — stays local (sovereign node).
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GmailAttachment:
    message_id: str
    sender_email: str
    subject: str
    filename: str
    mime_type: str
    content: bytes


def _build_service(token_path: str, credentials_path: str) -> Any:
    """Build and return an authenticated Gmail API service."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise ImportError(
            "Gmail API libraries not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        ) from exc

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",  # needed to apply labels
    ]

    creds = None
    token_file = Path(token_path)
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


class GmailClient:
    """Thin wrapper around the Gmail API for the hermes-gmail-poller."""

    def __init__(self, token_path: str, credentials_path: str) -> None:
        self._token_path = token_path
        self._credentials_path = credentials_path
        self._service: Any = None

    def _svc(self) -> Any:
        if self._service is None:
            self._service = _build_service(self._token_path, self._credentials_path)
        return self._service

    def _get_or_create_label(self, label_name: str) -> str:
        """Return the Gmail label ID for label_name, creating it if needed."""
        labels = self._svc().users().labels().list(userId="me").execute()
        for lbl in labels.get("labels", []):
            if lbl["name"] == label_name:
                return lbl["id"]
        created = (
            self._svc()
            .users()
            .labels()
            .create(userId="me", body={"name": label_name, "labelListVisibility": "labelShow"})
            .execute()
        )
        return created["id"]

    def list_unprocessed_messages(
        self, processed_label: str, max_results: int = 20
    ) -> list[dict[str, Any]]:
        """Return messages in INBOX that are unread, have attachments, and are NOT labeled processed."""
        query = f"in:inbox has:attachment -label:{processed_label}"
        resp = (
            self._svc()
            .users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return resp.get("messages", [])

    def get_message_metadata(self, message_id: str) -> dict[str, Any]:
        return (
            self._svc()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="metadata")
            .execute()
        )

    def get_message_full(self, message_id: str) -> dict[str, Any]:
        return (
            self._svc()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        resp = (
            self._svc()
            .users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = resp.get("data", "")
        return base64.urlsafe_b64decode(data + "==")  # pad to valid base64

    def mark_processed(self, message_id: str, processed_label: str) -> None:
        """Apply the processed label and mark as read."""
        label_id = self._get_or_create_label(processed_label)
        self._svc().users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": [label_id], "removeLabelIds": ["UNREAD"]},
        ).execute()

    def list_attachments(
        self, message: dict[str, Any], supported_mime_types: list[str]
    ) -> list[dict[str, Any]]:
        """Return attachment part descriptors from a full message that match supported MIME types."""
        attachments: list[dict[str, Any]] = []

        def _walk(parts: list[dict[str, Any]]) -> None:
            for part in parts:
                if part.get("filename") and part.get("body", {}).get("attachmentId"):
                    mime = part.get("mimeType", "")
                    if any(mime.startswith(t) for t in supported_mime_types):
                        attachments.append(part)
                if part.get("parts"):
                    _walk(part["parts"])

        _walk(message.get("payload", {}).get("parts", []))
        return attachments

    def extract_sender(self, message: dict[str, Any]) -> str:
        """Extract the From: email address from message metadata."""
        headers = message.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == "from":
                raw = h.get("value", "")
                # "Name <email@example.com>" → "email@example.com"
                if "<" in raw and ">" in raw:
                    return raw.split("<")[1].rstrip(">").strip().lower()
                return raw.strip().lower()
        return ""
