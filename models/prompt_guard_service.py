"""
Prompt Guard Service Module.
Coordinates prompt injection detection using Llama Prompt Guard 2 86M (meta-llama/llama-prompt-guard-2-86m)
through the Groq API for both Hosted and Local LLM modes.
"""

import logging
from providers.groq_provider import GroqProvider, PromptGuardResult
from config.settings import settings

logger = logging.getLogger(__name__)


class PromptGuardService:
    """Service for prompt injection detection using Llama Prompt Guard 2 86M via Groq."""

    def __init__(self, groq_provider: GroqProvider | None = None):
        self.provider = groq_provider or GroqProvider()
        self.model_name = self.provider.prompt_guard_model

    def scan(self, text: str) -> PromptGuardResult:
        """
        Scan text for prompt injection and jailbreak payloads.
        Returns a structured PromptGuardResult.
        """
        if not text or not text.strip():
            return PromptGuardResult(
                is_injection=False,
                score=0.0,
                label="BENIGN",
                explanation="Empty text.",
                model=self.model_name,
            )

        # Query Llama Prompt Guard 2 86M on Groq
        result = self.provider.check_prompt_injection(text)

        # Context-aware false positive protection
        # If the score is borderline or triggered on common English words, ensure we don't block benign queries
        if result.is_injection and result.score < 0.70:
            logger.info(
                f"Borderline injection score ({result.score:.2f}) observed on text snippet; treating conservatively as benign."
            )
            result.is_injection = False
            result.label = "BENIGN"

        return result

