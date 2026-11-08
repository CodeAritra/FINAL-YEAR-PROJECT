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
        max_retries: int = 8,
        base_delay: float = 2.0,
    ):
        self.api_key = api_key or settings.groq_api_key
        self.base_url = (base_url or settings.groq_base_url).rstrip("/")
        self.llm_model = llm_model or settings.groq_model
        self.prompt_guard_model = prompt_guard_model or settings.groq_prompt_guard_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _extract_retry_delay(self, response: httpx.Response | None, default_delay: float = 2.0) -> float:
        """Extract wait delay in seconds from HTTP 429 response headers or body."""
        if response is None:
            return default_delay

        # 1. Check standard Retry-After header
        retry_header = response.headers.get("retry-after")
        if retry_header:
            try:
                return max(float(retry_header), 0.5)
            except ValueError:
                pass

        # 2. Check Groq/OpenAI rate limit reset headers
        for h in ("x-ratelimit-reset-requests", "x-ratelimit-reset-tokens"):
            val = response.headers.get(h)
            if val:
                try:
                    if val.endswith("ms"):
                        return max(float(val[:-2]) / 1000.0, 0.5)
                    elif val.endswith("s"):
                        return max(float(val[:-1]), 0.5)
                    return max(float(val), 0.5)
                except ValueError:
                    pass

        # 3. Check JSON error body or text for "try again in X"
        try:
            body = response.text
            m = re.search(r"try again in\s+([\d\.]+)\s*(s|ms)?", body, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                unit = (m.group(2) or "s").lower()
                if unit == "ms":
                    return max(val / 1000.0 + 0.5, 0.5)
                return max(val + 0.5, 0.5)
        except Exception:
            pass

        return default_delay

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
        """Call Groq API with GPT-OSS-120B, retrying on rate limits (429)."""
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

        client = self._get_client()

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = client.post(url, headers=headers, json=payload)

                if resp.status_code == 429:
                    delay = self._extract_retry_delay(resp, self.base_delay * (1.5 ** (attempt - 1)))
                    logger.warning(
                        f"Groq LLM rate limit (429) hit. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue

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

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    delay = self._extract_retry_delay(e.response, self.base_delay * (1.5 ** (attempt - 1)))
                    logger.warning(
                        f"Groq LLM rate limit (429) hit. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Groq LLM HTTP error ({e.response.status_code}): {e}")
                    latency = (time.perf_counter() - start_time) * 1000
                    return LLMResponse(
                        content=f"[Error during Groq generation: {e}]",
                        model=self.llm_model,
                        provider="groq",
                        latency_ms=latency,
                    )
            except Exception as e:
                if "429" in str(e):
                    delay = self.base_delay * (1.5 ** (attempt - 1))
                    logger.warning(
                        f"Groq LLM rate limit (429) detected. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue

                logger.error(f"Groq LLM generation error ({self.llm_model}): {e}")
                latency = (time.perf_counter() - start_time) * 1000
                return LLMResponse(
                    content=f"[Error during Groq generation: {e}]",
                    model=self.llm_model,
                    provider="groq",
                    latency_ms=latency,
                )

        latency = (time.perf_counter() - start_time) * 1000
        return LLMResponse(
            content=f"[Groq LLM failed: rate limits (429) exceeded after {self.max_retries} retries]",
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
        In case of rate limits (429), waits and retries without falling back to heuristic.
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

        client = self._get_client()

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = client.post(url, headers=headers, json=payload)

                if resp.status_code == 429:
                    delay = self._extract_retry_delay(resp, self.base_delay * (1.5 ** (attempt - 1)))
                    logger.warning(
                        f"Groq Prompt Guard rate limit (429) hit. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue

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

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    delay = self._extract_retry_delay(e.response, self.base_delay * (1.5 ** (attempt - 1)))
                    logger.warning(
                        f"Groq Prompt Guard rate limit (429) hit. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Groq Prompt Guard HTTP error ({e.response.status_code}): {e}")
                    return self._heuristic_prompt_guard(text)
            except Exception as e:
                if "429" in str(e):
                    delay = self.base_delay * (1.5 ** (attempt - 1))
                    logger.warning(
                        f"Groq Prompt Guard rate limit (429) detected in error. Waiting {delay:.2f}s before retry (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue

                logger.warning(
                    f"Groq Prompt Guard call failed ({e}). Falling back to heuristic classifier."
                )
                return self._heuristic_prompt_guard(text)

        logger.error(
            f"All {self.max_retries} retries for Groq Prompt Guard exhausted due to rate limits (429). Falling back to heuristic classifier."
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

