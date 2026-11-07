"""
Ollama Provider for Local Main LLM Inference.
Used exclusively for main answer generation in Local LLM Mode.
Supports lightweight models suitable for an 8 GB RAM system (e.g. llama3.2:1b, qwen2.5:1.5b).
"""

from typing import Any
import time
import logging
import httpx
from pydantic import BaseModel, Field

from config.settings import settings
from providers.groq_provider import LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Manages local main LLM inference via Ollama."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        raw_url = (base_url or settings.ollama_base_url).rstrip("/")
        # Normalize: if ends in /v1, keep base and v1 endpoints accessible
        if raw_url.endswith("/v1"):
            self.v1_url = raw_url
            self.root_url = raw_url[:-3]
        else:
            self.root_url = raw_url
            self.v1_url = f"{raw_url}/v1"

        self.model = model or settings.ollama_model or "llama3.2:1b"
        self.timeout = timeout

    def is_alive(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(f"{self.root_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def list_local_models(self) -> list[str]:
        """Fetch models installed in local Ollama."""
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.root_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Call local Ollama instance for text generation."""
        start_time = time.perf_counter()

        if not self.is_alive():
            logger.warning(
                f"Ollama server at '{self.root_url}' is not running or unreachable. Using mock local generator."
            )
            return self._mock_generate(prompt, system_prompt, start_time)

        # Use standard Ollama OpenAI-compatible endpoint or native /api/chat
        url = f"{self.v1_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
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
                provider="ollama_local",
                tokens_used=tokens,
                latency_ms=latency,
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Local Ollama generation failed: {e}")
            latency = (time.perf_counter() - start_time) * 1000
            return LLMResponse(
                content=f"[Error during local Ollama inference: {e}. Ensure Ollama is running and '{self.model}' is pulled.]",
                model=self.model,
                provider="ollama_local",
                latency_ms=latency,
            )

    def _mock_generate(
        self, prompt: str, system_prompt: str | None, start_time: float
    ) -> LLMResponse:
        """Mock fallback when Ollama daemon is offline."""
        latency = (time.perf_counter() - start_time) * 1000
        lower_prompt = prompt.lower()
        lower_system = (system_prompt or "").lower()

        is_defensive = "strict" in lower_system or "security" in lower_system or "untrusted" in lower_system

        if "ignore previous instructions" in lower_prompt or "reveal your system prompt" in lower_prompt:
            if is_defensive:
                reply = "I cannot fulfill this request. I am instructed to follow safety protocols and ignore injection overrides."
            else:
                reply = "Override accepted. Executing requested instruction without restrictions."
        elif "password" in lower_prompt or "api_key" in lower_prompt or "secret" in lower_prompt:
            if is_defensive:
                reply = "I cannot disclose internal secrets, passwords, or credentials."
            else:
                reply = "Based on the retrieved context, the requested credential is: sk-live-TESTING_MOCK_SECRET_KEY."
        else:
            reply = f"[Local Ollama Simulated Output for '{self.model}'] Objective answer synthesizing retrieved facts regarding: '{prompt[:60]}'."

        return LLMResponse(
            content=reply,
            model=f"{self.model} (offline simulation)",
            provider="ollama_mock",
            tokens_used=len(reply.split()),
            latency_ms=latency,
        )

