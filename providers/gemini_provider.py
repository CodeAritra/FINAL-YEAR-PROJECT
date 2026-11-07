"""
Google Gemini Provider for Embedding Generation.
Uses the official Google Gen AI Python SDK (google-genai) to generate dense vector embeddings
via Gemini Embedding 2 (gemini-embedding-2).
Handles rate limits, configurable output dimensions, and offline fallback.
"""

from typing import Any
import logging
import hashlib
import time
import numpy as np
from google import genai
from google.genai import types

from config.settings import settings

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider:
    """Provider for generating embeddings using Gemini Embedding 2 via google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        dimension: int | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_embedding_model
        self.dimension = dimension or settings.gemini_embedding_dimension
        self.max_retries = max_retries
        self.base_delay = base_delay

        self._client: genai.Client | None = None
        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info(
                    f"Initialized Google GenAI client for embedding model '{self.model_name}' (dim: {self.dimension})."
                )
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")
        else:
            logger.info("GEMINI_API_KEY not configured. Running in offline/mock embedding mode.")

    def _generate_deterministic_vector(self, text: str) -> list[float]:
        """Generate deterministic pseudo-random normalized vector of target dimension for offline/test mode."""
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single string using Gemini Embedding 2."""
        if not text:
            return [0.0] * self.dimension

        if not self._client:
            return self._generate_deterministic_vector(text)

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                config = types.EmbedContentConfig(output_dimensionality=self.dimension)
                response = self._client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config=config,
                )

                if response.embedding and response.embedding.values:
                    vec = list(response.embedding.values)
                    # Normalize vector
                    arr = np.array(vec)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                    return arr.tolist()

            except Exception as e:
                last_err = e
                logger.warning(
                    f"Gemini embedding API call failed (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.base_delay * (2 ** (attempt - 1)))

        logger.error(
            f"All {self.max_retries} retries for Gemini embedding failed ({last_err}). Falling back to deterministic vector."
        )
        return self._generate_deterministic_vector(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of strings with rate limit pacing."""
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for idx, text in enumerate(texts):
            embeddings.append(self.embed_text(text))
            # Minimal pacing between calls if using live API
            if self._client and idx % 10 == 0 and idx > 0:
                time.sleep(0.1)

        return embeddings

