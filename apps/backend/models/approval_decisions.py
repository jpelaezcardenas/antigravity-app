"""
Approval Decisions Model

Tracks journal entry approvals and vectorization status.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ApprovalStatus(str, Enum):
    """Status of an approval decision"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class VectorizationStatus(str, Enum):
    """Status of decision vectorization"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # When OPENAI_API_KEY not available


class ApprovalDecision:
    """
    Represents a journal entry approval decision.

    Attributes:
        id: UUID of the approval decision
        draft_id: UUID of the draft journal entry
        draft_type: Type of draft (tax_correction, adjustment, etc.)
        status: Current approval status
        reason: Human-provided rationale for approval/rejection
        approved_by: Email of the contador who approved
        created_at: When the decision was made
        vectorization_status: Whether decision was converted to embedding
        vectorization_error: Error message if vectorization failed
        embedding_hash: SHA-256 hash of vectorized content
    """

    def __init__(
        self,
        id: str,
        draft_id: str,
        draft_type: str,
        status: ApprovalStatus,
        reason: str,
        approved_by: str,
        created_at: datetime,
        vectorization_status: VectorizationStatus = VectorizationStatus.PENDING,
        vectorization_error: Optional[str] = None,
        embedding_hash: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.draft_id = draft_id
        self.draft_type = draft_type
        self.status = status
        self.reason = reason
        self.approved_by = approved_by
        self.created_at = created_at
        self.vectorization_status = vectorization_status
        self.vectorization_error = vectorization_error
        self.embedding_hash = embedding_hash
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            "id": self.id,
            "draft_id": self.draft_id,
            "draft_type": self.draft_type,
            "status": self.status.value,
            "reason": self.reason,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat(),
            "vectorization_status": self.vectorization_status.value,
            "vectorization_error": self.vectorization_error,
            "embedding_hash": self.embedding_hash,
            "payload": self.payload,
        }
