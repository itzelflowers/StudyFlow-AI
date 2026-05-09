"""
Qdrant indexer — indexes educational resources into the vector database.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from rag.embeddings import embed_texts

logger = logging.getLogger(__name__)

COLLECTION_NAME = "educational_resources"
VECTOR_SIZE = 384  # BGE-small-en-v1.5 produces 384-dim vectors

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Get or create the Qdrant client (in-memory for MVP)."""
    global _client
    if _client is None:
        mode = os.getenv("QDRANT_MODE", "memory")
        if mode == "memory":
            _client = QdrantClient(location=":memory:")
            logger.info("Initialized Qdrant client (in-memory mode)")
        else:
            _client = QdrantClient(path="./qdrant_data")
            logger.info("Initialized Qdrant client (local storage)")
    return _client


def create_collection() -> None:
    """Create the educational resources collection if it doesn't exist."""
    client = get_qdrant_client()

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created collection: {COLLECTION_NAME}")
    else:
        logger.info(f"Collection already exists: {COLLECTION_NAME}")


def index_resources(resources: list[dict]) -> int:
    """
    Index educational resources into Qdrant.

    Args:
        resources: List of resource dicts with title, description, url, etc.

    Returns:
        Number of resources indexed.
    """
    if not resources:
        return 0

    create_collection()
    client = get_qdrant_client()

    # Create text representations for embedding
    texts = [
        f"{r.get('title', '')}. {r.get('description', '')}. "
        f"Topics: {', '.join(r.get('topics', []))}. "
        f"Level: {r.get('difficulty', 'beginner')}"
        for r in resources
    ]

    # Generate embeddings
    embeddings = embed_texts(texts)

    # Create points
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "url": r.get("url", ""),
                "resource_type": r.get("resource_type", "article"),
                "difficulty": r.get("difficulty", "beginner"),
                "topics": r.get("topics", []),
                "provider": r.get("provider", ""),
                "estimated_minutes": r.get("estimated_minutes", 30),
            },
        )
        for r, embedding in zip(resources, embeddings)
    ]

    # Upsert points
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"Indexed {len(points)} resources into Qdrant")

    return len(points)


def seed_from_file(filepath: str = "data/sample_resources.json") -> int:
    """
    Seed the vector database from a JSON file.

    Args:
        filepath: Path to the JSON file with resources.

    Returns:
        Number of resources indexed.
    """
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Seed file not found: {filepath}")
        return 0

    with open(path, "r") as f:
        resources = json.load(f)

    return index_resources(resources)
