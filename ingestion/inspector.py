"""
Document Inspection & Sanitization Exporter.
Extracts raw PDF text, evaluates and applies security guardrails (Secret Redaction & PII Masking),
and writes clean, human-readable sanitized text files to storage/processed_docs/
(one .txt file per input PDF).
"""

from pathlib import Path
from typing import List, Dict, Any
import logging
from pydantic import BaseModel, Field

from ingestion.pdf_extractor import PDFExtractor, ExtractedDocument
from guardrails.secret_detector import SecretDetector, SecretMatch
from guardrails.pii_masker import PIIMasker, PIIDetectionResult
from config.settings import settings

logger = logging.getLogger(__name__)


class DocumentInspectionResult(BaseModel):
    filename: str
    source_path: str
    total_pages: int
    raw_characters: int
    sanitized_characters: int
    secrets_count: int
    secrets_types: list[str] = Field(default_factory=list)
    pii_count: int
    pii_types: list[str] = Field(default_factory=list)
    output_txt_path: str


class DocumentInspector:
    """Extracts, sanitizes, and exports PDF documents as readable .txt files before chunking."""

    def __init__(
        self,
        pdf_extractor: PDFExtractor | None = None,
        secret_detector: SecretDetector | None = None,
        pii_masker: PIIMasker | None = None,
    ):
        self.extractor = pdf_extractor or PDFExtractor(preserve_page_breaks=True)
        self.secret_detector = secret_detector or SecretDetector()
        self.pii_masker = pii_masker or PIIMasker()

    def inspect_and_export(
        self,
        folder_or_file: str | Path,
        output_dir: str | Path | None = None,
    ) -> list[DocumentInspectionResult]:
        """
        Processes PDF(s), redacts secrets, masks PII, and exports one sanitized .txt per PDF.
        """
        target = Path(folder_or_file).resolve()
        out_path = Path(output_dir or (settings.storage_dir / "processed_docs")).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        if target.is_file() and target.suffix.lower() == ".pdf":
            docs = [self.extractor.extract_from_file(target)]
        elif target.is_dir():
            docs = self.extractor.extract_from_folder(target)
        else:
            raise ValueError(f"Target '{target}' is neither a PDF file nor a valid directory.")

        results: list[DocumentInspectionResult] = []

        for doc in docs:
            txt_filename = f"{Path(doc.filename).stem}.txt"
            dest_file = out_path / txt_filename

            all_secret_matches: list[SecretMatch] = []
            all_pii_matches: list[PIIDetectionResult] = []
            sanitized_pages_text: list[str] = []

            for page in doc.pages:
                raw_page_text = page.text

                # 1. Secret Detection & Redaction
                sec_text, sec_matches = self.secret_detector.redact(raw_page_text)
                all_secret_matches.extend(sec_matches)

                # 2. PII Detection & Masking
                pii_text, pii_matches = self.pii_masker.anonymize(sec_text)
                all_pii_matches.extend(pii_matches)

                sanitized_pages_text.append(
                    f"--- PAGE {page.page_number} ---\n{pii_text.strip()}\n"
                )

            # Build full sanitized document content with informative audit header
            header_lines = [
                "=" * 80,
                f"DOCUMENT: {doc.filename}",
                f"TOTAL PAGES: {doc.total_pages}",
                f"SOURCE PATH: {doc.file_path}",
                f"SECRETS REDACTED: {len(all_secret_matches)} "
                + (f"({', '.join(set(m.pattern_name for m in all_secret_matches))})" if all_secret_matches else "(None)"),
                f"PII ENTITIES MASKED: {len(all_pii_matches)} "
                + (f"({', '.join(set(m.entity_type for m in all_pii_matches))})" if all_pii_matches else "(None)"),
                "=" * 80,
                "",
            ]

            full_sanitized_content = "\n".join(header_lines) + "\n".join(sanitized_pages_text)

            # Write out to storage/processed_docs/<filename>.txt
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(full_sanitized_content)

            raw_chars = sum(p.char_count for p in doc.pages)
            san_chars = len(full_sanitized_content)

            results.append(
                DocumentInspectionResult(
                    filename=doc.filename,
                    source_path=doc.file_path,
                    total_pages=doc.total_pages,
                    raw_characters=raw_chars,
                    sanitized_characters=san_chars,
                    secrets_count=len(all_secret_matches),
                    secrets_types=list(set(m.pattern_name for m in all_secret_matches)),
                    pii_count=len(all_pii_matches),
                    pii_types=list(set(m.entity_type for m in all_pii_matches)),
                    output_txt_path=str(dest_file),
                )
            )
            logger.info(f"Exported sanitized document to: {dest_file}")

        return results

