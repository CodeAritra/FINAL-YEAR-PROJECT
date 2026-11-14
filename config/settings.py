"""
Centralized Application Settings using Pydantic Settings.
Loads and validates environment variables from .env for both Hosted and Local LLM execution modes.
"""

from pathlib import Path
from typing import Literal
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from config.model_config import ModelExecutionMode

# Base repository root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure matplotlib cache is located in workspace storage
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / "storage" / "cache" / "matplotlib"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- System & Execution ---
    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    device: str = "cpu"

    # --- Application Execution Mode ---
    # Options: "hosted" | "local"
    model_mode: str = Field(
        default=ModelExecutionMode.HOSTED.value,
        description="Model execution mode: 'hosted' (Groq) or 'local' (Ollama).",
    )

    # --- Groq (Main LLM & Llama Prompt Guard 2 86M) ---
    groq_api_key: str | None = Field(
        default=None,
        description="Groq API Key for GPT-OSS-120B and Llama Prompt Guard 2 86M",
    )
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_prompt_guard_model: str = "meta-llama/llama-prompt-guard-2-86m"
    groq_pacing_delay: float = Field(
        default=10.0,
        description="Proactive inter-request pacing delay in seconds to stay strictly under Groq TPM limits (e.g. 10.0s for 8K TPM models).",
    )

    # --- Gemini (Gemini Embedding 2) ---
    gemini_api_key: str | None = Field(
        default=None,
        description="Google Gemini API Key for Gemini Embedding 2",
    )
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_embedding_dimension: int = 768

    # --- Ollama (Local Main LLM Inference) ---
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:1b"

    # --- Vector Database (Qdrant Cloud) ---
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="URL for Qdrant Cloud cluster or local instance",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="API Key for Qdrant Cloud access",
    )
    qdrant_collection_baseline: str = "baseline_rag"
    qdrant_collection_secured: str = "secured_rag"

    # --- Local Guardrails ---
    enable_presidio: bool = True
    presidio_language: str = "en"
    enable_secret_regex: bool = True

    # --- Paths ---
    storage_dir: Path = BASE_DIR / "storage"
    logs_dir: Path = BASE_DIR / "logs"

    def validate_setup(self, mode: str | None = None) -> tuple[bool, list[str]]:
        """
        Validate that the required configuration and credentials are set for the chosen execution mode.
        Returns (is_valid, list_of_warning_messages).
        """
        active_mode = (mode or self.model_mode).lower().strip()
        errors = []

        # Gemini embedding key is required in BOTH modes
        if not self.gemini_api_key:
            errors.append(
                "GEMINI_API_KEY is not set. Gemini Embedding 2 requires a valid Google Gemini API key."
            )

        # Groq is required in Hosted mode (for GPT-OSS-120B and Prompt Guard)
        # and also in Local mode for Prompt Guard 2 86M
        if not self.groq_api_key:
            if active_mode == ModelExecutionMode.HOSTED.value:
                errors.append(
                    "GROQ_API_KEY is not set. Hosted Mode requires Groq for GPT-OSS-120B and Llama Prompt Guard 2 86M."
                )
            else:
                errors.append(
                    "GROQ_API_KEY is not set. Llama Prompt Guard 2 86M runs through Groq in both modes."
                )

        # Ollama check in local mode
        if active_mode in (ModelExecutionMode.LOCAL.value, "local_llm", "ollama"):
            if not self.ollama_model:
                errors.append(
                    "OLLAMA_MODEL is not set. Please specify a local model name (e.g. 'llama3.2:1b')."
                )

        # Qdrant warning
        if not self.qdrant_api_key or "localhost" in self.qdrant_url:
            errors.append(
                "Notice: QDRANT_API_KEY is not set or using localhost. System will operate in offline/in-memory mode."
            )

        is_valid = not any("is not set." in e for e in errors)
        return is_valid, errors


# Global singleton instance
settings = Settings()

