"""Deterministic cryptographic hashing and idempotency key computation."""
import hashlib
from typing import Optional


def compute_idempotency_key(
    learner_id: str,
    course_id: str,
    content_id: Optional[str],
    event_type: str,
    session_id: str,
    timestamp_utc: str,
) -> str:
    """Computes a stable deterministic SHA-256 idempotency key across source event fields."""
    content_part = content_id or ""
    raw = f"{learner_id}|{course_id}|{content_part}|{event_type}|{session_id}|{timestamp_utc}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
