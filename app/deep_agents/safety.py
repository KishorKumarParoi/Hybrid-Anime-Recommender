"""
Zero-Trust Content Safety & Policy Guardrail Node
Implements prompt injection defense, PII redaction, and domain scope enforcement.
"""
import re
import logging
from typing import Dict, Any, Tuple
from app.deep_agents.state import DeepAnimeAgentState

logger = logging.getLogger("SafetyGuardrail")

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(prior|previous)\s+guidelines",
    r"system\s*prompt",
    r"dan\s+mode",
    r"unrestricted\s+assistant",
    r"<script[\s\S]*?>[\s\S]*?<\/script>",
    r"__import__\(",
    r"build\s+(a\s+)?bomb",
    r"make\s+(a\s+)?weapon",
    r"bypass\s+content\s+filters",
    r"reveal\s+your\s+instructions",
]

PII_PATTERNS = [
    (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL_REDACTED]"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]"),
    (r"gsk_[a-zA-Z0-9]{20,}", "[GROQ_API_KEY_REDACTED]"),
    (r"sk-[a-zA-Z0-9]{20,}", "[API_KEY_REDACTED]"),
]


def redact_pii(text: str) -> Tuple[str, bool]:
    has_pii = False
    sanitized = text
    for pattern, replacement in PII_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            has_pii = True
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized, has_pii


def scan_prompt_safety(text: str) -> Tuple[bool, str, list]:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"🚨 [Safety Guardrail] Injection attack blocked pattern: '{pattern}' in '{text[:80]}'")
            return False, "Prompt violates security policy or contains adversarial injection patterns.", ["prompt_injection"]

    # Scope check: if user asks for non-anime destructive tasks
    lower = text.lower()
    destructive_keywords = ["ddos", "ransomware", "trojan", "sql injection", "exploit payload"]
    for kw in destructive_keywords:
        if kw in lower:
            return False, f"Request out of domain: destructive cyber term '{kw}' detected.", ["out_of_scope"]

    return True, "Clean", []


async def safety_guardrail_node(state: DeepAnimeAgentState) -> Dict[str, Any]:
    """
    Evaluates input query against zero-trust policy.
    Redacts PII and aborts cleanly if malicious.
    """
    raw_query = state.get("topic", "")
    sanitized_query, had_pii = redact_pii(raw_query)

    is_safe, reason, violations = scan_prompt_safety(sanitized_query)

    safety_audit = {
        "is_safe": is_safe,
        "reason": reason,
        "violation_types": violations,
        "pii_redacted": had_pii,
    }

    if not is_safe:
        return {
            "topic": sanitized_query,
            "safety_audit": safety_audit,
            "final_dossier": (
                "### 🛑 Security Advisory: Request Intercepted\n\n"
                f"**Policy Violation:** {reason}\n\n"
                "The Hybrid Anime Recommender Deep Agent Mesh enforces Zero-Trust AI Guardrails (NIST AI RMF / OWASP LLM-01). "
                "Adversarial prompts, system leaks, and malicious payloads are automatically quarantined."
            ),
            "loop_status": "REJECTED",
        }

    return {
        "topic": sanitized_query,
        "safety_audit": safety_audit,
    }
