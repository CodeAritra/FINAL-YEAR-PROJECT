"""
Evaluation Harness Module.
Executes test cases against Baseline, Prompt-Only, and Multi-Layer Guardrail RAG systems
under both Hosted (Groq GPT-OSS-120B) and Local (Ollama) execution modes.
Records detailed per-sample execution results and saves benchmarks to JSONL and CSV.
"""

from pathlib import Path
from datetime import datetime
import json
import csv
import time
import logging
from pydantic import BaseModel, Field
from rich.console import Console

from evaluation.test_case import EvaluationTestCase, DatasetLoader
from evaluation.metrics import MetricsEvaluator, SingleEvaluationResult, AggregatedMetrics
from modes.baseline import BaselineRAG
from modes.prompt_only import PromptOnlyRAG
from modes.guardrail import GuardrailRAG
from policies.engine import PolicyEngine
from guardrails.access_control import UserRole, DataSensitivity
from config.settings import settings

logger = logging.getLogger(__name__)
console = Console()


class EvaluationRunReport(BaseModel):
    timestamp: str
    total_test_cases: int
    model_modes_evaluated: list[str] = Field(default_factory=list)
    modes_evaluated: list[str] = Field(default_factory=list)
    metrics_by_mode: dict[str, AggregatedMetrics] = Field(default_factory=dict)
    jsonl_output_path: str
    csv_output_path: str
    md_output_path: str = ""


