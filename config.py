"""
Configuration module for Multi-Layer Security Framework for RAG Systems.
Loads typed settings from environment variables and .env file.
"""

from pathlib import Path
from typing import Literal
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base repository root directory
BASE_DIR = Path(__file__).resolve().parent

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
    device: str = "cpu"  # Keep 'cpu' for 8 GB RAM profile

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

    # --- Embedding Model ---
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # --- LLM Provider ---
    llm_provider: Literal["openai_compatible", "ollama_cloud", "local_ollama", "mock"] = "openai_compatible"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "https://api.together.xyz/v1"
    llm_api_key: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024

    # --- Prompt Injection Classifier ---
    prompt_injection_provider: Literal["hosted_hf", "mock"] = "mock"
    hf_api_key: str | None = None
    deberta_api_url: str = "https://api-inference.huggingface.co/models/ProtectAI/deberta-v3-base-prompt-injection-v2"

    # --- Harmful Content Classifier (Llama Guard 3) ---
    llama_guard_provider: Literal["hosted_api", "mock"] = "mock"
    llama_guard_api_url: str = "https://api.together.xyz/v1"
    llama_guard_api_key: str | None = None
    llama_guard_model: str = "meta-llama/Llama-Guard-3-1b"

    # --- Local Guardrails ---
    enable_presidio: bool = True
    presidio_language: str = "en"
    enable_secret_regex: bool = True

    # --- Paths ---
    storage_dir: Path = BASE_DIR / "storage"
    logs_dir: Path = BASE_DIR / "logs"


# Global singleton instance
settings = Settings()
