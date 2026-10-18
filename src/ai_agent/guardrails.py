"""
AI Safety Guardrails & Adversarial Attack Shield for Hybrid Anime Recommender.
Inspired by enterprise Bedrock / PyRIT security standards.
"""

import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Prompt injection, jailbreak & adversarial manipulation patterns
ADVERSARIAL_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+|prior\s+)?(instructions|directions|prompts|rules|guidelines)",
    r"disregard\s+(all\s+)?(previous\s+|prior\s+)?(rules|guidelines|instructions)",
    r"(reveal|output|show|print|leak|dump)\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt|configuration|secret\s+keys|api\s+keys)",
    r"you\s+are\s+now\s+(in\s+)?(dan|developer|unrestricted|jailbreak)",
    r"bypass\s+(all\s+)?(safety|security|content)\s+(filters|policies|guardrails|checks)",
    r"pretend\s+you\s+have\s+no\s+.*?(rules|restrictions|filters)",
    r"system\s*:\s*you\s+are",
    r"<!--\s*system\s+prompt\s+injection",
    r"<script[\s\S]*?>[\s\S]*?<\/script>",
    r"javascript\s*:",
    r"__import__\s*\(",
    r"exec\s*\(",
    r"eval\s*\(",
    r"DROP\s+TABLE",
    r"SELECT\s+\*\s+FROM",
    r"\b(database\s+passwords|dump\s+passwords|leak\s+keys|dump\s+internal\s+keys|dump\s+all\s+user\s+session)\b",
    r"\b(authorized\s+security\s+researcher|emergency\s+penetration\s+test|approved\s+by\s+ciso|red\s+team\s+exercise)\b.*?\b(dump|bypass|leak|output|list)\b",
    r"\b(exploit|bypass|crack)\s+(drm|encryption|streaming\s+buffer|decryption\s+keys)\b",
    r"\b(give|provide)\s+(exact\s+)?(python\s+code\s+to\s+)?exploit\b",
    r"\b(bypass\s+drm|unauthorized\s+dumping|mechanisms\s+used\s+to\s+bypass)\b",
]


# Sensitive, illegal, and harmful content keywords
HARMFUL_PATTERNS = [
    r"\b(build|make|manufacture|create)\b.*?\b(bomb|explosive|weapon|poison)\b",
    r"\b(how\s+to\s+)?(commit\s+suicide|self-harm|cut\s+myself)\b",
    r"\b(synthesize|cook|sell|manufacture|make)\s+(meth|heroin|fentanyl|cocaine|illegal\s+substances|drugs)\b",
    r"\b(how\s+to\s+)?(hack\s+into|hack\s+a\s+bank|hack\s+internal\s+servers|steal\s+credit\s+card|ddos\s+attack)\b",
]


# PII Detection Patterns (Emails, Phone numbers, API keys)
PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL_REDACTED]"),
    (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]"),
    (r"\bgsk_[A-Za-z0-9]{40,64}\b", "[GROQ_API_KEY_REDACTED]"),
    (r"\bsk-[A-Za-z0-9]{32,64}\b", "[OPENAI_API_KEY_REDACTED]"),
    (r"\bghp_[A-Za-z0-9]{36}\b", "[GITHUB_TOKEN_REDACTED]"),
]


def anonymize_pii(text: str) -> str:
    """Anonymizes and redacts sensitive PII and API keys from text."""
    sanitized = text
    for pattern, replacement in PII_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized


def validate_input(query: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates user query against adversarial prompt attacks, length limits, and policy violations.
    
    Returns:
        (is_valid: bool, error_message: str, metadata: dict)
    """
    if not query or len(query.strip()) < 2:
        return False, "Query cannot be empty or under 2 characters.", {"reason": "too_short"}

    if len(query) > 1000:
        return False, "Query exceeds maximum allowed length of 1000 characters.", {"reason": "length_exceeded"}

    lowered = query.lower()

    # 1. Adversarial Prompt Injection & Jailbreak Check
    for pattern in ADVERSARIAL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            logger.warning(f"Guardrail intercepted prompt attack pattern: '{pattern}' in query")
            return (
                False,
                "Query blocked by AI Safety Guardrail: Adversarial prompt injection pattern detected.",
                {"reason": "prompt_injection", "flagged_pattern": pattern},
            )

    # 2. Harmful Content Policy Check
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            logger.warning(f"Guardrail intercepted harmful content pattern: '{pattern}'")
            return (
                False,
                "Query blocked by AI Safety Guardrail: Request violates content safety guidelines.",
                {"reason": "content_policy_violation", "flagged_pattern": pattern},
            )

    return True, "", {"status": "clean"}


def validate_output(response: str) -> Tuple[bool, str]:
    """
    Validates LLM-generated response before returning it to the client.
    Guarantees no internal prompts, keys, or forbidden phrases leak out.
    """
    if not response:
        return False, "Empty response generated."

    lowered = response.lower()
    leak_indicators = [
        "system prompt:",
        "my instructions are to",
        "api_key=",
        "api_key:",
        "gsk_",
        "sk-",
    ]

    for indicator in leak_indicators:
        if indicator in lowered:
            logger.critical(f"Output guardrail tripped! Potential secret leakage: '{indicator}'")
            return False, "Generated response was blocked by output safety guardrail."

    return True, ""
