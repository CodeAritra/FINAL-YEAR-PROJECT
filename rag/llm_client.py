"""
Universal LLM Inference Client.
Delegates to LLMService to switch seamlessly between Hosted Mode (Groq GPT-OSS-120B)
and Local LLM Mode (Ollama).
"""

from typing import Any
import logging
from pydantic import BaseModel

from models.llm_service import LLMService
from providers.groq_provider import LLMResponse
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Configurable client for LLM inference across Hosted (Groq) and Local (Ollama) backends."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        model_mode: str | None = None,
    ):
        self.service = llm_service or LLMService()
        self.model_mode = model_mode or settings.model_mode

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        mode: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate completion using the active model execution mode."""
        active_mode = mode or self.model_mode
        return self.service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            mode=active_mode,
            temperature=temperature,
            max_tokens=max_tokens,
        )
