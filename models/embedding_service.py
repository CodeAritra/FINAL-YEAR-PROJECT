"""
Embedding Service Module.
Coordinates document and query vector generation using Gemini Embedding 2 (gemini-embedding-2).
Guarantees consistent dimensionality (768) and handles caching across pipeline stages.
"""

from typing import Any
import logging
from providers.gemini_provider import GeminiEmbeddingProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """High-level embedding service powered by Gemini Embedding 2."""

    def __init__(
        self,
        provider: GeminiEmbeddingProvider | None = None,
        enable_cache: bool = True,
    ):
        self.provider = provider or GeminiEmbeddingProvider()
        self.dimension = self.provider.dimension
        self.model_name = self.provider.model_name
        self.enable_cache = enable_cache
        self._cache: dict[str, list[float]] = {}

    def embed_text(self, text: str) -> list[float]:
        """Embed a single query or chunk string."""
        if not text:
            return [0.0] * self.dimension

        if self.enable_cache and text in self._cache:
            return self._cache[text]

        vec = self.provider.embed_text(text)
        if self.enable_cache:
            self._cache[text] = vec
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text chunks."""
        if not texts:
            return []

        results: list[list[float]] = []
        to_fetch_indices = []
        to_fetch_texts = []

        for idx, t in enumerate(texts):
            if self.enable_cache and t in self._cache:
                results.append(self._cache[t])
            else:
                results.append([])
                to_fetch_indices.append(idx)
                to_fetch_texts.append(t)

        if to_fetch_texts:
            fetched_vecs = self.provider.embed_batch(to_fetch_texts)
            for idx, vec in zip(to_fetch_indices, fetched_vecs):
                results[idx] = vec
                if self.enable_cache:
                    self._cache[texts[idx]] = vec

        return results

