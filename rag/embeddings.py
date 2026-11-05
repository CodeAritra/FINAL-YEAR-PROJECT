"""
Embedding Engine Module.
Generates vector representations using sentence-transformers (all-MiniLM-L6-v2) on CPU.
Includes mock fallback for zero-dependency test execution.
"""

from typing import Any
import logging
import hashlib
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generates dense vector embeddings for documents and queries."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        use_mock: bool = False,
    ):
        self.model_name = model_name or settings.embedding_model_name
        self.device = device or settings.device
        self.dimension = settings.embedding_dimension
        self.use_mock = use_mock
        self._model: Any = None

        if not self.use_mock:
            self._load_model()

    def _load_model(self) -> None:
        """Lazy load SentenceTransformer model onto CPU."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(
                f"Loading embedding model '{self.model_name}' on device '{self.device}'."
            )
            self._model = SentenceTransformer(self.model_name, device=self.device)
            # Verify dimension
            sample_dim = self._model.get_sentence_embedding_dimension()
            if sample_dim:
                self.dimension = sample_dim
        except Exception as e:
            logger.warning(
                f"Failed to load SentenceTransformer ({e}). Falling back to deterministic pseudo-embeddings."
            )
            self.use_mock = True

    def _generate_mock_vector(self, text: str) -> list[float]:
        """Generate deterministic pseudo-random normalized vector for testing/offline."""
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized embedding for a single string."""
        if not text:
            return [0.0] * self.dimension

        if self.use_mock or self._model is None:
            return self._generate_mock_vector(text)

        try:
            vec = self._model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return vec.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}. Falling back to pseudo-vector.")
            return self._generate_mock_vector(text)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate normalized embeddings for a batch of strings."""
        if not texts:
            return []

        if self.use_mock or self._model is None:
            return [self._generate_mock_vector(t) for t in texts]

        try:
            vectors = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 50,
                convert_to_numpy=True,
            )
            return vectors.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}. Falling back to pseudo-vectors.")
            return [self._generate_mock_vector(t) for t in texts]

