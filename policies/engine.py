"""
Central Policy Engine for Multi-Layer Guardrail RAG.
Coordinates explicit ALLOW, REDACT, QUARANTINE, and BLOCK decisions.
Supports ablation testing by toggling individual security layers.
Preserves existing security architecture:
1. Ingestion security (Secret redaction, Presidio PII masking, Prompt Guard quarantine).
2. Query security (Llama Prompt Guard 2 86M).
3. Access control & authorization (RBAC).
4. Retrieved-context security (untrusted delimiters & instruction prefix stripping).
5. Output security scanning (secret leak interception).
"""

from enum import Enum
from typing import Any
import logging
from pydantic import BaseModel, Field

from guardrails.secret_detector import SecretDetector
from guardrails.pii_masker import PIIMasker
from guardrails.prompt_injection import PromptInjectionDetector, InjectionDetectionResult
from guardrails.access_control import AccessControlEngine, UserRole, DataSensitivity, AuthorizationResult
from guardrails.context_sanitizer import ContextSanitizer

logger = logging.getLogger(__name__)


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    REDACT = "REDACT"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class IngestionDecisionResult(BaseModel):
    decision: PolicyDecision
    processed_text: str
    reasons: list[str] = Field(default_factory=list)
    secrets_count: int = 0
    pii_count: int = 0
    is_injection_quarantined: bool = False
    sensitivity_tier: DataSensitivity = DataSensitivity.INTERNAL


class QueryDecisionResult(BaseModel):
    decision: PolicyDecision
    reason: str
    authorization: AuthorizationResult
    injection_result: InjectionDetectionResult


class OutputDecisionResult(BaseModel):
    decision: PolicyDecision
    sanitized_output: str
    reasons: list[str] = Field(default_factory=list)
    secrets_found: int = 0


class PolicyEngine:
    """Coordinates security decisions across all RAG pipeline stages with ablation support."""

    def __init__(
        self,
        enable_ingestion_security: bool = True,
        enable_query_security: bool = True,
        enable_access_control: bool = True,
        enable_context_sanitization: bool = True,
        enable_output_security: bool = True,
    ):
        # Ablation Flags
        self.enable_ingestion_security = enable_ingestion_security
        self.enable_query_security = enable_query_security
        self.enable_access_control = enable_access_control
        self.enable_context_sanitization = enable_context_sanitization
        self.enable_output_security = enable_output_security

        # Sub-guardrails
        self.secret_detector = SecretDetector()
        self.pii_masker = PIIMasker()
        self.injection_detector = PromptInjectionDetector()
        self.access_control = AccessControlEngine()
        self.context_sanitizer = ContextSanitizer(secret_detector=self.secret_detector)

    def evaluate_ingestion(self, raw_text: str, document_name: str) -> IngestionDecisionResult:
        """
        Evaluate and process document text chunk before embedding and storage.
        Masks secrets, anonymizes PII, and quarantines prompt injection payloads.
        """
        if not self.enable_ingestion_security:
            return IngestionDecisionResult(
                decision=PolicyDecision.ALLOW,
                processed_text=raw_text,
                reasons=["Ingestion security disabled (ablation mode)."],
            )

        reasons = []
        text = raw_text
        decision = PolicyDecision.ALLOW
        quarantined = False

        # 1. Prompt Injection Scanning via Llama Prompt Guard 2 86M (Quarantine check)
        inj_res = self.injection_detector.detect(text)
        if inj_res.is_injection:
            quarantined = True
            decision = PolicyDecision.QUARANTINE
            reasons.append(f"Prompt injection detected in document: {inj_res.explanation}")
            text = f"[QUARANTINED ADVERSARIAL CONTENT: {inj_res.explanation}]\n" + text.replace("ignore", "[neutralized]")

        # 2. Secret Detection & Redaction (Regex + Shannon Entropy)
        sanitized_sec, sec_matches = self.secret_detector.redact(text)
        sec_count = len(sec_matches)
        if sec_count > 0:
            text = sanitized_sec
            if decision != PolicyDecision.QUARANTINE:
                decision = PolicyDecision.REDACT
            reasons.append(f"Redacted {sec_count} secret(s) or API credential(s).")

        # 3. PII Detection & Masking (Presidio)
        sanitized_pii, pii_matches = self.pii_masker.anonymize(text)
        pii_count = len(pii_matches)
        if pii_count > 0:
            text = sanitized_pii
            if decision != PolicyDecision.QUARANTINE:
                decision = PolicyDecision.REDACT
            reasons.append(f"Masked {pii_count} PII entity/entities.")

        sensitivity = DataSensitivity.INTERNAL

        return IngestionDecisionResult(
            decision=decision,
            processed_text=text,
            reasons=reasons,
            secrets_count=sec_count,
            pii_count=pii_count,
            is_injection_quarantined=quarantined,
            sensitivity_tier=sensitivity,
        )

    def evaluate_query(
        self,
        query: str,
        user_role: UserRole = UserRole.RESEARCHER,
        target_sensitivity: DataSensitivity = DataSensitivity.INTERNAL,
    ) -> QueryDecisionResult:
        """
        Evaluate incoming user query: Authorization and Prompt Injection.
        Keeps authorization and safety decisions strictly decoupled.
        """
        # Default passes
        auth_res = AuthorizationResult(
            is_authorized=True,
            user_role=user_role,
            required_clearance=target_sensitivity,
            reason="Access control bypassed.",
        )
        inj_res = InjectionDetectionResult(
            is_injection=False, confidence_score=0.0, trigger_type="clean", explanation="Bypassed"
        )

        # 1. Authorization Check (RBAC)
        if self.enable_access_control:
            auth_res = self.access_control.check_access(user_role, target_sensitivity)
            if not auth_res.is_authorized:
                return QueryDecisionResult(
                    decision=PolicyDecision.BLOCK,
                    reason=auth_res.reason,
                    authorization=auth_res,
                    injection_result=inj_res,
                )

        # 2. Query Prompt Injection Check (Llama Prompt Guard 2 86M)
        if self.enable_query_security:
            inj_res = self.injection_detector.detect(query)
            if inj_res.is_injection:
                return QueryDecisionResult(
                    decision=PolicyDecision.BLOCK,
                    reason=f"Blocked: Query contains prompt injection attack ({inj_res.explanation}).",
                    authorization=auth_res,
                    injection_result=inj_res,
                )

        return QueryDecisionResult(
            decision=PolicyDecision.ALLOW,
            reason="Query validated successfully through input security layers.",
            authorization=auth_res,
            injection_result=inj_res,
        )

    def evaluate_output(self, raw_llm_output: str) -> OutputDecisionResult:
        """
        Scan and sanitize LLM output before presentation to user.
        Validates that no secret leakage occurred.
        """
        if not self.enable_output_security:
            return OutputDecisionResult(
                decision=PolicyDecision.ALLOW,
                sanitized_output=raw_llm_output,
                reasons=["Output security disabled (ablation mode)."],
            )

        reasons = []
        text = raw_llm_output

        # Check for Secret Leakage in Output
        sanitized_sec, sec_matches = self.secret_detector.redact(text)
        sec_count = len(sec_matches)
        if sec_count > 0:
            text = sanitized_sec
            reasons.append(f"Intercepted and redacted {sec_count} secret(s) from LLM output.")

        decision = PolicyDecision.REDACT if sec_count > 0 else PolicyDecision.ALLOW
        return OutputDecisionResult(
            decision=decision,
            sanitized_output=text,
            reasons=reasons,
            secrets_found=sec_count,
        )
