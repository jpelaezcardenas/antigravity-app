"""
Tests for Decision Vectorization Service.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from services.embeddings_service import EmbeddingsService


def test_extract_semantic_summary():
    """Extract semantic summary from approval."""
    approval = {
        "draft_id": "draft-001",
        "draft_type": "tax_correction",
        "decision": "approved",
        "reason": "Contexia's own invoice, matches DIAN",
        "approved_by": "contador@contexia.com",
        "payload": {
            "lines": [
                {"account": "1105", "debit": 1000000, "credit": 0},
                {"account": "2105", "debit": 0, "credit": 1000000},
            ]
        },
    }

    summary = EmbeddingsService.extract_semantic_summary(approval)
    assert "tax_correction" in summary
    assert "approved" in summary
    assert "Contexia's own invoice" in summary


def test_compute_content_hash():
    """Compute SHA-256 hash of content."""
    content = "Test content for hashing"
    hash1 = EmbeddingsService.compute_content_hash(content)
    hash2 = EmbeddingsService.compute_content_hash(content)

    # Same content should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex string length


def test_compute_content_hash_unique():
    """Different content produces different hashes."""
    content1 = "Content A"
    content2 = "Content B"

    hash1 = EmbeddingsService.compute_content_hash(content1)
    hash2 = EmbeddingsService.compute_content_hash(content2)

    assert hash1 != hash2


@pytest.mark.asyncio
async def test_vectorize_approval_no_api_key():
    """Vectorization fails gracefully when no API key."""
    # Temporarily disable API key
    original_key = EmbeddingsService.OPENAI_API_KEY
    EmbeddingsService.OPENAI_API_KEY = None

    try:
        approval = {
            "draft_id": "draft-001",
            "draft_type": "tax_correction",
            "decision": "approved",
            "reason": "Test approval",
            "approved_by": "test@example.com",
            "payload": {},
        }

        result = await EmbeddingsService.vectorize_approval_decision(approval)

        assert result["vectorized"] is False
        assert result["embedding"] is None
        assert result["error"] is None  # Non-blocking, no error raised

    finally:
        EmbeddingsService.OPENAI_API_KEY = original_key


@pytest.mark.asyncio
async def test_vectorize_approval_with_mock_embedding():
    """Vectorization succeeds with mock embedding API."""
    approval = {
        "draft_id": "draft-001",
        "draft_type": "tax_correction",
        "decision": "approved",
        "reason": "Contexia's own invoice, matches DIAN",
        "approved_by": "contador@contexia.com",
        "payload": {
            "lines": [
                {"account": "1105", "debit": 1000000, "credit": 0},
                {"account": "2105", "debit": 0, "credit": 1000000},
            ]
        },
    }

    # Mock the OpenAI API response
    mock_embedding = [0.1] * 1536  # 1536-dim vector

    with patch.object(
        EmbeddingsService, "get_embedding_vector", new_callable=AsyncMock
    ) as mock_get_embedding:
        mock_get_embedding.return_value = mock_embedding

        result = await EmbeddingsService.vectorize_approval_decision(approval)

        assert result["vectorized"] is True
        assert result["embedding"] == mock_embedding
        assert result["embedding_hash"] is not None
        assert result["confidence"] == 1.0
        assert result["error"] is None


@pytest.mark.asyncio
async def test_vectorize_approval_low_confidence():
    """Generic/unknown approval gets lower confidence."""
    approval = {
        "draft_id": "draft-002",
        "draft_type": "unknown",  # Contains 'unknown'
        "decision": "approved",
        "reason": "fix",
        "approved_by": "test@example.com",
        "payload": {},
    }

    mock_embedding = [0.2] * 1536

    with patch.object(
        EmbeddingsService, "get_embedding_vector", new_callable=AsyncMock
    ) as mock_get_embedding:
        mock_get_embedding.return_value = mock_embedding

        result = await EmbeddingsService.vectorize_approval_decision(approval)

        assert result["vectorized"] is True
        assert result["confidence"] == 0.7  # Lower confidence for unknown type


@pytest.mark.asyncio
async def test_persist_embedding_without_embedding():
    """Persist gracefully handles None embedding."""
    # Mock Supabase client
    mock_supabase = None

    success, error = await EmbeddingsService.persist_embedding_to_supabase(
        approval_id="draft-001",
        content="Test content",
        embedding=None,  # No embedding
        metadata={},
        supabase_client=mock_supabase,
    )

    assert success is True
    assert error is None  # Non-blocking
