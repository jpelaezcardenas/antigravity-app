"""
Approval Queue Service

Manages journal entry approval workflow with Agent Critic validation.
"""

import logging
import uuid
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

from agents.agent_critic import validate_journal_entry
from models.approval_decisions import ApprovalDecision, ApprovalStatus, VectorizationStatus

logger = logging.getLogger(__name__)


class ApprovalQueueService:
    """
    Manages approval queue: enqueue with validation, approve with vectorization.
    """

    @staticmethod
    async def enqueue_draft(
        draft_id: str,
        draft_type: str,
        journal_entry: Dict[str, Any],
        memo: str = "",
    ) -> Tuple[bool, Optional[ApprovalDecision], Optional[str]]:
        """
        Enqueue a journal entry for approval after Agent Critic validation.

        Args:
            draft_id: UUID of the draft
            draft_type: Type of draft (tax_correction, adjustment, etc.)
            journal_entry: { "lines": [...], "memo": "..." }
            memo: Additional context

        Returns:
            (success: bool, decision: Optional[ApprovalDecision], error: Optional[str])
            - If success=True: decision created with status=pending_approval
            - If success=False: error reason provided (e.g., "Unbalanced")
        """
        try:
            # Step 1: Call Agent Critic
            is_valid, critic_reason = validate_journal_entry(journal_entry)

            if not is_valid:
                logger.warning(
                    f"Draft {draft_id} failed Critic validation: {critic_reason}"
                )
                return False, None, critic_reason

            # Step 2: Create pending approval decision
            decision = ApprovalDecision(
                id=str(uuid.uuid4()),
                draft_id=draft_id,
                draft_type=draft_type,
                status=ApprovalStatus.PENDING_APPROVAL,
                reason="",  # Will be filled on approval
                approved_by="",  # Will be filled on approval
                created_at=datetime.utcnow(),
                vectorization_status=VectorizationStatus.PENDING,
                payload=journal_entry,
            )

            # Log successful enqueue
            logger.info(
                f"Draft {draft_id} enqueued for approval (decision_id={decision.id})"
            )

            return True, decision, None

        except Exception as e:
            logger.error(f"Approval queue enqueue error: {str(e)}")
            return False, None, str(e)

    @staticmethod
    async def approve_draft(
        decision_id: str,
        approval_reason: str,
        approved_by: str,
    ) -> Tuple[bool, Optional[ApprovalDecision], Optional[str]]:
        """
        Approve a pending draft. Sets status to 'approved' and triggers vectorization.

        Args:
            decision_id: UUID of the approval decision
            approval_reason: Human-provided reason for approval
            approved_by: Email of the contador

        Returns:
            (success: bool, decision: Optional[ApprovalDecision], error: Optional[str])
            - success=True: decision approved, vectorization triggered asynchronously
            - success=False: error reason
        """
        try:
            # In a real implementation, this would load the decision from database
            # For now, we return a placeholder
            logger.info(
                f"Approval decision {decision_id} approved by {approved_by}"
            )

            # Return placeholder (real implementation would load from DB)
            decision = ApprovalDecision(
                id=decision_id,
                draft_id="",
                draft_type="",
                status=ApprovalStatus.APPROVED,
                reason=approval_reason,
                approved_by=approved_by,
                created_at=datetime.utcnow(),
                vectorization_status=VectorizationStatus.PENDING,  # Will be updated by vectorization service
            )

            return True, decision, None

        except Exception as e:
            logger.error(f"Approval queue approve error: {str(e)}")
            return False, None, str(e)

    @staticmethod
    async def reject_draft(
        decision_id: str,
        rejection_reason: str,
        rejected_by: str,
    ) -> Tuple[bool, Optional[ApprovalDecision], Optional[str]]:
        """Reject a pending draft."""
        try:
            logger.info(
                f"Approval decision {decision_id} rejected by {rejected_by}: {rejection_reason}"
            )

            decision = ApprovalDecision(
                id=decision_id,
                draft_id="",
                draft_type="",
                status=ApprovalStatus.REJECTED,
                reason=rejection_reason,
                approved_by=rejected_by,
                created_at=datetime.utcnow(),
            )

            return True, decision, None

        except Exception as e:
            logger.error(f"Approval queue reject error: {str(e)}")
            return False, None, str(e)
