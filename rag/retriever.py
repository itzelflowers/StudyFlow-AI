"""
Semantic search retriever — searches educational resources from Qdrant.
"""

from __future__ import annotations

import logging

from rag.embeddings import embed_query
from rag.indexer import get_qdrant_client, COLLECTION_NAME, create_collection

logger = logging.getLogger(__name__)


def search_resources(
    query: str,
    limit: int = 5,
    difficulty: str | None = None,
    resource_type: str | None = None,
) -> list[dict]:
    """
    Search for educational resources using semantic similarity.

    Args:
        query: Search query (e.g., "learn derivatives calculus")
        limit: Maximum number of results
        difficulty: Optional filter by difficulty level
        resource_type: Optional filter by resource type

    Returns:
        List of matching resources with scores.
    """
    try:
        create_collection()
        client = get_qdrant_client()

        # Generate query embedding
        query_vector = embed_query(query)

        # Build filter conditions
        must_conditions = []
        if difficulty:
            must_conditions.append({
                "key": "difficulty",
                "match": {"value": difficulty},
            })
        if resource_type:
            must_conditions.append({
                "key": "resource_type",
                "match": {"value": resource_type},
            })

        query_filter = None
        if must_conditions:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = []
            if difficulty:
                conditions.append(
                    FieldCondition(key="difficulty", match=MatchValue(value=difficulty))
                )
            if resource_type:
                conditions.append(
                    FieldCondition(key="resource_type", match=MatchValue(value=resource_type))
                )
            query_filter = Filter(must=conditions)

        # Search
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )

        # Format results
        resources = []
        for point in results.points:
            resource = {
                **point.payload,
                "relevance_score": point.score,
            }
            resources.append(resource)

        logger.info(f"Found {len(resources)} resources for query: {query[:50]}...")
        return resources

    except Exception as e:
        logger.warning(f"Resource search failed: {e}")
        return []
