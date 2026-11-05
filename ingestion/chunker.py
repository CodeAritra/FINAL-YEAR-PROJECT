"""
Text Chunking Module using LangChain RecursiveCharacterTextSplitter.
Splits extracted document texts into chunks while maintaining semantic integrity.
"""

from typing import Any
import uuid
import logging
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingestion.pdf_extractor import ExtractedDocument

logger = logging.getLogger(__name__)


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_name: str
    source_path: str
    page_number: int | None = None
    chunk_index: int
    text: str
    char_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class TextChunker:
    """Splits extracted documents into overlapping text chunks."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

    def chunk_document(self, document: ExtractedDocument) -> list[DocumentChunk]:
        """
        Chunk document by page to retain accurate page-level citations and metadata.
        Falls back to full text if page text is not discrete.
        """
        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        # Prefer per-page chunking to preserve page provenance
        if document.pages:
            for page in document.pages:
                if not page.text.strip():
                    continue
                sub_chunks = self.splitter.split_text(page.text)
                for sc in sub_chunks:
                    clean = sc.strip()
                    if clean:
                        chunks.append(
                            DocumentChunk(
                                document_name=document.filename,
                                source_path=document.file_path,
                                page_number=page.page_number,
                                chunk_index=chunk_idx,
                                text=clean,
                                char_count=len(clean),
                                metadata=dict(document.metadata),
                            )
                        )
                        chunk_idx += 1
        else:
            sub_chunks = self.splitter.split_text(document.full_text)
            for sc in sub_chunks:
                clean = sc.strip()
                if clean:
                    chunks.append(
                        DocumentChunk(
                            document_name=document.filename,
                            source_path=document.file_path,
                            page_number=None,
                            chunk_index=chunk_idx,
                            text=clean,
                            char_count=len(clean),
                            metadata=dict(document.metadata),
                        )
                    )
                    chunk_idx += 1

        logger.info(f"Generated {len(chunks)} chunks for {document.filename}.")
        return chunks

    def chunk_documents(self, documents: list[ExtractedDocument]) -> list[DocumentChunk]:
        """Chunk a collection of documents."""
        all_chunks: list[DocumentChunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

