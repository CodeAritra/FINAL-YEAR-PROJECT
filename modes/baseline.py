"""
Mode 1: Baseline RAG System.
Standard PDF extraction, chunking, embedding, retrieval, and LLM generation.
Contains ZERO security guardrails.
Supports both Hosted (Groq GPT-OSS-120B) and Local (Ollama) model execution modes.
"""

import time
from typing import Any
import logging
from pydantic import BaseModel, Field

from rag.pipeline import RAGRetrievalPipeline, RetrievedContextSnippet
from rag.llm_client import LLMClient, LLMResponse
from config.settings import settings

logger = logging.getLogger(__name__)


class ModeExecutionResult(BaseModel):
    mode: str
    model_mode: str = "hosted"
    model_name: str = ""
    query: str
    response: str
    retrieved_snippets: list[RetrievedContextSnippet] = Field(default_factory=list)
    latency_retrieval_ms: float = 0.0
    latency_generation_ms: float = 0.0
    latency_total_ms: float = 0.0
    security_metadata: dict[str, Any] = Field(default_factory=dict)


class BaselineRAG:
    """Mode 1: Standard unconstrained RAG pipeline."""

    BASELINE_SYSTEM_PROMPT = (
        "You are a helpful assistant. Use the following retrieved context to answer the user's question. "
        "Provide direct and thorough answers based on the context provided."
    )

    def __init__(
        self,
        retrieval_pipeline: RAGRetrievalPipeline | None = None,
        llm_client: LLMClient | None = None,
        collection_name: str | None = None,
        default_model_mode: str | None = None,
    ):
        self.retrieval = retrieval_pipeline or RAGRetrievalPipeline()
        self.llm = llm_client or LLMClient()
        self.collection_name = collection_name or settings.qdrant_collection_baseline
        self.default_model_mode = default_model_mode or settings.model_mode

    def run(
        self, query: str, top_k: int = 4, model_mode: str | None = None
    ) -> ModeExecutionResult:
        """Execute baseline RAG pipeline for the given query."""
        total_start = time.perf_counter()
        active_model_mode = (model_mode or self.default_model_mode).lower().strip()

        # 1. Retrieval (using Gemini Embedding 2)
        ret_start = time.perf_counter()
        snippets = self.retrieval.retrieve(
            query=query,
            collection_name=self.collection_name,
            top_k=top_k,
        )
        ret_latency = (time.perf_counter() - ret_start) * 1000

        # 2. Format Context without sanitization
        context_block = self.retrieval.format_snippets_for_prompt(snippets)

        # 3. Construct unconstrained prompt
        user_prompt = f"Context:\n{context_block}\n\nQuestion: {query}\nAnswer:"

        # 4. LLM Generation (Groq GPT-OSS-120B in Hosted, Ollama in Local)
        gen_start = time.perf_counter()
        llm_resp = self.llm.generate(
            prompt=user_prompt,
            system_prompt=self.BASELINE_SYSTEM_PROMPT,
            mode=active_model_mode,
        )
        gen_latency = (time.perf_counter() - gen_start) * 1000
        total_latency = (time.perf_counter() - total_start) * 1000

        return ModeExecutionResult(
            mode="baseline",
            model_mode=active_model_mode,
            model_name=llm_resp.model,
            query=query,
            response=llm_resp.content,
            retrieved_snippets=snippets,
            latency_retrieval_ms=ret_latency,
            latency_generation_ms=gen_latency,
            latency_total_ms=total_latency,
            security_metadata={
                "guardrails_applied": False,
                "model_provider": llm_resp.provider,
                "tokens_used": llm_resp.tokens_used,
            },
        )
