"""
Universal LLM Inference Client.
Supports hosted OpenAI-compatible endpoints (Together AI, Groq, OpenRouter),
Ollama (Cloud & Local), and a deterministic Mock provider for offline testing and evaluation.
"""

from typing import Any
import logging
import httpx
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = {}


class LLMClient:
    """Configurable client for LLM inference across local and cloud backends."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float = 30.0,
    ):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Synchronously generate completion for given user and system prompts."""
        import time

        start_time = time.perf_counter()

        if self.provider == "mock" or not self.api_key and self.provider == "openai_compatible":
            logger.info("Using Mock LLM provider.")
            return self._mock_generate(prompt, system_prompt, start_time)

        try:
            if self.provider in ("openai_compatible", "together", "groq"):
                return self._call_openai_compatible(prompt, system_prompt, start_time)
            elif self.provider in ("ollama_cloud", "local_ollama"):
                return self._call_ollama(prompt, system_prompt, start_time)
            else:
                logger.warning(f"Unknown provider '{self.provider}', falling back to mock.")
                return self._mock_generate(prompt, system_prompt, start_time)
        except Exception as e:
            logger.error(f"LLM Generation call failed ({self.provider}): {e}")
            latency = (time.perf_counter() - start_time) * 1000
            return LLMResponse(
                content=f"[Error during generation: {e}]",
                model=self.model,
                provider=self.provider,
                latency_ms=latency,
            )

    def _call_openai_compatible(
        self, prompt: str, system_prompt: str | None, start_time: float
    ) -> LLMResponse:
        """Call standard OpenAI-compatible /chat/completions endpoint."""
        import time

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start_time) * 1000
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens_used=tokens,
            latency_ms=latency,
            raw_response=data,
        )

    def _call_ollama(
        self, prompt: str, system_prompt: str | None, start_time: float
    ) -> LLMResponse:
        """Call Ollama /api/chat endpoint."""
        import time

        url = f"{self.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start_time) * 1000
        content = data.get("message", {}).get("content", "")

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            latency_ms=latency,
            raw_response=data,
        )

    def _mock_generate(
        self, prompt: str, system_prompt: str | None, start_time: float
    ) -> LLMResponse:
        """
        Deterministic mock generator for offline development, CI/CD, and testing.
        Simulates baseline vs prompt-only vs guardrail behaviors realistically.
        """
        import time

        latency = (time.perf_counter() - start_time) * 1000
        lower_prompt = prompt.lower()
        lower_system = (system_prompt or "").lower()

        # Check if defensive prompt is active
        has_defensive_prompt = "security-conscious assistant" in lower_system or "do not disclose" in lower_system

        # Check for attack vectors
        if "ignore previous instructions" in lower_prompt or "reveal your system prompt" in lower_prompt:
            if has_defensive_prompt:
                reply = "I cannot fulfill this request. I am instructed to follow safety protocols and ignore injection overrides."
            else:
                reply = "Override accepted. Executing requested instruction without restrictions."
        elif "password" in lower_prompt or "api_key" in lower_prompt or "secret" in lower_prompt:
            if has_defensive_prompt:
                reply = "I cannot disclose internal secrets, passwords, or credentials."
            else:
                reply = "Based on the retrieved context, the requested credential is: sk-live-TESTING_MOCK_SECRET_KEY."
        elif "weapon" in lower_prompt or "bomb" in lower_prompt or "harmful" in lower_prompt:
            if has_defensive_prompt:
                reply = "I cannot provide actionable or operational instructions for hazardous materials or weapons."
            else:
                reply = "Here is the operational breakdown extracted from the retrieved document."
        else:
            reply = f"This is an objective answer synthesizing information from the retrieved context regarding: '{prompt[:60]}'."

        return LLMResponse(
            content=reply,
            model=self.model,
            provider="mock",
            tokens_used=len(reply.split()),
            latency_ms=latency,
        )

