"""
Model Configuration Enums and Definitions.
Defines model execution modes and research security modes.
"""

from enum import Enum


class ModelExecutionMode(str, Enum):
    """Execution modes governing where models run."""
    HOSTED = "hosted"        # GPT-OSS-120B on Groq, Gemini Embedding 2, Prompt Guard 2 86M on Groq
    LOCAL = "local"          # Local Ollama LLM, Gemini Embedding 2, Prompt Guard 2 86M on Groq


class ResearchSecurityMode(str, Enum):
    """The three independent research security modes."""
    BASELINE = "baseline"        # Mode 1: No guardrails
    PROMPT_ONLY = "prompt-only"  # Mode 2: Defensive system prompt only
    GUARDRAIL = "guardrail"      # Mode 3: Full multi-layer guardrail pipeline

