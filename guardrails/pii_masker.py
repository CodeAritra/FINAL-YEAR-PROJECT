"""
Personally Identifiable Information (PII) Masker Guardrail.
Uses Microsoft Presidio Analyzer & Anonymizer with fallback regex patterns
to detect and redact names, emails, phone numbers, SSNs, and credit cards.
"""

from typing import Any
import re
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PIIDetectionResult(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    text: str


class PIIMasker:
    """Detects and redacts PII using Presidio Analyzer or regex fallback."""

    FALLBACK_PATTERNS = {
        "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
        "PHONE_NUMBER": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "US_SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "IP_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    }

    def __init__(self, language: str = "en", use_presidio: bool = True):
        self.language = language
        self.use_presidio = use_presidio
        self.analyzer: Any = None
        self.anonymizer: Any = None

        if self.use_presidio:
            self._init_presidio()

    def _init_presidio(self) -> None:
        """Initialize Presidio Analyzer and Anonymizer engines."""
        try:
            import spacy
            if not spacy.util.is_package("en_core_web_sm") and not spacy.util.is_package("en_core_web_lg"):
                logger.info("spaCy language model not pre-installed. Using robust regex PII fallback.")
                self.use_presidio = False
                return

            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio Analyzer & Anonymizer initialized successfully.")
        except (Exception, SystemExit) as e:
            logger.warning(
                f"Presidio engine initialization skipped ({e}). Using regex fallback for PII."
            )
            self.use_presidio = False

    def scan(self, text: str) -> list[PIIDetectionResult]:
        """Scan text and return detected PII entities."""
        if not text:
            return []

        results: list[PIIDetectionResult] = []

        if self.use_presidio and self.analyzer:
            try:
                presidio_res = self.analyzer.analyze(
                    text=text,
                    language=self.language,
                    entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "US_SSN", "CREDIT_CARD", "IP_ADDRESS"],
                )
                for item in presidio_res:
                    results.append(
                        PIIDetectionResult(
                            entity_type=item.entity_type,
                            start=item.start,
                            end=item.end,
                            score=item.score,
                            text=text[item.start : item.end],
                        )
                    )
                return results
            except Exception as e:
                logger.warning(f"Presidio scan failed ({e}), falling back to regex.")

        # Regex fallback
        for entity_type, pat in self.FALLBACK_PATTERNS.items():
            for m in re.finditer(pat, text):
                results.append(
                    PIIDetectionResult(
                        entity_type=entity_type,
                        start=m.start(),
                        end=m.end(),
                        score=0.90,
                        text=m.group(0),
                    )
                )

        return results

    def anonymize(self, text: str) -> tuple[str, list[PIIDetectionResult]]:
        """
        Anonymize PII in the text.
        Returns the sanitized text and list of detected PII items.
        """
        if not text:
            return "", []

        detections = self.scan(text)
        if not detections:
            return text, []

        if self.use_presidio and self.anonymizer and self.analyzer:
            try:
                from presidio_analyzer import RecognizerResult

                presidio_entities = [
                    RecognizerResult(
                        entity_type=d.entity_type,
                        start=d.start,
                        end=d.end,
                        score=d.score,
                    )
                    for d in detections
                ]
                anon_res = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=presidio_entities,
                )
                return anon_res.text, detections
            except Exception as e:
                logger.warning(f"Presidio anonymization failed ({e}), falling back to regex replacement.")

        # Manual replacement fallback
        sorted_detections = sorted(detections, key=lambda x: x.start, reverse=True)
        anonymized_text = text
        for d in sorted_detections:
            replacement = f"<{d.entity_type}>"
            anonymized_text = anonymized_text[: d.start] + replacement + anonymized_text[d.end :]

        return anonymized_text, detections

