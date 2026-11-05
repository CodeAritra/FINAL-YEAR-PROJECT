"""
PDF Extraction Module using PyMuPDF (fitz).
Extracts text, metadata, and page structures safely without executing embedded scripts.
"""

from pathlib import Path
from typing import Any
import logging
import pymupdf  # Modern PyMuPDF API
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    char_count: int


class ExtractedDocument(BaseModel):
    file_path: str
    filename: str
    total_pages: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[ExtractedPage] = Field(default_factory=list)
    full_text: str = ""


class PDFExtractor:
    """Safely extracts text and layout metadata from PDF documents."""

    def __init__(self, preserve_page_breaks: bool = True):
        self.preserve_page_breaks = preserve_page_breaks

    def extract_from_file(self, file_path: str | Path) -> ExtractedDocument:
        """Extract text and metadata from a single PDF file."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF document not found at: {path}")

        logger.info(f"Extracting content from PDF: {path.name}")
        pages: list[ExtractedPage] = []
        full_text_parts: list[str] = []

        try:
            doc = pymupdf.open(str(path))
            metadata = doc.metadata or {}

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = page.get_text("text") or ""
                cleaned_text = page_text.strip()

                pages.append(
                    ExtractedPage(
                        page_number=page_idx + 1,
                        text=cleaned_text,
                        char_count=len(cleaned_text),
                    )
                )
                if cleaned_text:
                    full_text_parts.append(cleaned_text)

            doc.close()

            separator = "\n\n--- PAGE BREAK ---\n\n" if self.preserve_page_breaks else "\n\n"
            full_text = separator.join(full_text_parts)

            return ExtractedDocument(
                file_path=str(path),
                filename=path.name,
                total_pages=len(pages),
                metadata=metadata,
                pages=pages,
                full_text=full_text,
            )

        except Exception as e:
            logger.error(f"Failed to parse PDF {path.name}: {e}")
            raise RuntimeError(f"Error parsing PDF file {path.name}: {e}") from e

    def extract_from_folder(
        self, folder_path: str | Path, recursive: bool = True
    ) -> list[ExtractedDocument]:
        """Extract all PDF documents found in a directory."""
        folder = Path(folder_path).resolve()
        if not folder.exists() or not folder.is_dir():
            raise NotADirectoryError(f"Directory not found: {folder}")

        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = sorted(folder.glob(pattern))

        logger.info(f"Discovered {len(pdf_files)} PDF files in {folder}.")
        extracted_docs = []
        for pdf in pdf_files:
            try:
                extracted_docs.append(self.extract_from_file(pdf))
            except Exception as e:
                logger.warning(f"Skipping corrupt or unreadable PDF {pdf.name}: {e}")

        return extracted_docs
