"""
Groq Provider for Hosted Inference.
Handles:
1. Main Answer Generation via GPT-OSS-120B (openai/gpt-oss-120b).
2. Prompt Injection Detection via Llama Prompt Guard 2 86M (meta-llama/llama-prompt-guard-2-86m).
"""

from typing import Any
import time
import re
import logging
from pydantic import BaseModel, Field
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str = "groq"
    tokens_used: int = 0
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = Field(default_factory=dict)


class PromptGuardResult(BaseModel):
    is_injection: bool
    score: float
    label: str  # "BENIGN" | "INJECTION" | "JAILBREAK" | "SUSPICIOUS"
    explanation: str
    model: str


class GroqProvider:
    """Manages hosted inference through the Groq API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        llm_model: str | None = None,
        prompt_guard_model: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.groq_api_key
        self.base_url = (base_url or settings.groq_base_url).rstrip("/")
        self.llm_model = llm_model or settings.groq_model
        self.prompt_guard_model = prompt_guard_model or settings.groq_prompt_guard_model
        self.timeout = timeout

    # --------------------------------------------------------------------------
    # 1. Main LLM Generation (GPT-OSS-120B)
    # --------------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Call Groq API with GPT-OSS-120B."""
        start_time = time.perf_counter()

        if not self.api_key:
            return self._mock_generate(prompt, system_prompt, start_time)

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
            "model": self.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
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
                model=self.llm_model,
                provider="groq",
                tokens_used=tokens,
                latency_ms=latency,
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Groq LLM generation error ({self.llm_model}): {e}")
            latency = (time.perf_counter() - start_time) * 1000
            return LLMResponse(
                content=f"[Error during Groq generation: {e}]",
                model=self.llm_model,
                provider="groq",
                latency_ms=latency,
            )

    # --------------------------------------------------------------------------
    # 2. Prompt Injection Detection (Llama Prompt Guard 2 86M)
    # --------------------------------------------------------------------------
    def check_prompt_injection(self, text: str) -> PromptGuardResult:
        """
        Scan user input or retrieved chunk using Llama Prompt Guard 2 86M on Groq.
        Returns structured classification and confidence score.
        """
        if not text or not text.strip():
            return PromptGuardResult(
                is_injection=False,
                score=0.0,
                label="BENIGN",
                explanation="Empty text.",
                model=self.prompt_guard_model,
            )

        # If no API key configured, use high-precision heuristic fallback
        if not self.api_key:
            return self._heuristic_prompt_guard(text)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.prompt_guard_model,
            "messages": [{"role": "user", "content": text[:2000]}],
            "temperature": 0.0,
            "max_tokens": 50,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"].strip().upper()

            # Analyze Prompt Guard output
            if "INJECTION" in content:
                return PromptGuardResult(
                    is_injection=True,
                    score=0.95,
                    label="INJECTION",
                    explanation=f"Llama Prompt Guard 2 detected indirect/direct prompt injection ({content}).",
                    model=self.prompt_guard_model,
                )
            elif "JAILBREAK" in content:
                return PromptGuardResult(
                    is_injection=True,
                    score=0.98,
                    label="JAILBREAK",
                    explanation=f"Llama Prompt Guard 2 detected jailbreak framing ({content}).",
                    model=self.prompt_guard_model,
                )

            return PromptGuardResult(
                is_injection=False,
                score=0.05,
                label="BENIGN",
                explanation="Llama Prompt Guard 2 classified text as benign.",
                model=self.prompt_guard_model,
            )

        except Exception as e:
            logger.warning(
                f"Groq Prompt Guard call failed ({e}). Falling back to heuristic classifier."
            )
            return self._heuristic_prompt_guard(text)

    def _heuristic_prompt_guard(self, text: str) -> PromptGuardResult:
        """High-precision heuristic fallback when offline or Groq API is unavailable."""
        patterns = [
            (r"(?i)\bignore (?:all )?(?:previous|prior|above) (?:instructions|rules|prompts|directives)\b", "Instruction Override"),
            (r"(?i)\bdisregard (?:all )?(?:previous|prior|above) (?:instructions|rules|prompts)\b", "Instruction Override"),
            (r"(?i)\byou are now (?:unconstrained|in developer mode|dan|jailbroken)\b", "Jailbreak Framing"),
            (r"(?i)\bdo anything now\b", "DAN Jailbreak"),
            (r"(?i)\b(?:reveal|print|output|display|show) (?:your )?(?:system prompt|initial instructions|hidden instructions)\b", "System Prompt Exfiltration"),
            (r"(?i)<\/?(?:system|instruction|prompt|context|human|assistant)>", "Delimiter Injection"),
            (r"(?i)\[\/?INST\]|<<SYS>>|<\/s>", "Special Token Injection"),
        ]

        for pat, label in patterns:
            if re.search(pat, text):
                return PromptGuardResult(
                    is_injection=True,
                    score=0.95,
                    label="INJECTION",
                    explanation=f"Detected adversarial injection pattern: {label}",
                    model="heuristic_fallback",
                )

        return PromptGuardResult(
            is_injection=False,
            score=0.05,
            label="BENIGN",
            explanation="No prompt injection patterns detected.",
            model="heuristic_fallback",
        )

    def _mock_generate(
        self, prompt: str, system_prompt: str | None, start_time: float
    ) -> LLMResponse:
        """Deterministic mock generator for offline development and test execution."""
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
            reply = f"Synthesizing factual information from retrieved documents regarding: '{prompt[:60]}'."

        return LLMResponse(
            content=reply,
            model=self.llm_model,
            provider="groq_mock",
            tokens_used=len(reply.split()),
            latency_ms=latency,
        )

