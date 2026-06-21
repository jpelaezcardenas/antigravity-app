"""
Resolution Agent Service

Generates tax_correction drafts from shadow_gl_discrepancies via LLM cascade
(Groq → Cerebras → OpenRouter → Mistral). Produces balanced journal entries
that can be enqueued to approval_queue and validated by Agent Critic.

TODO (2026-06-21): LLM cascade implementation pending — currently uses a
synthetic fixture for testing. Once LLM credentials (Groq, Cerebras API keys)
are available, replace _generate_correction_lines_fixture() with actual
_generate_correction_lines_via_llm_cascade().
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.supabase_client import get_supabase
from services.approval_queue_service import ApprovalQueueService

logger = logging.getLogger(__name__)


def _generate_correction_lines_fixture(
    tenant_id: str, discrepancy: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    FIXTURE: Generates a balanced journal entry that corrects a discrepancy.

    Real implementation will call LLM cascade (Groq → Cerebras → OpenRouter →
    Mistral) to propose the correction lines based on the discrepancy details
    and KB similarity lookup. For now, returns a synthetic balanced entry.

    Args:
        tenant_id: The tenant UUID
        discrepancy: Row from shadow_gl_discrepancies with keys:
            - cufe, dian_total_minor, erp_total_minor, variance_minor, status

    Returns:
        List of journal line dicts: [{"account": "...", "debit": ..., "credit": ...}, ...]
    """
    status = discrepancy["status"]
    dian_total = discrepancy.get("dian_total_minor", 0)
    erp_total = discrepancy.get("erp_total_minor", 0)
    variance = dian_total - (erp_total or 0)

    if status == "missing_in_erp":
        # No ERP entry exists; create a full booking of the DIAN amount
        return [
            {"account": "1105", "debit": dian_total, "credit": 0, "description": f"Registrar factura DIAN (CUFE {discrepancy['cufe']})"},
            {"account": "4135", "debit": 0, "credit": dian_total, "description": "Venta registrada"},
        ]
    elif status == "amount_mismatch":
        # Amounts differ; adjust the ERP entry to match DIAN
        if variance > 0:
            return [
                {"account": "1105", "debit": variance, "credit": 0, "description": f"Ajuste por discrepancia (CUFE {discrepancy['cufe']})"},
                {"account": "4135", "debit": 0, "credit": variance, "description": "Ajuste venta"},
            ]
        else:
            return [
                {"account": "1105", "debit": 0, "credit": abs(variance), "description": f"Reverso por discrepancia (CUFE {discrepancy['cufe']})"},
                {"account": "4135", "debit": abs(variance), "credit": 0, "description": "Reverso venta"},
            ]
    else:
        logger.warning(f"Unexpected discrepancy status: {status}")
        return []


async def generate_draft(
    tenant_id: str, cufe: str
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Generate a tax_correction draft for a single discrepancy identified by
    tenant_id + cufe. Queries the materialized view, generates correction
    lines, and enqueues to approval_queue via ApprovalQueueService.

    Returns:
        (decision_id, decision_object) if successful; (None, None) on error
    """
    supabase = get_supabase()

    discrepancies = (
        supabase.table("shadow_gl_discrepancies")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("cufe", cufe)
        .execute()
    )

    if not discrepancies.data:
        logger.warning(f"No discrepancy found for tenant {tenant_id}, cufe {cufe}")
        return None, None

    discrepancy = discrepancies.data[0]

    # Generate correction lines (fixture for now, LLM cascade TODO)
    correction_lines = _generate_correction_lines_fixture(tenant_id, discrepancy)

    if not correction_lines:
        logger.error(f"Failed to generate correction lines for discrepancy {cufe}")
        return None, None

    # Enqueue as a tax_correction draft
    success, decision, error = await ApprovalQueueService.enqueue_draft(
        draft_id=f"tax_correction_{cufe}",
        draft_type="tax_correction",
        journal_entry={"lines": correction_lines, "memo": f"Auto-generated from discrepancy {cufe}"},
    )

    if not success:
        logger.error(f"Failed to enqueue draft for {cufe}: {error}")
        return None, None

    logger.info(f"Generated tax_correction draft {decision.id} for discrepancy {cufe}")
    return decision.id, decision


async def generate_draft_with_retry(
    tenant_id: str, cufe: str, max_retries: int = 2
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Generate a tax_correction draft with Agent Critic retry logic.
    If Critic validation fails (unbalanced draft), retries up to `max_retries`
    times to regenerate a balanced version.

    Returns:
        (decision_id, decision_object) if successful after retries;
        (None, None) if all retries fail
    """
    supabase = get_supabase()

    for attempt in range(max_retries + 1):
        discrepancies = (
            supabase.table("shadow_gl_discrepancies")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("cufe", cufe)
            .execute()
        )

        if not discrepancies.data:
            logger.warning(f"No discrepancy found for tenant {tenant_id}, cufe {cufe}")
            return None, None

        discrepancy = discrepancies.data[0]

        # Generate correction lines
        correction_lines = _generate_correction_lines_fixture(tenant_id, discrepancy)

        if not correction_lines:
            logger.error(f"Failed to generate correction lines for discrepancy {cufe}")
            return None, None

        # Try enqueue
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=f"tax_correction_{cufe}_attempt{attempt}",
            draft_type="tax_correction",
            journal_entry={"lines": correction_lines, "memo": f"Auto-generated from discrepancy {cufe} (attempt {attempt + 1})"},
        )

        if success:
            logger.info(f"Generated tax_correction draft {decision.id} for {cufe} on attempt {attempt + 1}")
            return decision.id, decision

        # If error mentions Critic/balance, retry; else fail immediately
        if error and ("Critic" in error or "balance" in error or "unbalanced" in error.lower()):
            logger.warning(f"Attempt {attempt + 1} failed Critic validation for {cufe}: {error}. Retrying...")
            continue
        else:
            logger.error(f"Attempt {attempt + 1} failed with non-Critic error for {cufe}: {error}")
            return None, None

    logger.error(f"All {max_retries + 1} attempts to generate draft for {cufe} failed Critic validation")
    return None, None
