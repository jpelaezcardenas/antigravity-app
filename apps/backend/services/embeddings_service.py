"""
Embeddings Service

Converts approval decisions to vector embeddings and persists to Supabase pgvector.
"""

import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Manages vectorization of approval decisions.
    """

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
    EMBEDDING_MODEL = "text-embedding-3-small"  # Cheaper than ada-002
    EMBEDDING_DIMENSION = 1536

    @staticmethod
    def extract_semantic_summary(approval: Dict[str, Any]) -> str:
        """
        Extract semantic summary from an approval decision.

        Args:
            approval: {
                "draft_id": "uuid",
                "draft_type": "tax_correction",
                "decision": "approved",
                "reason": "Contexia's own invoice, matches DIAN",
                "approved_by": "contador@contexia.com",
                "payload": {...},  # journal entry
            }

        Returns:
            Semantic summary string (500 chars max)
        """
        try:
            draft_type = approval.get("draft_type", "unknown")
            decision = approval.get("decision", "unknown")
            reason = approval.get("reason", "")
            payload = approval.get("payload", {})

            # Extract first few lines from payload for context
            lines_preview = ""
            if isinstance(payload, dict) and "lines" in payload:
                lines = payload["lines"][:2]  # First 2 lines
                for line in lines:
                    account = line.get("account", "?")
                    debit = line.get("debit", 0)
                    credit = line.get("credit", 0)
                    lines_preview += f"{account}({debit}/{credit}) "

            summary = f"""
Draft Type: {draft_type}
Decision: {decision}
Reason: {reason}
Lines: {lines_preview.strip()}
""".strip()

            return summary[:500]  # Limit to 500 chars

        except Exception as e:
            logger.error(f"Error extracting semantic summary: {str(e)}")
            return f"Draft {approval.get('draft_type', '?')}: {approval.get('decision', '?')}"

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    async def get_embedding_vector(text: str) -> Optional[list]:
        """
        Call embedding API (OpenAI, Cerebras, or fallback).

        Args:
            text: Text to embed

        Returns:
            List of 1536 floats (embedding vector), or None if failed
        """
        if not EmbeddingsService.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not set, skipping vectorization (non-blocking)"
            )
            return None

        try:
            # Use openai-python library
            from openai import OpenAI

            client = OpenAI(api_key=EmbeddingsService.OPENAI_API_KEY)

            response = client.embeddings.create(
                input=text,
                model=EmbeddingsService.EMBEDDING_MODEL,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except ImportError:
            logger.error("openai library not installed, skipping vectorization")
            return None
        except Exception as e:
            logger.error(f"Embedding API error: {str(e)}")
            return None

    @staticmethod
    async def vectorize_approval_decision(
        approval: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Vectorize an approval decision and prepare for persistence.

        Args:
            approval: {
                "draft_id": "uuid",
                "draft_type": "tax_correction",
                "decision": "approved",
                "reason": "...",
                "approved_by": "...",
                "payload": {...},
            }

        Returns:
            {
                "vectorized": bool,
                "embedding_hash": str,
                "embedding": list or None,
                "content": str,
                "error": str or None,
            }
        """
        try:
            # Step 1: Extract semantic summary
            semantic_summary = EmbeddingsService.extract_semantic_summary(approval)

            # Step 2: Compute content hash for deduplication
            content_hash = EmbeddingsService.compute_content_hash(semantic_summary)

            # Step 3: Get embedding vector
            embedding = await EmbeddingsService.get_embedding_vector(semantic_summary)

            # Step 4: Determine confidence
            # If text is very short or generic, reduce confidence
            if len(semantic_summary) < 50 or "unknown" in semantic_summary.lower():
                confidence = 0.7
            else:
                confidence = 1.0

            result = {
                "vectorized": embedding is not None,
                "embedding_hash": content_hash,
                "embedding": embedding,
                "content": semantic_summary,
                "confidence": confidence,
                "error": None,
            }

            logger.info(
                f"Vectorized approval {approval.get('draft_id', '?')} "
                f"(hash={content_hash[:8]}..., confidence={confidence})"
            )

            return result

        except Exception as e:
            logger.error(f"Vectorization error: {str(e)}")
            return {
                "vectorized": False,
                "embedding_hash": None,
                "embedding": None,
                "content": None,
                "confidence": 0,
                "error": str(e),
            }

    @staticmethod
    async def persist_embedding_to_supabase(
        approval_id: str,
        content: str,
        embedding: list,
        metadata: Dict[str, Any],
        supabase_client: Any,  # SupabaseClient instance
    ) -> Tuple[bool, Optional[str]]:
        """
        Persist embedding to Supabase knowledge_chunks table.

        Args:
            approval_id: UUID of the approval decision
            content: Semantic summary text
            embedding: Vector (1536 dims)
            metadata: { approval_id, decided_by, timestamp, confidence }
            supabase_client: SupabaseClient instance

        Returns:
            (success: bool, error: Optional[str])
        """
        try:
            if embedding is None:
                logger.warning(f"Skipping persist for {approval_id} (no embedding)")
                return True, None

            # Insert into knowledge_chunks
            result = supabase_client.table("knowledge_chunks").insert(
                {
                    "content": content,
                    "embedding": embedding,
                    "content_hash": EmbeddingsService.compute_content_hash(content),
                    "metadata": metadata,
                }
            ).execute()

            logger.info(f"Persisted embedding for approval {approval_id}")
            return True, None

        except Exception as e:
            logger.error(f"Supabase persist error: {str(e)}")
            return False, str(e)
