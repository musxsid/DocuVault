"""
DocuVault — Regular Expression PII Redaction & Legal Compliance Engine
Identifies, sanitizes, and audits Personally Identifiable Information (PII)
including Social Security Numbers, Credit Cards, Email Addresses, and Phone Numbers.
"""

import re
from typing import Any, Dict, List, Tuple


class PIIRedactor:
    """
    Production regex-driven PII detector and sanitizer.
    Provides compliance masking for confidential legal, financial, and medical documents.
    """

    PATTERNS = {
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    }

    @classmethod
    def redact_text(cls, text: str, mask_char: str = "█") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Sanitizes text by replacing sensitive PII instances with masked blocks.
        Returns the sanitized string alongside an audit list of detected redactions.
        """
        if not text:
            return "", []

        sanitized = text
        detections: List[Dict[str, Any]] = []

        for pii_type, regex in cls.PATTERNS.items():
            for match in regex.finditer(text):
                val = match.group()
                masked_val = f"[{pii_type}: " + (mask_char * min(len(val), 8)) + "]"
                detections.append({
                    "type": pii_type,
                    "span": (match.start(), match.end()),
                    "length": len(val),
                })

            sanitized = regex.sub(lambda m: f"[{pii_type}: {mask_char * 6}]", sanitized)

        return sanitized, detections

    @classmethod
    def audit_pii(cls, text: str) -> Dict[str, int]:
        """Counts occurrences of each PII pattern in the given text."""
        counts = {}
        for pii_type, regex in cls.PATTERNS.items():
            counts[pii_type] = len(regex.findall(text))
        return counts
