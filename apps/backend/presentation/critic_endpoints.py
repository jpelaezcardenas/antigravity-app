"""
Critic API Endpoints

POST /api/v1/critic/validate - Validate journal entry double-entry bookkeeping
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

from agents.agent_critic import validate_journal_entry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/critic", tags=["critic"])


class JournalLine(BaseModel):
    """Single line in a journal entry"""

    account: str
    debit: float = 0
    credit: float = 0
    description: str = ""


class JournalEntryRequest(BaseModel):
    """Request body for journal entry validation"""

    lines: List[JournalLine]
    memo: str = ""


class ValidationResponse(BaseModel):
    """Response from critic validation"""

    is_valid: bool
    reason: str


@router.post("/validate", response_model=ValidationResponse)
async def validate_journal_entry_endpoint(request: JournalEntryRequest):
    """
    Validate a journal entry using Agent Critic.

    Checks that SUM(débitos) = SUM(créditos) for double-entry bookkeeping.

    Request:
    ```json
    {
      "lines": [
        {"account": "1105", "debit": 1000000, "credit": 0},
        {"account": "2105", "debit": 0, "credit": 1000000}
      ],
      "memo": "DIAN correction"
    }
    ```

    Response:
    ```json
    {
      "is_valid": true,
      "reason": "Entry balanced ✓"
    }
    ```
    """
    try:
        # Convert Pydantic model to dict for agent_critic
        entry = {
            "lines": [line.model_dump() for line in request.lines],
            "memo": request.memo,
        }

        is_valid, reason = validate_journal_entry(entry)

        return ValidationResponse(is_valid=is_valid, reason=reason)

    except Exception as e:
        logger.error(f"Critic endpoint error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
