"""
Central Policy Engine for Multi-Layer Guardrail RAG.
Makes explicit ALLOW, REDACT, QUARANTINE, and BLOCK decisions.
Supports ablation testing by toggling individual security layers.
"""

from enum import Enum
from typing import Any
import logging
from pydantic import BaseModel, Field

from guardrails.secret_detector import SecretDetector
from guardrails.pii_masker import PIIMasker
from guardrails.prompt_injection import PromptInjectionDetector, InjectionDetectionResult
from guardrails.harm_classifier import HarmClassifier, HarmClassificationResult
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
    reasons: list[str] = []
    secrets_count: int = 0
    pii_count: int = 0
    is_injection_quarantined: bool = False
    is_operational_harm: bool = False
    sensitivity_tier: DataSensitivity = DataSensitivity.INTERNAL


class QueryDecisionResult(BaseModel):
    decision: PolicyDecision
    reason: str
    authorization: AuthorizationResult
    injection_result: InjectionDetectionResult
    harm_result: HarmClassificationResult


class OutputDecisionResult(BaseModel):
    decision: PolicyDecision
    sanitized_output: str
    reasons: list[str] = []
    secrets_found: int = 0
    is_harmful: bool = False


class PolicyEngine:
    """
    Coordinates security decisions across all pipeline stages.
    Supports granular ablation controls to isolate individual layer impact.
    """

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
        self.harm_classifier = HarmClassifier()
        self.access_control = AccessControlEngine()
        self.context_sanitizer = ContextSanitizer(secret_detector=self.secret_detector)

    def evaluate_ingestion(self, raw_text: str, document_name: str) -> IngestionDecisionResult:
        """
        Evaluate and process document text chunk before embedding and storage.
        Preserves legitimate research while masking secrets and isolating injections.
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

        # 1. Prompt Injection Scanning (Quarantine check)
        inj_res = self.injection_detector.detect(text)
        if inj_res.is_injection:
            quarantined = True
            decision = PolicyDecision.QUARANTINE
            reasons.append(f"Prompt injection detected in document: {inj_res.explanation}")
            # Quarantine action: neutralize injection payloads so they cannot execute
            text = f"[QUARANTINED ADVERSARIAL CONTENT: {inj_res.explanation}]\n" + text.replace("ignore", "[neutralized]")

        # 2. Secret Detection & Redaction
        sanitized_sec, sec_matches = self.secret_detector.redact(text)
        sec_count = len(sec_matches)
        if sec_count > 0:
            text = sanitized_sec
            if decision != PolicyDecision.QUARANTINE:
                decision = PolicyDecision.REDACT
            reasons.append(f"Redacted {sec_count} secret(s) or API credential(s).")

        # 3. PII Detection & Masking
        sanitized_pii, pii_matches = self.pii_masker.anonymize(text)
        pii_count = len(pii_matches)
        if pii_count > 0:
            text = sanitized_pii
            if decision != PolicyDecision.QUARANTINE:
                decision = PolicyDecision.REDACT
            reasons.append(f"Masked {pii_count} PII entity/entities.")

        # 4. Harmful Operational Analysis (Preserve educational/research, flag operational hazard)
        harm_res = self.harm_classifier.classify(text)
        sensitivity = DataSensitivity.INTERNAL
        if harm_res.is_operational_harm:
            sensitivity = DataSensitivity.RESTRICTED
            reasons.append(f"Flagged operational hazard ({harm_res.category}). Stored as RESTRICTED.")
        elif harm_res.category != "safe":
            sensitivity = DataSensitivity.INTERNAL
            reasons.append(f"Research material tagged under '{harm_res.category}'. Stored safely.")

        return IngestionDecisionResult(
            decision=decision,
            processed_text=text,
            reasons=reasons,
            secrets_count=sec_count,
            pii_count=pii_count,
            is_injection_quarantined=quarantined,
            is_operational_harm=harm_res.is_operational_harm,
            sensitivity_tier=sensitivity,
        )

    def evaluate_query(
        self,
        query: str,
        user_role: UserRole = UserRole.RESEARCHER,
        target_sensitivity: DataSensitivity = DataSensitivity.INTERNAL,
    ) -> QueryDecisionResult:
        """
        Evaluate incoming user query: Authorization, Injection, and Harmfulness.
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
        harm_res = HarmClassificationResult(
            is_harmful=False, is_operational_harm=False, category="safe", confidence=1.0, explanation="Bypassed"
        )

        # 1. Authorization Check
        if self.enable_access_control:
            auth_res = self.access_control.check_access(user_role, target_sensitivity)
            if not auth_res.is_authorized:
                return QueryDecisionResult(
                    decision=PolicyDecision.BLOCK,
                    reason=auth_res.reason,
                    authorization=auth_res,
                    injection_result=inj_res,
                    harm_result=harm_res,
                )

        # 2. Query Prompt Injection Check
        if self.enable_query_security:
            inj_res = self.injection_detector.detect(query)
            if inj_res.is_injection:
                return QueryDecisionResult(
                    decision=PolicyDecision.BLOCK,
                    reason=f"Blocked: Query contains prompt injection attack ({inj_res.explanation}).",
                    authorization=auth_res,
                    injection_result=inj_res,
                    harm_result=harm_res,
                )

        # 3. Query Harm Check (Block actionable malicious requests)
        if self.enable_query_security:
            harm_res = self.harm_classifier.classify(query)
            if harm_res.is_operational_harm:
                return QueryDecisionResult(
                    decision=PolicyDecision.BLOCK,
                    reason=f"Blocked: Query solicits actionable operational harm ({harm_res.category}).",
                    authorization=auth_res,
                    injection_result=inj_res,
                    harm_result=harm_res,
                )

        return QueryDecisionResult(
            decision=PolicyDecision.ALLOW,
            reason="Query validated successfully through input security layers.",
            authorization=auth_res,
            injection_result=inj_res,
            harm_result=harm_res,
        )

    def evaluate_output(self, raw_llm_output: str) -> OutputDecisionResult:
        """
        Scan and sanitize LLM output before presentation to user.
        Validates no secret leakage or generated operational harm occurred.
        """
        if not self.enable_output_security:
            return OutputDecisionResult(
                decision=PolicyDecision.ALLOW,
                sanitized_output=raw_llm_output,
                reasons=["Output security disabled (ablation mode)."],
            )

        reasons = []
        text = raw_llm_output

        # 1. Check for Secret Leakage in Output
        sanitized_sec, sec_matches = self.secret_detector.redact(text)
        sec_count = len(sec_matches)
        if sec_count > 0:
            text = sanitized_sec
            reasons.append(f"Intercepted and redacted {sec_count} secret(s) from LLM output.")

        # 2. Check for Harmful Output Generation (Llama Guard / Heuristics)
        harm_res = self.harm_classifier.classify(text)
        if harm_res.is_operational_harm:
            return OutputDecisionResult(
                decision=PolicyDecision.BLOCK,
                sanitized_output="[BLOCKED: The system generated content violating safety policies regarding hazardous materials or weapons.]",
                reasons=[f"Output blocked due to operational harm ({harm_res.category})."],
                secrets_found=sec_count,
                is_harmful=True,
            )

        decision = PolicyDecision.REDACT if sec_count > 0 else PolicyDecision.ALLOW
        return OutputDecisionResult(
            decision=decision,
            sanitized_output=text,
            reasons=reasons,
            secrets_found=sec_count,
            is_harmful=False,
        )

