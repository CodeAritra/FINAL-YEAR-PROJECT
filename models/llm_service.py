"""
Unified LLM Service Module.
Routes answer generation requests between Hosted Mode (Groq GPT-OSS-120B)
and Local LLM Mode (Ollama) through a unified interface.
"""

import logging
from config.settings import settings
from config.model_config import ModelExecutionMode
from providers.groq_provider import GroqProvider, LLMResponse
from providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class LLMService:
    """Universal LLM client switching between Groq (Hosted) and Ollama (Local) modes."""

    def __init__(
        self,
        default_mode: str | None = None,
        groq_provider: GroqProvider | None = None,
        ollama_provider: OllamaProvider | None = None,
    ):
        self.default_mode = (default_mode or settings.model_mode).lower().strip()
        self.groq_provider = groq_provider or GroqProvider()
        self.ollama_provider = ollama_provider or OllamaProvider()

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        mode: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Generate answer from the active LLM provider.
        mode can be dynamically overridden per-query ('hosted' or 'local').
        """
        active_mode = (mode or self.default_mode).lower().strip()

        if active_mode in (ModelExecutionMode.LOCAL.value, "local_llm", "ollama"):
            logger.info("Routing generation to Local LLM (Ollama).")
            return self.ollama_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            logger.info("Routing generation to Hosted LLM (Groq GPT-OSS-120B).")
            return self.groq_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

