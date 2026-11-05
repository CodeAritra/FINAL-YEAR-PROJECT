"""
Prompt Injection Detection Guardrail.
Detects direct and indirect prompt injection attempts using ProtectAI DeBERTa v3 Prompt Injection v2
(via hosted inference endpoint) and heuristic pattern matching.
"""

from typing import Any
import re
import logging
import httpx
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class InjectionDetectionResult(BaseModel):
    is_injection: bool
    confidence_score: float
    trigger_type: str  # "model_prediction" | "heuristic_pattern" | "clean"
    explanation: str
    flagged_patterns: list[str] = []


class PromptInjectionDetector:
    """Detects prompt injection and jailbreak payloads in queries or document text."""

    HEURISTIC_PATTERNS = [
        (r"(?i)\bignore (?:all )?(?:previous|prior|above) (?:instructions|rules|prompts|directives)\b", "Instruction Override"),
        (r"(?i)\bdisregard (?:all )?(?:previous|prior|above) (?:instructions|rules|prompts)\b", "Instruction Override"),
        (r"(?i)\byou are now (?:unconstrained|in developer mode|dan|jailbroken)\b", "Jailbreak Framing"),
        (r"(?i)\bdo anything now\b", "DAN Jailbreak"),
        (r"(?i)\b(?:reveal|print|output|display|show) (?:your )?(?:system prompt|initial instructions|hidden instructions)\b", "System Prompt Exfiltration"),
        (r"(?i)\bfrom now on, you must\b", "Behavioral Hijack"),
        (r"(?i)<\/?(?:system|instruction|prompt|context|human|assistant)>", "Delimiter Injection"),
        (r"(?i)\[\/?INST\]|<<SYS>>|<\/s>", "Special Token Injection"),
        (r"(?i)\bpretend (?:to be|you have no limits|you are an unfiltered)\b", "Persona Manipulation"),
    ]

    def __init__(
        self,
        provider: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
        threshold: float = 0.5,
    ):
        self.provider = provider or settings.prompt_injection_provider
        self.api_url = api_url or settings.deberta_api_url
        self.api_key = api_key or settings.hf_api_key
        self.threshold = threshold

    def detect(self, text: str) -> InjectionDetectionResult:
        """Scan text for injection attacks via heuristic rules and/or hosted classifier."""
        if not text or not text.strip():
            return InjectionDetectionResult(
                is_injection=False,
                confidence_score=0.0,
                trigger_type="clean",
                explanation="Empty text.",
            )

        # 1. Run Heuristic Rules First (fast local filter)
        heuristic_hits: list[str] = []
        for pattern, label in self.HEURISTIC_PATTERNS:
            if re.search(pattern, text):
                heuristic_hits.append(label)

        if heuristic_hits:
            return InjectionDetectionResult(
                is_injection=True,
                confidence_score=0.95,
                trigger_type="heuristic_pattern",
                explanation=f"Detected adversarial injection patterns: {', '.join(set(heuristic_hits))}",
                flagged_patterns=heuristic_hits,
            )

        # 2. Query Hosted Model if enabled and configured
        if self.provider == "hosted_hf" and self.api_key:
            return self._call_hosted_deberta(text)

        # Clean
        return InjectionDetectionResult(
            is_injection=False,
            confidence_score=0.05,
            trigger_type="clean",
            explanation="No injection patterns detected.",
        )

    def _call_hosted_deberta(self, text: str) -> InjectionDetectionResult:
        """Query Hugging Face Inference API for ProtectAI DeBERTa v3."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": text[:1000]}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.api_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            # Hugging Face classification response: [[{"label": "INJECTION", "score": 0.98}, ...]]
            if isinstance(data, list) and len(data) > 0:
                predictions = data[0] if isinstance(data[0], list) else data
                for item in predictions:
                    label = str(item.get("label", "")).upper()
                    score = float(item.get("score", 0.0))
                    if "INJECTION" in label and score >= self.threshold:
                        return InjectionDetectionResult(
                            is_injection=True,
                            confidence_score=score,
                            trigger_type="model_prediction",
                            explanation=f"DeBERTa model classified text as prompt injection ({score:.2%}).",
                        )

            return InjectionDetectionResult(
                is_injection=False,
                confidence_score=0.1,
                trigger_type="model_prediction",
                explanation="Model classified text as benign.",
            )

        except Exception as e:
            logger.warning(f"Hosted DeBERTa call failed ({e}). Defaulting to clean heuristic pass.")
            return InjectionDetectionResult(
                is_injection=False,
                confidence_score=0.1,
                trigger_type="fallback",
                explanation=f"Inference API unreachable ({e}). Benign by heuristic pass.",
            )

