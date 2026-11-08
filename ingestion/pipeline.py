"""
Document Ingestion Orchestration Pipeline.
Extracts, chunks, evaluates security policies, embeds, and indexes PDFs into Qdrant Cloud.
Strictly separates baseline and secured ingestion collections.
"""

from pathlib import Path
from typing import Any
import logging
import uuid
from pydantic import BaseModel, Field

from ingestion.pdf_extractor import PDFExtractor, ExtractedDocument
from ingestion.chunker import TextChunker, DocumentChunk
from ingestion.inspector import DocumentInspector
from rag.embeddings import EmbeddingEngine
from database.qdrant_manager import QdrantManager
from policies.engine import PolicyEngine, PolicyDecision
from config import settings

logger = logging.getLogger(__name__)


class IngestionStats(BaseModel):
    files_processed: int = 0
    total_chunks: int = 0
    baseline_indexed: int = 0
    secured_indexed: int = 0
    secrets_redacted: int = 0
    pii_masked: int = 0
    injections_quarantined: int = 0


class IngestionPipeline:
    """Coordinates PDF parsing, chunking, security scanning, embedding, and storage."""

    def __init__(
        self,
        pdf_extractor: PDFExtractor | None = None,
        chunker: TextChunker | None = None,
        embedder: EmbeddingEngine | None = None,
        qdrant_manager: QdrantManager | None = None,
        policy_engine: PolicyEngine | None = None,
    ):
        self.extractor = pdf_extractor or PDFExtractor()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or EmbeddingEngine()
        self.qdrant = qdrant_manager or QdrantManager()
        self.policy_engine = policy_engine or PolicyEngine()

        # Ensure collections exist
        self.baseline_collection = settings.qdrant_collection_baseline
        self.secured_collection = settings.qdrant_collection_secured
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """Create both baseline and secured collections in Qdrant if needed."""
        self.qdrant.ensure_collection(self.baseline_collection, vector_size=self.embedder.dimension)
        self.qdrant.ensure_collection(self.secured_collection, vector_size=self.embedder.dimension)

    def ingest_folder(
        self, folder_path: str | Path, target: str = "both"
    ) -> IngestionStats:
        """
        Ingest all PDF files from a directory into baseline and/or secured collections.
        target options: 'baseline', 'secured', 'both'
        """
        folder = Path(folder_path)
        docs = self.extractor.extract_from_folder(folder)
        stats = IngestionStats(files_processed=len(docs))

        all_chunks: list[DocumentChunk] = []
        for doc in docs:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        stats.total_chunks = len(all_chunks)
        if not all_chunks:
            logger.warning(f"No chunks extracted from {folder}.")
            return stats

        # Automatically export sanitized documents to storage/processed_docs/ for auditing
        try:
            inspector = DocumentInspector(
                pdf_extractor=self.extractor,
                secret_detector=self.policy_engine.secret_detector,
                pii_masker=self.policy_engine.pii_masker,
            )
            inspector.inspect_and_export(folder)
        except Exception as e:
            logger.warning(f"Could not export inspection documents: {e}")

        # 1. Ingest into Baseline Collection (Raw, Unsanitized)
        if target in ("baseline", "both"):
            logger.info(f"Indexing {len(all_chunks)} raw chunks into baseline collection.")
            raw_texts = [c.text for c in all_chunks]
            raw_embeddings = self.embedder.embed_batch(raw_texts)

            baseline_points = [
                {
                    "id": c.chunk_id,
                    "vector": raw_embeddings[i],
                    "payload": {
                        "document_name": c.document_name,
                        "source_path": c.source_path,
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index,
                        "text": c.text,
                        "metadata": c.metadata,
                    },
                }
                for i, c in enumerate(all_chunks)
            ]
            indexed_count = self.qdrant.upsert_points(self.baseline_collection, baseline_points)
            stats.baseline_indexed = indexed_count

        # 2. Ingest into Secured Collection (Policy-Evaluated, Masked, Quarantined)
        if target in ("secured", "both"):
            logger.info(f"Processing and indexing {len(all_chunks)} chunks into secured collection.")
            secured_points = []

            for c in all_chunks:
                # Security scanning & policy decision
                eval_res = self.policy_engine.evaluate_ingestion(c.text, c.document_name)

                stats.secrets_redacted += eval_res.secrets_count
                stats.pii_masked += eval_res.pii_count
                if eval_res.is_injection_quarantined:
                    stats.injections_quarantined += 1

                # Embed the processed/sanitized text, NEVER the raw secrets
                sanitized_vector = self.embedder.embed_text(eval_res.processed_text)

                secured_points.append(
                    {
                        "id": c.chunk_id,
                        "vector": sanitized_vector,
                        "payload": {
                            "document_name": c.document_name,
                            "source_path": c.source_path,
                            "page_number": c.page_number,
                            "chunk_index": c.chunk_index,
                            "text": eval_res.processed_text,
                            "policy_decision": eval_res.decision.value,
                            "policy_reasons": eval_res.reasons,
                            "sensitivity_tier": eval_res.sensitivity_tier.value,
                            "is_quarantined": eval_res.is_injection_quarantined,
                            "metadata": c.metadata,
                        },
                    }
                )

            indexed_count = self.qdrant.upsert_points(self.secured_collection, secured_points)
            stats.secured_indexed = indexed_count

        return stats

