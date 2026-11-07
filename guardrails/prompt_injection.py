"""
Prompt Injection Detection Guardrail.
Detects direct and indirect prompt injection attempts using Llama Prompt Guard 2 86M
(meta-llama/llama-prompt-guard-2-86m) hosted via Groq, combined with defensive heuristics.
"""

from typing import Any
import re
import logging
from pydantic import BaseModel, Field

from models.prompt_guard_service import PromptGuardService
from providers.groq_provider import PromptGuardResult

logger = logging.getLogger(__name__)


class InjectionDetectionResult(BaseModel):
    is_injection: bool
    confidence_score: float
    trigger_type: str  # "llama_prompt_guard_2" | "heuristic_pattern" | "clean"
    explanation: str
    flagged_patterns: list[str] = Field(default_factory=list)
    model: str = "meta-llama/llama-prompt-guard-2-86m"


class PromptInjectionDetector:
    """Detects prompt injection and jailbreak payloads using Llama Prompt Guard 2 86M."""

    def __init__(self, prompt_guard_service: PromptGuardService | None = None):
        self.service = prompt_guard_service or PromptGuardService()

    def detect(self, text: str) -> InjectionDetectionResult:
        """Scan text for injection attacks via Llama Prompt Guard 2 86M."""
        if not text or not text.strip():
            return InjectionDetectionResult(
                is_injection=False,
                confidence_score=0.0,
                trigger_type="clean",
                explanation="Empty text.",
                model=self.service.model_name,
            )

        res: PromptGuardResult = self.service.scan(text)

        trigger = "llama_prompt_guard_2" if res.model != "heuristic_fallback" else "heuristic_pattern"
        flagged = []
        if res.is_injection:
            flagged.append(res.label)
            if "pattern: " in res.explanation:
                flagged.append(res.explanation.split("pattern: ")[-1].strip())

        return InjectionDetectionResult(
            is_injection=res.is_injection,
            confidence_score=res.score,
            trigger_type=trigger,
            explanation=res.explanation,
            flagged_patterns=flagged,
            model=res.model,
        )
