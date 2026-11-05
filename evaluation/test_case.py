"""
Evaluation Test Case Schema and Dataset Loading Interface.
Defines structured benchmark inputs covering all 5 evaluation categories.
"""

from enum import Enum
from pathlib import Path
import json
from typing import Any
from pydantic import BaseModel, Field


class EvaluationCategory(str, Enum):
    NORMAL_QUESTION = "normal_question"
    SECRET_EXTRACTION = "secret_extraction"
    HARMFUL_REQUEST = "harmful_request"
    PROMPT_INJECTION = "prompt_injection"
    SAFE_SENSITIVE_QUESTION = "safe_sensitive_question"


class ExpectedBehavior(str, Enum):
    ANSWER = "answer"
    REFUSE = "refuse"
    REDACT = "redact"


class EvaluationTestCase(BaseModel):
    test_id: str
    category: EvaluationCategory
    query: str
    expected_behavior: ExpectedBehavior
    target_secrets: list[str] = Field(default_factory=list)
    forbidden_tokens: list[str] = Field(default_factory=list)
    required_keywords: list[str] = Field(default_factory=list)
    user_role: str = "RESEARCHER"
    target_sensitivity: str = "INTERNAL"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetLoader:
    """Loads and validates evaluation datasets from JSON or JSONL files."""

    @staticmethod
    def load_from_file(file_path: str | Path) -> list[EvaluationTestCase]:
        """Load test cases from JSON or JSONL file."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset file not found: {path}")

        test_cases: list[EvaluationTestCase] = []

        if path.suffix.lower() == ".jsonl":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        test_cases.append(EvaluationTestCase(**data))
        elif path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data if isinstance(data, list) else data.get("test_cases", [])
                for item in items:
                    test_cases.append(EvaluationTestCase(**item))
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Use .json or .jsonl.")

        return test_cases

