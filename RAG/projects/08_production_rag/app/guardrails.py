"""Input/output guardrails (doc 11).

Lightweight, dependency-free checks so you understand the mechanics. In production you'd
use dedicated models/services, but the *categories* are exactly these.
"""
from __future__ import annotations

import re

# Phrases that often signal prompt-injection hidden in a query or a retrieved document.
_INJECTION_PATTERNS = [
    r"ignore (all|the|your|previous) (instructions|rules|context)",
    r"disregard (the|all|previous) (above|instructions)",
    r"you are now",
    r"reveal (your|the) (system )?prompt",
    r"act as (an? )?(dan|jailbreak)",
]

_PII_PATTERNS = {
    "email": r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


def detect_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _INJECTION_PATTERNS)


def redact_pii(text: str) -> tuple[str, list[str]]:
    found = []
    out = text
    for label, pat in _PII_PATTERNS.items():
        if re.search(pat, out):
            found.append(label)
            out = re.sub(pat, f"[REDACTED_{label.upper()}]", out)
    return out, found


def check_input(query: str) -> dict:
    """Return {'allowed': bool, 'reason': str}."""
    if not query.strip():
        return {"allowed": False, "reason": "empty query"}
    if len(query) > 4000:
        return {"allowed": False, "reason": "query too long"}
    if detect_injection(query):
        return {"allowed": False, "reason": "possible prompt injection"}
    return {"allowed": True, "reason": ""}
