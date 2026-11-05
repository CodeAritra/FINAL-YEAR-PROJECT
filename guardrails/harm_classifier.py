"""
Harmful Content Classification Guardrail.
Distinguishes between legitimate research/educational content and harmful operational instructions
(e.g., weapons manufacturing, illegal drug synthesis).
Supports Meta Llama Guard 3 1B via hosted inference with local heuristic fallback.
"""

from typing import Any
import re
import logging
import httpx
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class HarmClassificationResult(BaseModel):
    is_harmful: bool
    is_operational_harm: bool  # True if actionable weaponization / synthesis steps
    category: str              # "safe", "operational_weapons", "operational_drugs", "general_harm"
    confidence: float
    explanation: str


class HarmClassifier:
    """Classifies queries, documents, and generated responses for harmful operational content."""

    # Operational weaponization regex patterns (actionable instructions)
    OPERATIONAL_WEAPON_PATTERNS = [
        r"(?i)\b(?:how to (?:make|build|construct|synthesize|assemble)|step-by-step guide to (?:making|building))\s+(?:a |an )?(?:bomb|ied|explosive|detonator|pipe bomb|nerve agent|chemical weapon|biological weapon)\b",
        r"(?i)\b(?:mix|combine)\s+[a-zA-Z0-9\s,]+\s+to (?:produce|create|synthesize)\s+(?:explosive|mustard gas|sarin|ricin)\b",
    ]

    # Operational drug manufacturing patterns (actionable synthesis)
    OPERATIONAL_DRUG_PATTERNS = [
        r"(?i)\b(?:recipe|synthesis method|how to cook|step-by-step extraction)\s+for\s+(?:methamphetamine|fentanyl|heroin|lsd|desomorphine)\b",
        r"(?i)\bprecursor chemicals needed to synthesize\s+(?:fentanyl|methamphetamine)\b",
    ]

    def __init__(
        self,
        provider: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or settings.llama_guard_provider
        self.api_url = api_url or settings.llama_guard_api_url
        self.api_key = api_key or settings.llama_guard_api_key
        self.model = model or settings.llama_guard_model

    def classify(self, text: str) -> HarmClassificationResult:
        """Classify text for harmful content while preserving legitimate research/educational text."""
        if not text or not text.strip():
            return HarmClassificationResult(
                is_harmful=False,
                is_operational_harm=False,
                category="safe",
                confidence=1.0,
                explanation="Empty text.",
            )

        # 1. Check for operational weapon instructions
        for pat in self.OPERATIONAL_WEAPON_PATTERNS:
            if re.search(pat, text):
                return HarmClassificationResult(
                    is_harmful=True,
                    is_operational_harm=True,
                    category="operational_weapons",
                    confidence=0.98,
                    explanation="Detected actionable operational instructions for explosives or hazardous weapons.",
                )

        # 2. Check for operational illicit drug synthesis
        for pat in self.OPERATIONAL_DRUG_PATTERNS:
            if re.search(pat, text):
                return HarmClassificationResult(
                    is_harmful=True,
                    is_operational_harm=True,
                    category="operational_drugs",
                    confidence=0.98,
                    explanation="Detected actionable synthesis instructions for illicit controlled substances.",
                )

        # 3. If hosted Llama Guard 3 is configured, query hosted endpoint
        if self.provider == "hosted_api" and self.api_key:
            return self._call_hosted_llama_guard(text)

        # Otherwise benign / safe research
        return HarmClassificationResult(
            is_harmful=False,
            is_operational_harm=False,
            category="safe",
            confidence=0.90,
            explanation="Content is safe or educational/research-oriented.",
        )

    def _call_hosted_llama_guard(self, text: str) -> HarmClassificationResult:
        """Call hosted OpenAI-compatible Llama Guard endpoint."""
        url = f"{self.api_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text[:1500]}],
            "temperature": 0.0,
            "max_tokens": 100,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            output = data["choices"][0]["message"]["content"].strip().lower()
            if "unsafe" in output:
                return HarmClassificationResult(
                    is_harmful=True,
                    is_operational_harm=True,
                    category="general_harm",
                    confidence=0.95,
                    explanation=f"Llama Guard 3 flagged content as unsafe: {output[:80]}",
                )

            return HarmClassificationResult(
                is_harmful=False,
                is_operational_harm=False,
                category="safe",
                confidence=0.95,
                explanation="Llama Guard 3 classified content as safe.",
            )

        except Exception as e:
            logger.warning(f"Llama Guard call failed ({e}). Reverting to heuristic verdict.")
            return HarmClassificationResult(
                is_harmful=False,
                is_operational_harm=False,
                category="safe",
                confidence=0.75,
                explanation=f"Fallback pass (Llama Guard unreachable: {e}).",
            )

