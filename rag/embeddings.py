"""
Embedding Engine Module.
Delegates to EmbeddingService powered by Gemini Embedding 2 (gemini-embedding-2).
Preserves backward compatibility while enforcing Gemini Embedding 2.
"""

from typing import Any
import logging
from models.embedding_service import EmbeddingService
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Wrapper around EmbeddingService for generating Gemini Embedding 2 vectors."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        dimension: int | None = None,
    ):
        self.service = embedding_service or EmbeddingService()
        self.dimension = dimension or self.service.dimension
        self.model_name = self.service.model_name

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized embedding for a single string using Gemini Embedding 2."""
        return self.service.embed_text(text)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate normalized embeddings for a batch of strings."""
        return self.service.embed_batch(texts)
