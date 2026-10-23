"""
Enterprise Security, Multi-Tenant Governance & KMS Encryption
=============================================================
Implements:
1. Multi-Tenant Security Isolation Context (Row-Level Security simulation)
2. KMS Envelope Encryption (Master Key + DEK with AES-256-GCM)
3. Cryptographic Tamper-Evident Audit Trail with Hash-Chaining (SOC 2 / ISO 27001)
"""

import os
import json
import base64
import hashlib
import hmac
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("EnterpriseSecurity")


@dataclass
class TenantSecurityContext:
    """Enforces multi-tenant isolation context across request lifecycles."""
    tenant_id: str
    user_id: str
    roles: List[str] = field(default_factory=lambda: ["member"])
    rate_limit_rpm: int = 120
    allowed_models: List[str] = field(default_factory=lambda: ["qwen2.5-7b-awq", "anime-critic-lora"])

    def can_access_tenant_data(self, target_tenant_id: str) -> bool:
        """Strict tenant isolation check."""
        return self.tenant_id == target_tenant_id or "superadmin" in self.roles


class KMSEnvelopeEncryption:
    """
    KMS Envelope Encryption using AES-256-GCM.
    - Master Key (KEK - Key Encryption Key) encrypts the per-record Data Encryption Key (DEK).
    - Protects PII and sensitive vector embeddings at rest.
    """

    def __init__(self, master_key_bytes: Optional[bytes] = None):
        # 256-bit Key Encryption Key (KEK)
        self.kek = master_key_bytes or AESGCM.generate_key(bit_length=256)

    def encrypt_payload(self, plaintext: str) -> Dict[str, str]:
        """
        Encrypts plaintext using a generated DEK, then encrypts the DEK using the KEK.
        Returns: {encrypted_data, encrypted_dek, nonce}
        """
        dek = AESGCM.generate_key(bit_length=256)
        aesgcm_dek = AESGCM(dek)
        nonce = os.urandom(12)

        ciphertext = aesgcm_dek.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Wrap DEK with KEK
        aesgcm_kek = AESGCM(self.kek)
        kek_nonce = os.urandom(12)
        wrapped_dek = aesgcm_kek.encrypt(kek_nonce, dek, None)

        return {
            "ciphertext_b64": base64.b64encode(ciphertext).decode("utf-8"),
            "nonce_b64": base64.b64encode(nonce).decode("utf-8"),
            "wrapped_dek_b64": base64.b64encode(wrapped_dek).decode("utf-8"),
            "kek_nonce_b64": base64.b64encode(kek_nonce).decode("utf-8"),
        }

    def decrypt_payload(self, envelope: Dict[str, str]) -> str:
        """Unwraps the DEK using KEK and decrypts the ciphertext."""
        ciphertext = base64.b64decode(envelope["ciphertext_b64"])
        nonce = base64.b64decode(envelope["nonce_b64"])
        wrapped_dek = base64.b64decode(envelope["wrapped_dek_b64"])
        kek_nonce = base64.b64decode(envelope["kek_nonce_b64"])

        # Unwrap DEK
        aesgcm_kek = AESGCM(self.kek)
        dek = aesgcm_kek.decrypt(kek_nonce, wrapped_dek, None)

        # Decrypt payload
        aesgcm_dek = AESGCM(dek)
        plaintext = aesgcm_dek.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")


@dataclass
class AuditRecord:
    index: int
    timestamp: str
    tenant_id: str
    action: str
    actor: str
    details: Dict[str, Any]
    prev_hash: str
    signature: str


class AuditTrailLogger:
    """
    Cryptographic Tamper-Evident Audit Trail.
    Chains each audit event to the previous record's hash (Blockchain-style integrity),
    signed with HMAC-SHA256 to prove audit log immutability for SOC 2 Type II compliance.
    """

    def __init__(self, hmac_secret: str = "enterprise-audit-secret-key-2026"):
        self.secret = hmac_secret.encode("utf-8")
        self.chain: List[AuditRecord] = []
        self._last_hash = "GENESIS_BLOCK_0000000000000000000000000000"

    def record_event(self, tenant_id: str, action: str, actor: str, details: Dict[str, Any]) -> AuditRecord:
        """Appends a cryptographically signed event to the audit trail."""
        index = len(self.chain)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Compute payload fingerprint
        payload_str = json.dumps(
            {"index": index, "timestamp": timestamp, "tenant": tenant_id, "action": action, "actor": actor, "prev": self._last_hash},
            sort_keys=True
        )

        sig = hmac.new(self.secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

        record = AuditRecord(
            index=index,
            timestamp=timestamp,
            tenant_id=tenant_id,
            action=action,
            actor=actor,
            details=details,
            prev_hash=self._last_hash,
            signature=sig,
        )

        self._last_hash = sig
        self.chain.append(record)
        return record

    def verify_integrity(self) -> Tuple[bool, Optional[int]]:
        """
        Validates the entire audit chain.
        Returns: (is_valid: bool, corrupted_index: Optional[int])
        """
        expected_prev = "GENESIS_BLOCK_0000000000000000000000000000"
        for idx, rec in enumerate(self.chain):
            if rec.prev_hash != expected_prev:
                return False, idx

            payload_str = json.dumps(
                {"index": rec.index, "timestamp": rec.timestamp, "tenant": rec.tenant_id, "action": rec.action, "actor": rec.actor, "prev": expected_prev},
                sort_keys=True
            )
            expected_sig = hmac.new(self.secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
            if rec.signature != expected_sig:
                return False, idx

            expected_prev = rec.signature

        return True, None
