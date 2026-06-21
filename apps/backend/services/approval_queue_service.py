"""
Approval Queue Service

Manages journal entry approval workflow with Agent Critic validation.
Persists to the `approval_queue` table in Supabase.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional

from agents.agent_critic import validate_journal_entry
from core.supabase_client import get_supabase
from models.approval_decisions import ApprovalDecision, ApprovalStatus, VectorizationStatus
from services.embeddings_service import EmbeddingsService

logger = logging.getLogger(__name__)

# Draft types representing journal entries that must balance debits/credits.
# Other draft types (risk_review, audit_report_signoff, taty_escalation,
# social_reply, ...) carry their own payload shape and skip Critic validation.
JOURNAL_ENTRY_DRAFT_TYPES = {"tax_correction"}


def _row_to_decision(row: Dict[str, Any]) -> ApprovalDecision:
    return ApprovalDecision(
        id=row["id"],
        draft_id=row["draft_id"],
        draft_type=row["draft_type"],
        status=ApprovalStatus(row["status"]),
        reason=row["reason"],
        approved_by=row["approved_by"],
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        vectorization_status=VectorizationStatus(row["vectorization_status"]),
        vectorization_error=row.get("vectorization_error"),
        embedding_hash=row.get("embedding_hash"),
        payload=row.get("payload") or {},
    )


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
        Enqueue a draft for approval.

        Journal-entry draft types (tax_correction) are validated by Agent
        Critic first; only balanced entries are persisted. Other draft types
        skip balance validation and are enqueued directly.

        Returns:
            (success: bool, decision: Optional[ApprovalDecision], error: Optional[str])
        """
        try:
            if draft_type in JOURNAL_ENTRY_DRAFT_TYPES:
                is_valid, critic_reason = validate_journal_entry(journal_entry)
                if not is_valid:
                    logger.warning(
                        f"Draft {draft_id} failed Critic validation: {critic_reason}"
                    )
                    return False, None, critic_reason

            decision = ApprovalDecision(
                id=str(uuid.uuid4()),
                draft_id=draft_id,
                draft_type=draft_type,
                status=ApprovalStatus.PENDING_APPROVAL,
                reason="",
                approved_by="",
                created_at=datetime.utcnow(),
                vectorization_status=VectorizationStatus.PENDING,
                payload=journal_entry,
            )

            supabase = get_supabase()
            supabase.table("approval_queue").insert(decision.to_dict()).execute()

            logger.info(
                f"Draft {draft_id} enqueued for approval (decision_id={decision.id})"
            )

            return True, decision, None

        except Exception as e:
            logger.error(f"Approval queue enqueue error: {str(e)}")
            return False, None, str(e)

    @staticmethod
    async def list_drafts(
        status: Optional[str] = None,
        draft_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[ApprovalDecision]:
        """
        List drafts across all draft_type values, optionally filtered by
        status, draft_type, and tenant_id.
        """
        supabase = get_supabase()
        query = supabase.table("approval_queue").select("*")

        if status:
            query = query.eq("status", status)
        if draft_type:
            query = query.eq("draft_type", draft_type)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)

        result = query.order("created_at", desc=True).execute()
        return [_row_to_decision(row) for row in result.data]

    @staticmethod
    async def approve_draft(
        decision_id: str,
        approval_reason: str,
        approved_by: str,
    ) -> Tuple[bool, Optional[ApprovalDecision], Optional[str]]:
        """
        Approve a pending draft. Sets status to 'approved' and triggers
        vectorization asynchronously (non-blocking, failure does not roll
        back the approval).
        """
        try:
            supabase = get_supabase()

            existing = (
                supabase.table("approval_queue")
                .select("*")
                .eq("id", decision_id)
                .execute()
            )
            if not existing.data:
                return False, None, f"Decision {decision_id} not found"

            updated = (
                supabase.table("approval_queue")
                .update(
                    {
                        "status": ApprovalStatus.APPROVED.value,
                        "reason": approval_reason,
                        "approved_by": approved_by,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", decision_id)
                .execute()
            )

            decision = _row_to_decision(updated.data[0])

            logger.info(f"Approval decision {decision_id} approved by {approved_by}")

            # For tax_correction drafts, create an executor_outbox job (synchronous)
            if decision.draft_type == "tax_correction":
                ApprovalQueueService._create_outbox_job_sync(decision_id, decision)

            asyncio.create_task(
                ApprovalQueueService._vectorize_and_persist(decision)
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
            supabase = get_supabase()

            existing = (
                supabase.table("approval_queue")
                .select("id")
                .eq("id", decision_id)
                .execute()
            )
            if not existing.data:
                return False, None, f"Decision {decision_id} not found"

            updated = (
                supabase.table("approval_queue")
                .update(
                    {
                        "status": ApprovalStatus.REJECTED.value,
                        "reason": rejection_reason,
                        "approved_by": rejected_by,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", decision_id)
                .execute()
            )

            decision = _row_to_decision(updated.data[0])

            logger.info(
                f"Approval decision {decision_id} rejected by {rejected_by}: {rejection_reason}"
            )

            return True, decision, None

        except Exception as e:
            logger.error(f"Approval queue reject error: {str(e)}")
            return False, None, str(e)

    @staticmethod
    def _create_outbox_job_sync(decision_id: str, decision: ApprovalDecision) -> None:
        """
        Create an executor_outbox row for tax_correction drafts.
        Synchronous and non-blocking at the application level (DB insert is fast).
        Exceptions are logged but do not roll back the approval.
        """
        supabase = get_supabase()
        try:
            supabase.table("executor_outbox").insert(
                {
                    "approval_decision_id": decision_id,
                    "status": "pending",
                    "attempts": 0,
                    "payload": {
                        "approval_id": decision_id,
                        "draft_id": decision.draft_id,
                        "draft_type": decision.draft_type,
                        "reason": decision.reason,
                        "approved_by": decision.approved_by,
                        "payload": decision.payload,
                    },
                }
            ).execute()
            logger.info(f"Created executor_outbox job for approval {decision_id}")
        except Exception as e:
            logger.error(f"Failed to create executor_outbox job for approval {decision_id}: {str(e)}")

    @staticmethod
    async def _vectorize_and_persist(decision: ApprovalDecision) -> None:
        """Background task: vectorize an approved decision, never raises."""
        supabase = get_supabase()
        try:
            supabase.table("approval_queue").update(
                {"vectorization_status": VectorizationStatus.IN_PROGRESS.value}
            ).eq("id", decision.id).execute()

            result = await EmbeddingsService.vectorize_approval_decision(
                {
                    "draft_id": decision.draft_id,
                    "draft_type": decision.draft_type,
                    "decision": "approved",
                    "reason": decision.reason,
                    "approved_by": decision.approved_by,
                    "payload": decision.payload,
                }
            )

            if result["vectorized"]:
                persisted, persist_error = await EmbeddingsService.persist_embedding_to_supabase(
                    approval_id=decision.id,
                    content=result["content"],
                    embedding=result["embedding"],
                    metadata={
                        "approval_id": decision.id,
                        "decided_by": decision.approved_by,
                        "timestamp": datetime.utcnow().isoformat(),
                        "confidence": result["confidence"],
                    },
                    supabase_client=supabase,
                )
                final_status = (
                    VectorizationStatus.SUCCESS if persisted else VectorizationStatus.FAILED
                )
                error_msg = persist_error
            else:
                final_status = (
                    VectorizationStatus.SKIPPED
                    if result.get("error") is None
                    else VectorizationStatus.FAILED
                )
                error_msg = result.get("error")

            supabase.table("approval_queue").update(
                {
                    "vectorization_status": final_status.value,
                    "vectorization_error": error_msg,
                    "embedding_hash": result.get("embedding_hash"),
                }
            ).eq("id", decision.id).execute()

        except Exception as e:
            logger.error(f"Vectorization background task failed for {decision.id}: {str(e)}")
            try:
                supabase.table("approval_queue").update(
                    {
                        "vectorization_status": VectorizationStatus.FAILED.value,
                        "vectorization_error": str(e),
                    }
                ).eq("id", decision.id).execute()
            except Exception:
                pass
