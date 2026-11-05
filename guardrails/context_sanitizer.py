"""
Retrieved Context Sanitizer & Framing Guardrail.
Treats retrieved document chunks strictly as untrusted data, never as system instructions.
Neutralizes escape sequences, instructional prefixes, and injects delimiter boundaries.
"""

import re
from typing import Any
from pydantic import BaseModel

from guardrails.secret_detector import SecretDetector
from rag.pipeline import RetrievedContextSnippet


class SanitizedSnippet(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int | None = None
    sanitized_text: str
    redacted_secrets_count: int
    was_modified: bool


class ContextSanitizer:
    """Sanitizes and safely frames retrieved context chunks before LLM generation."""

    # Instructional prefix patterns that attackers use inside documents to hijack context
    INSTRUCTIONAL_PREFIX_PATTERNS = [
        r"(?i)^(?:\s*#+\s*)?(?:system|developer|admin|instruction|directive|user|human|assistant)\s*:\s*",
        r"(?i)^(?:\s*\[(?:system|instruction|admin)\]\s*)",
        r"(?i)^(?:\s*<<SYS>>\s*)",
    ]

    def __init__(self, secret_detector: SecretDetector | None = None):
        self.secret_detector = secret_detector or SecretDetector()

    def sanitize_text(self, text: str) -> tuple[str, int, bool]:
        """Strip instructional prefixes and redact any leftover secrets."""
        modified = False
        secrets_redacted = 0

        # 1. Redact secrets
        clean_text, matches = self.secret_detector.redact(text)
        if matches:
            modified = True
            secrets_redacted = len(matches)

        # 2. Neutralize attempt to break out of delimiters
        clean_text = clean_text.replace("</retrieved_untrusted_data>", "[ESCAPED_CLOSING_TAG]")
        clean_text = clean_text.replace("<retrieved_untrusted_data>", "[ESCAPED_OPENING_TAG]")

        # 3. Strip instruction headers from lines
        lines = clean_text.splitlines()
        sanitized_lines = []
        for line in lines:
            curr_line = line
            for pat in self.INSTRUCTIONAL_PREFIX_PATTERNS:
                subbed = re.sub(pat, "[DATA_TEXT]: ", curr_line)
                if subbed != curr_line:
                    modified = True
                    curr_line = subbed
            sanitized_lines.append(curr_line)

        sanitized_text = "\n".join(sanitized_lines)
        return sanitized_text, secrets_redacted, modified

    def sanitize_snippets(
        self, snippets: list[RetrievedContextSnippet]
    ) -> list[SanitizedSnippet]:
        """Sanitize a list of retrieved snippets."""
        sanitized_list = []
        for s in snippets:
            clean_text, sec_count, mod = self.sanitize_text(s.text)
            sanitized_list.append(
                SanitizedSnippet(
                    chunk_id=s.chunk_id,
                    document_name=s.document_name,
                    page_number=s.page_number,
                    sanitized_text=clean_text,
                    redacted_secrets_count=sec_count,
                    was_modified=mod,
                )
            )
        return sanitized_list

    def frame_for_generation(self, sanitized_snippets: list[SanitizedSnippet]) -> str:
        """
        Wrap sanitized snippets in rigid untrusted delimiters.
        Instructs the model that contents inside the boundary are pure data, not instructions.
        """
        if not sanitized_snippets:
            return "<retrieved_untrusted_data>\nNo relevant documents found.\n</retrieved_untrusted_data>"

        framed_parts = ["<retrieved_untrusted_data>"]
        for idx, s in enumerate(sanitized_snippets, 1):
            header = f"[DOCUMENT_{idx}: {s.document_name}"
            if s.page_number:
                header += f", Page {s.page_number}"
            header += "]"
            framed_parts.append(f"{header}\n{s.sanitized_text}\n")

        framed_parts.append("</retrieved_untrusted_data>")
        return "\n\n".join(framed_parts)

