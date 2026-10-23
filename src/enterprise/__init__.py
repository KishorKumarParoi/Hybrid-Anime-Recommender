"""
Enterprise AI Platform Architecture Suite
=========================================
Principal-grade modules implementing:
- Prompt & Policy Guardrails (PII Anonymization, Prompt Injection Defense, Canary Tokens)
- Evaluation Harness (G-Eval style LLM-as-a-judge, Rubrics, Cost/Latency Dashboards)
- Production-Grade RAG Service (Hybrid Search, Reciprocal Rank Fusion, A/B Testing)
- Architectural Patterns (Transactional Outbox, Exactly-Once Semantics, CQRS & Saga)
- Lakehouse & Feature Freshness SLA Engine (Delta / Apache Iceberg, Feature Freshness)
- Security & Multi-Tenant Governance (KMS Envelope Encryption, Tamper-Evident Audit Trails)
"""

from src.enterprise.guardrails import (
    PIIFilterVault,
    PromptInjectionGuard,
    SafetyGuardrailResult,
    apply_enterprise_guardrails,
)
from src.enterprise.eval_harness import (
    GEvalRubric,
    GEvalHarness,
    EvaluationResult,
    OfflineEvalDataset,
)
from src.enterprise.rag_service import (
    ProductionRAGService,
    HybridSearchResult,
    ABTestRouter,
    CostTracker,
)
from src.enterprise.patterns import (
    IdempotencyManager,
    TransactionalOutbox,
    SagaOrchestrator,
    SagaStep,
    SagaStatus,
)
from src.enterprise.lakehouse import (
    LakehouseManager,
    TableFormat,
    FeatureFreshnessSLA,
)
from src.enterprise.security import (
    TenantSecurityContext,
    KMSEnvelopeEncryption,
    AuditTrailLogger,
)

__all__ = [
    "PIIFilterVault",
    "PromptInjectionGuard",
    "SafetyGuardrailResult",
    "apply_enterprise_guardrails",
    "GEvalRubric",
    "GEvalHarness",
    "EvaluationResult",
    "OfflineEvalDataset",
    "ProductionRAGService",
    "HybridSearchResult",
    "ABTestRouter",
    "CostTracker",
    "IdempotencyManager",
    "TransactionalOutbox",
    "SagaOrchestrator",
    "SagaStep",
    "SagaStatus",
    "LakehouseManager",
    "TableFormat",
    "FeatureFreshnessSLA",
    "TenantSecurityContext",
    "KMSEnvelopeEncryption",
    "AuditTrailLogger",
]
