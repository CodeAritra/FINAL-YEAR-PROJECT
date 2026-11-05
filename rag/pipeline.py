"""
Core RAG Retrieval Pipeline.
Coordinates embedding generation and Qdrant similarity search.
Provides common retrieval infrastructure reused across all three modes.
"""

from typing import Any
import logging
from pydantic import BaseModel, Field

from rag.embeddings import EmbeddingEngine
from database.qdrant_manager import QdrantManager
from config import settings

logger = logging.getLogger(__name__)


class RetrievedContextSnippet(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int | None = None
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGRetrievalPipeline:
    """Handles semantic retrieval of document chunks from Qdrant vector database."""

    def __init__(
        self,
        qdrant_manager: QdrantManager | None = None,
        embedding_engine: EmbeddingEngine | None = None,
    ):
        self.qdrant = qdrant_manager or QdrantManager()
        self.embedder = embedding_engine or EmbeddingEngine()

    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 4,
        score_threshold: float = 0.0,
    ) -> list[RetrievedContextSnippet]:
        """Embed user query and retrieve top-k matching snippets from the given collection."""
        if not query.strip():
            return []

        logger.info(f"Retrieving top-{top_k} chunks from '{collection_name}' for query.")
        query_vector = self.embedder.embed_text(query)

        hits = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold if score_threshold > 0.0 else None,
        )

        snippets: list[RetrievedContextSnippet] = []
        for hit in hits:
            payload = hit.get("payload", {})
            snippets.append(
                RetrievedContextSnippet(
                    chunk_id=str(hit.get("id")),
                    document_name=payload.get("document_name", "unknown_source"),
                    page_number=payload.get("page_number"),
                    text=payload.get("text", ""),
                    score=hit.get("score", 0.0),
                    metadata=payload.get("metadata", {}),
                )
            )

        return snippets

    @staticmethod
    def format_snippets_for_prompt(
        snippets: list[RetrievedContextSnippet],
        include_metadata: bool = True,
    ) -> str:
        """Format retrieved snippets into a clean text block for LLM prompts."""
        if not snippets:
            return "No relevant context found in documents."

        formatted_parts = []
        for idx, s in enumerate(snippets, 1):
            header = f"[Source {idx}: {s.document_name}"
            if s.page_number is not None:
                header += f", Page {s.page_number}"
            header += f" (Relevance: {s.score:.3f})]"

            formatted_parts.append(f"{header}\n{s.text}")

        return "\n\n".join(formatted_parts)