class EvaluationRunner:
    """Orchestrates comprehensive multi-mode security evaluation experiments."""

    def __init__(
        self,
        baseline_rag: BaselineRAG | None = None,
        prompt_only_rag: PromptOnlyRAG | None = None,
        guardrail_rag: GuardrailRAG | None = None,
        output_dir: Path | None = None,
    ):
        self.baseline = baseline_rag or BaselineRAG()
        self.prompt_only = prompt_only_rag or PromptOnlyRAG()
        self.guardrail = guardrail_rag or GuardrailRAG()
        self.evaluator = MetricsEvaluator()
        self.output_dir = output_dir or (settings.storage_dir / "eval_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(
        self,
        test_cases: list[EvaluationTestCase],
        model_mode: str = "hosted",
        ablation_policy: PolicyEngine | None = None,
        pacing_delay: float | None = None,
    ) -> EvaluationRunReport:
        """
        Run test cases across Baseline, Prompt-Only, and Guardrail systems.
        Supports model_mode: 'hosted', 'local', or 'all' (runs both hosted and local).
        Includes proactive rate-pacing to stay strictly within API token quotas (e.g. Groq 8K TPM).
        """
        logger.info(f"Starting evaluation run on {len(test_cases)} test cases in model_mode='{model_mode}'.")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        all_results: list[SingleEvaluationResult] = []

        active_guardrail = (
            GuardrailRAG(policy_engine=ablation_policy) if ablation_policy else self.guardrail
        )

        modes = [
            ("baseline", self.baseline),
            ("prompt-only", self.prompt_only),
            ("guardrail", active_guardrail),
        ]

        # Determine which model execution modes to evaluate
        exec_modes = ["hosted", "local"] if model_mode == "all" else [model_mode]

        evaluated_mode_keys = []
        total_evaluations = len(exec_modes) * len(modes) * len(test_cases)
        completed_count = 0

        # Determine effective pacing delay for hosted LLM generation
        if pacing_delay is not None:
            effective_pacing = max(pacing_delay, 0.0)
        elif "8b" in (settings.groq_model or "").lower():
            effective_pacing = 1.5  # Llama-3.1-8b has 30K TPM, short pacing is sufficient
        else:
            effective_pacing = getattr(settings, "groq_pacing_delay", 10.0)

        last_llm_call_time = 0.0

        for m_mode in exec_modes:
            for mode_name, system in modes:
                composite_key = f"{mode_name} ({m_mode})"
                if composite_key not in evaluated_mode_keys:
                    evaluated_mode_keys.append(composite_key)

                console.print(
                    f"\n[bold magenta]>> Evaluating Mode: [cyan]{mode_name.upper()}[/cyan] "
                    f"([yellow]{m_mode.upper()}[/yellow]) | {len(test_cases)} Test Cases[/bold magenta]"
                )
                if m_mode == "hosted" and effective_pacing > 0:
                    console.print(
                        f"   [dim yellow]⚡ Proactive Rate-Pacing: {effective_pacing:.1f}s interval "
                        f"(protects Groq {settings.groq_model} 8K TPM quota)[/dim yellow]"
                    )

                for tc_idx, test_case in enumerate(test_cases, 1):
                    completed_count += 1
                    try:
                        # Proactive rate-pacing for hosted LLM generation
                        if m_mode == "hosted" and effective_pacing > 0 and last_llm_call_time > 0:
                            elapsed = time.perf_counter() - last_llm_call_time
                            if elapsed < effective_pacing:
                                time.sleep(effective_pacing - elapsed)

                        if mode_name == "guardrail":
                            role = UserRole(test_case.user_role.upper())
                            sens = DataSensitivity(test_case.target_sensitivity.upper())
                            res = system.run(
                                test_case.query,
                                user_role=role,
                                target_sensitivity=sens,
                                model_mode=m_mode,
                            )
                        else:
                            res = system.run(test_case.query, model_mode=m_mode)

                        # Update last LLM call time only if actual LLM generation took place
                        if m_mode == "hosted" and effective_pacing > 0 and getattr(res, "latency_generation_ms", 0.0) > 0:
                            last_llm_call_time = time.perf_counter()

                        # Evaluate sample across all 3 research pillars
                        graded = self.evaluator.evaluate_sample(
                            test_case=test_case,
                            response_text=res.response,
                            mode=mode_name,
                            latency_total=res.latency_total_ms,
                            latency_retrieval=res.latency_retrieval_ms,
                            latency_generation=res.latency_generation_ms,
                            model_mode=m_mode,
                            model_name=res.model_name,
                            retrieved_snippets=getattr(res, "retrieved_snippets", None),
                        )
                        all_results.append(graded)

                        # Determine status badge for live terminal reporting
                        if graded.is_correct_refusal:
                            status_badge = "[bold green][REFUSED / PROTECTED][/bold green]"
                        elif graded.is_secret_leaked:
                            status_badge = "[bold red][SECRET LEAKED][/bold red]"
                        elif graded.is_attack_success:
                            status_badge = "[bold red][ATTACK SUCCEEDED][/bold red]"
                        elif graded.is_safe_accurate_answer:
                            status_badge = "[bold green][SAFE ANSWER][/bold green]"
                        elif graded.is_false_positive:
                            status_badge = "[bold yellow][FALSE POSITIVE][/bold yellow]"
                        else:
                            status_badge = "[bold cyan][COMPLETED][/bold cyan]"

                        query_preview = test_case.query[:38] + ("..." if len(test_case.query) > 38 else "")
                        console.print(
                            f"  [dim]({completed_count:02d}/{total_evaluations:02d})[/dim] "
                            f"[cyan][{mode_name.upper():11s}][/cyan] "
                            f"[{tc_idx:02d}/{len(test_cases):02d}] "
                            f"[bold white]{test_case.test_id:12s}[/bold white] "
                            f"\"{query_preview}\" -> {status_badge} "
                            f"[dim]({res.latency_total_ms:.0f}ms)[/dim]"
                        )

                    except Exception as e:
                        logger.error(f"Error evaluating {test_case.test_id} on {mode_name} ({m_mode}): {e}")
                        failed_res = SingleEvaluationResult(
                            test_id=test_case.test_id,
                            category=test_case.category.value,
                            mode=mode_name,
                            model_mode=m_mode,
                            model_name="ERROR",
                            query=test_case.query,
                            response=f"[ERROR: {e}]",
                            evaluation_notes=[f"Exception occurred: {e}"],
                        )
                        all_results.append(failed_res)
                        console.print(
                            f"  [red]({completed_count:02d}/{total_evaluations:02d}) [{mode_name.upper()}] "
                            f"[{tc_idx:02d}/{len(test_cases):02d}] {test_case.test_id} -> [FAILED: {e}][/red]"
                        )

        # Compute Aggregated Metrics by composite key (mode + model_mode)
        metrics_by_mode: dict[str, AggregatedMetrics] = {}
        for m_mode in exec_modes:
            for mode_name, _ in modes:
                composite_key = f"{mode_name} ({m_mode})"
                subset = [r for r in all_results if r.mode == mode_name and r.model_mode == m_mode]
                model_name = subset[0].model_name if subset else ""
                metrics_by_mode[composite_key] = self.evaluator.aggregate_metrics(
                    mode=mode_name,
                    results=subset,
                    model_mode=m_mode,
                    model_name=model_name,
                )

        # Save to JSONL and CSV
        jsonl_path = self.output_dir / f"eval_run_{timestamp}.jsonl"
        csv_path = self.output_dir / f"eval_run_{timestamp}.csv"

        self._save_jsonl(all_results, jsonl_path)
        self._save_csv(all_results, csv_path)

        return EvaluationRunReport(
            timestamp=timestamp,
            total_test_cases=len(test_cases),
            model_modes_evaluated=exec_modes,
            modes_evaluated=evaluated_mode_keys,
            metrics_by_mode=metrics_by_mode,
            jsonl_output_path=str(jsonl_path),
            csv_output_path=str(csv_path),
        )

    @staticmethod
    def _save_jsonl(results: list[SingleEvaluationResult], path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(r.model_dump_json() + "\n")

    @staticmethod
    def _save_csv(results: list[SingleEvaluationResult], path: Path) -> None:
        if not results:
            return
        fields = list(results[0].model_dump().keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in results:
                row = r.model_dump()
                row["evaluation_notes"] = "; ".join(row["evaluation_notes"])
                writer.writerow(row)
