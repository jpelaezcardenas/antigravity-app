"""
Knowledge Base Service

Wrapper for similarity search against knowledge_chunks table.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class KBService:
    """
    Knowledge base similarity search.
    """

    @staticmethod
    async def search_similar_decisions(
        query_embedding: List[float],
        supabase_client: Any,  # SupabaseClient instance
        limit: int = 5,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Search for similar past decisions using pgvector similarity.

        Args:
            query_embedding: Query vector (1536 dims)
            supabase_client: SupabaseClient instance
            limit: Max number of results
            threshold: Similarity threshold (0-1), default 0.7

        Returns:
            {
                "matches": [
                    {
                        "id": "uuid",
                        "content": "...",
                        "similarity": 0.85,
                        "metadata": {...}
                    },
                    ...
                ],
                "error": None or error message
            }
        """
        try:
            # Call RPC function match_knowledge_chunks
            result = supabase_client.rpc(
                "match_knowledge_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                },
            ).execute()

            matches = []
            if result.data:
                for row in result.data:
                    matches.append(
                        {
                            "id": row.get("id"),
                            "content": row.get("content"),
                            "similarity": row.get("similarity", 0),
                            "metadata": row.get("metadata", {}),
                        }
                    )

            logger.info(f"KB search returned {len(matches)} matches")

            return {
                "matches": matches,
                "error": None,
            }

        except Exception as e:
            logger.error(f"KB search error: {str(e)}")
            return {
                "matches": [],
                "error": str(e),
            }

    @staticmethod
    async def search_endpoint_response(
        query_embedding: List[float],
        supabase_client: Any,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Format search results for API response.

        Returns:
            {
                "matches": [
                    {
                        "id": "uuid",
                        "content": "...",
                        "similarity": 0.85,
                        "approved_by": "...",
                        "timestamp": "2026-06-21T...",
                        "confidence": 1.0
                    },
                    ...
                ]
            }
        """
        result = await KBService.search_similar_decisions(
            query_embedding, supabase_client, limit, threshold
        )

        if result["error"]:
            logger.warning(f"KB search error, returning empty: {result['error']}")
            return {"matches": []}

        matches = []
        for match in result["matches"]:
            metadata = match.get("metadata", {})
            matches.append(
                {
                    "id": match["id"],
                    "content": match["content"],
                    "similarity": match["similarity"],
                    "approved_by": metadata.get("decided_by", "unknown"),
                    "timestamp": metadata.get("timestamp", ""),
                    "confidence": metadata.get("confidence", 0.5),
                }
            )

        return {"matches": matches}
