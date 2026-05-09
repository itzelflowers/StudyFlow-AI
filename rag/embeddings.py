"""
Embedding model setup for StudyFlow AI.

Uses FastEmbed for lightweight, fast embedding generation.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_model = None


def get_embedding_model():
    """Get or create the embedding model singleton."""
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding

            _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("Initialized FastEmbed model: BAAI/bge-small-en-v1.5")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_embedding_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]


def embed_query(query: str) -> list[float]:
    """
    Generate an embedding for a single query.

    Args:
        query: The query text.

    Returns:
        The embedding vector.
    """
    model = get_embedding_model()
    embeddings = list(model.embed([query]))
    return embeddings[0].tolist()
