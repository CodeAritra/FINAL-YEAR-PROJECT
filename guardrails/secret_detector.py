"""
Secret Detection and Redaction Guardrail.
Scans text for API keys, passwords, private keys, database credentials, and high-entropy secrets.
Provides both pattern matching and Shannon entropy validation.
"""

import re
import math
from typing import NamedTuple
from pydantic import BaseModel


class SecretMatch(BaseModel):
    pattern_name: str
    matched_text: str
    start_pos: int
    end_pos: int
    confidence: float
    masked_replacement: str


class SecretDetector:
    """Detects and redacts credentials, API keys, tokens, and sensitive strings."""

    DEFAULT_PATTERNS = {
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{32,64}",
        "Generic Bearer/API Key": r"(?i)(?:api_key|apikey|secret_key|access_token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{20,80})['\"]?",
        "AWS Access Key": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "AWS Secret Key": r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([a-zA-Z0-9/+=]{40})['\"]?",
        "GitHub Personal Access Token": r"gh[pous]_[a-zA-Z0-9]{36,255}",
        "Slack Token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}",
        "RSA/OpenSSH Private Key": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "Generic Password in Text": r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s,;'\"]{6,40})['\"]?",
        "JSON Web Token": r"ey[A-Za-z0-9_-]{10,}\.ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "Database Connection URI": r"(?i)(?:postgres|mysql|mongodb|redis):\/\/[a-zA-Z0-9_-]+:[^@\s]+@[a-zA-Z0-9\.-]+(?::[0-9]+)?\/[a-zA-Z0-9_-]+",
    }

    def __init__(
        self,
        custom_patterns: dict[str, str] | None = None,
        entropy_threshold: float = 3.5,
    ):
        self.patterns = dict(self.DEFAULT_PATTERNS)
        if custom_patterns:
            self.patterns.update(custom_patterns)
        self.entropy_threshold = entropy_threshold

        # Compile regular expressions
        self._compiled_patterns = {
            name: re.compile(pat) for name, pat in self.patterns.items()
        }

    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """Calculate the Shannon entropy of a string (bits per symbol)."""
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        frequencies: dict[str, int] = {}
        for char in data:
            frequencies[char] = frequencies.get(char, 0) + 1

        for count in frequencies.values():
            p_x = count / length
            entropy += - p_x * math.log2(p_x)

        return entropy

    def scan(self, text: str) -> list[SecretMatch]:
        """Scan text and identify all detected secrets."""
        matches: list[SecretMatch] = []

        for name, regex in self._compiled_patterns.items():
            for m in regex.finditer(text):
                # If there's a capture group, focus on the credential value
                if m.groups():
                    matched_value = m.group(1)
                    start = m.start(1)
                    end = m.end(1)
                else:
                    matched_value = m.group(0)
                    start = m.start()
                    end = m.end()

                # Basic validation: filter out common false positives
                if len(matched_value.strip()) < 6:
                    continue

                entropy = self.calculate_shannon_entropy(matched_value)
                confidence = 0.95 if entropy >= self.entropy_threshold else 0.80

                masked_repr = f"[REDACTED_{name.upper().replace(' ', '_')}]"
                matches.append(
                    SecretMatch(
                        pattern_name=name,
                        matched_text=matched_value,
                        start_pos=start,
                        end_pos=end,
                        confidence=confidence,
                        masked_replacement=masked_repr,
                    )
                )

        # Sort matches by start position descending for safe replacement
        matches.sort(key=lambda x: x.start_pos, reverse=True)
        return matches

    def redact(self, text: str) -> tuple[str, list[SecretMatch]]:
        """
        Redact all detected secrets from text.
        Returns the sanitized text and the list of detected matches.
        """
        matches = self.scan(text)
        if not matches:
            return text, []

        sanitized = text
        for m in matches:
            # Replace target slice
            sanitized = (
                sanitized[: m.start_pos]
                + m.masked_replacement
                + sanitized[m.end_pos :]
            )

        return sanitized, matches

