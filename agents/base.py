"""
Security helpers and an HMAC-SHA256 audit trail for the optional legacy agent subsystem.

The PHI pattern guard is a narrow pattern screen, not a HIPAA de-identification
implementation and not a guarantee that arbitrary text is free of PHI.
"""
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
]

class SecurityException(Exception):
    """Raised when the narrow outbound identifier screen detects a match."""

class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed configured safety bounds."""

def assert_no_phi(text: str) -> None:
    if not text:
        return
    value = str(text)
    for pattern in PHI_PATTERNS:
        if pattern.search(value):
            raise SecurityException("Identifier pattern detected by outbound guard: " + pattern.pattern)

class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def redact_phi(text: str) -> str:
        result = str(text)
        for pattern in PHI_PATTERNS:
            result = pattern.sub("[REDACTED_IDENTIFIER]", result)
        return result

class AuditTrail:
    """In-memory HMAC-SHA256 chained audit trail."""
    GENESIS = "GENESIS_BLOCK_0000000000000000"

    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            raise SecurityException("AUDIT_SECRET_KEY must be set before using the audit trail.")
        self.secret_key = resolved_key.encode("utf-8")
        self.logs: List[Dict[str, Any]] = []

    def _signature(self, audit_id: str, timestamp: str, actor: str, actor_tier: str, event_type: str, payload_hash: str, prev_hash: str) -> str:
        sign_string = f"{audit_id}|{timestamp}|{actor}|{actor_tier}|{event_type}|{payload_hash}|{prev_hash}"
        return hmac.new(self.secret_key, sign_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        payload_str = json.dumps(details, sort_keys=True, separators=(",", ":"))
        assert_no_phi(payload_str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        audit_id = f"AUDIT-{int(time.time() * 1000)}-{len(self.logs) + 1}"
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self.logs[-1]["current_hash"] if self.logs else self.GENESIS
        signature = self._signature(audit_id, timestamp, actor, actor_tier, event_type, payload_hash, prev_hash)
        entry = {"audit_id": audit_id, "timestamp": timestamp, "actor": actor, "actor_tier": actor_tier, "event_type": event_type, "payload_hash": payload_hash, "prev_hash": prev_hash, "current_hash": signature}
        self.logs.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        for index, entry in enumerate(self.logs):
            expected_prev = self.logs[index - 1]["current_hash"] if index > 0 else self.GENESIS
            if entry.get("prev_hash") != expected_prev:
                return False
            expected_signature = self._signature(entry["audit_id"], entry["timestamp"], entry["actor"], entry["actor_tier"], entry["event_type"], entry["payload_hash"], entry["prev_hash"])
            if not hmac.compare_digest(entry.get("current_hash", ""), expected_signature):
                return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return list(self.logs)

_GLOBAL_AUDIT: Optional[AuditTrail] = None

def _get_global_audit() -> AuditTrail:
    global _GLOBAL_AUDIT
    if _GLOBAL_AUDIT is None:
        _GLOBAL_AUDIT = AuditTrail()
    return _GLOBAL_AUDIT

class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return _get_global_audit().log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return _get_global_audit().get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return _get_global_audit().verify_integrity()

class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return result
