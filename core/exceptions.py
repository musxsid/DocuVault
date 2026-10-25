"""
DocuVaultAI — Custom Exception Hierarchy (Unit 1: OOP & Custom Exceptions)
Provides domain-specific exceptions with structured error codes, timestamps,
and contextual debugging payloads.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class DocuVaultError(Exception):
    """Base exception for all DocuVault domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_GENERIC",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code
        self.timestamp: str = datetime.now().isoformat()
        self.context: Dict[str, Any] = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses and logs."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
            "context": self.context,
        }

    def __str__(self) -> str:
        ctx_str = f" | Context: {self.context}" if self.context else ""
        return f"[{self.error_code}] {self.message}{ctx_str}"


class CorruptFileError(DocuVaultError):
    """Raised when binary magic byte inspection fails or file is damaged."""

    def __init__(
        self,
        filepath: str,
        expected_format: str,
        found_magic: Optional[bytes] = None,
        reason: str = "Magic byte signature mismatch",
    ) -> None:
        context = {
            "filepath": filepath,
            "expected_format": expected_format,
            "found_magic": found_magic.hex() if found_magic else None,
            "reason": reason,
        }
        msg = f"Corrupt or disguised file detected at '{filepath}'. Expected {expected_format}, found {context['found_magic']}."
        super().__init__(msg, error_code="ERR_CORRUPT_FILE", context=context)


class TamperedFileError(DocuVaultError):
    """Raised when SHA-256 cryptographic checksum does not match expected integrity hash."""

    def __init__(
        self,
        filepath: str,
        expected_hash: str,
        actual_hash: str,
    ) -> None:
        context = {
            "filepath": filepath,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
        }
        msg = (
            f"Cryptographic integrity check failed for '{filepath}'! "
            f"Expected SHA-256: {expected_hash}, Actual: {actual_hash}."
        )
        super().__init__(msg, error_code="ERR_TAMPERED_INTEGRITY", context=context)


class MissingClauseError(DocuVaultError):
    """Raised when mandatory legal compliance clauses fail regex verification."""

    def __init__(
        self,
        document_id: str,
        missing_clauses: List[str],
        jurisdiction: Optional[str] = None,
    ) -> None:
        context = {
            "document_id": document_id,
            "missing_clauses": missing_clauses,
            "jurisdiction": jurisdiction or "Unspecified",
        }
        clauses_str = ", ".join(f"'{c}'" for c in missing_clauses)
        msg = f"Document '{document_id}' is missing required legal compliance clauses: {clauses_str}."
        super().__init__(msg, error_code="ERR_MISSING_CLAUSE", context=context)
        self.missing_clauses = missing_clauses


class InvalidFormError(DocuVaultError):
    """Raised when regex form validation fails for dates, currency amounts, or entities."""

    def __init__(
        self,
        field_name: str,
        invalid_value: Any,
        expected_pattern: str,
    ) -> None:
        context = {
            "field_name": field_name,
            "invalid_value": str(invalid_value),
            "expected_pattern": expected_pattern,
        }
        msg = f"Form field validation failed for '{field_name}'='{invalid_value}'. Must match: {expected_pattern}"
        super().__init__(msg, error_code="ERR_INVALID_FORM", context=context)


class StorageProviderError(DocuVaultError):
    """Base exception for storage provider abstraction failures."""

    def __init__(
        self,
        provider_name: str,
        operation: str,
        details: str,
        error_code: str = "ERR_STORAGE_FAIL",
    ) -> None:
        context = {
            "provider": provider_name,
            "operation": operation,
            "details": details,
        }
        msg = f"Storage provider '{provider_name}' failed during '{operation}': {details}"
        super().__init__(msg, error_code=error_code, context=context)


class StorageReadError(StorageProviderError):
    """Raised when file reading fails in local or cloud storage."""

    def __init__(self, provider_name: str, path: str, details: str) -> None:
        super().__init__(
            provider_name,
            operation=f"read({path})",
            details=details,
            error_code="ERR_STORAGE_READ",
        )


class StorageWriteError(StorageProviderError):
    """Raised when file writing fails in local or cloud storage."""

    def __init__(self, provider_name: str, path: str, details: str) -> None:
        super().__init__(
            provider_name,
            operation=f"write({path})",
            details=details,
            error_code="ERR_STORAGE_WRITE",
        )


class NetworkSyncError(StorageProviderError):
    """Raised when cloud storage synchronization encounters network timeouts or TLS errors."""

    def __init__(self, endpoint: str, status_code: Optional[int], reason: str) -> None:
        super().__init__(
            provider_name="CloudStorageProvider",
            operation=f"sync({endpoint})",
            details=f"Status: {status_code} - {reason}",
            error_code="ERR_NETWORK_SYNC",
        )


class UnsupportedFormatError(DocuVaultError):
    """Raised when an unhandled file extension or MIME type is ingested."""

    def __init__(self, filepath: str, detected_extension: str) -> None:
        context = {"filepath": filepath, "extension": detected_extension}
        msg = f"Unsupported document format '{detected_extension}' for file '{filepath}'."
        super().__init__(msg, error_code="ERR_UNSUPPORTED_FORMAT", context=context)


class ParsingError(DocuVaultError):
    """Raised when content extraction fails during parsing."""

    def __init__(self, parser_name: str, filepath: str, reason: str) -> None:
        context = {"parser": parser_name, "filepath": filepath, "reason": reason}
        msg = f"Parser '{parser_name}' failed to process '{filepath}': {reason}"
        super().__init__(msg, error_code="ERR_PARSER_FAILURE", context=context)


class CalendarAPIError(DocuVaultError):
    """Raised when the working-day calculation cannot reach the calendar service."""

    def __init__(self, country_code: str, year: int, reason: str) -> None:
        context = {"country_code": country_code, "year": year, "reason": reason}
        msg = f"Public holiday API call failed for {country_code}/{year}: {reason}"
        super().__init__(msg, error_code="ERR_CALENDAR_API", context=context)


class VectorIndexError(DocuVaultError):
    """Raised when TF-IDF vector matrix construction or query retrieval fails."""

    def __init__(self, reason: str, dimension_info: Optional[Dict[str, Any]] = None) -> None:
        context = dimension_info or {}
        msg = f"Vector search engine error: {reason}"
        super().__init__(msg, error_code="ERR_VECTOR_INDEX", context=context)


class TierLimitExceededError(DocuVaultError):
    """Raised when a user on Free Trial exceeds allowed usage quotas (e.g. max 5 documents, max 10 chats)."""

    def __init__(
        self,
        resource_name: str,
        current_count: int,
        limit: int,
        tier: str = "Free",
        suggestion: str = "Upgrade to Pro Plan for unlimited document indexing and AI queries.",
    ) -> None:
        context = {
            "resource": resource_name,
            "current_count": current_count,
            "limit": limit,
            "tier": tier,
            "suggestion": suggestion,
        }
        msg = (
            f"Subscription Tier Limit Reached ({tier} Plan): {current_count}/{limit} {resource_name} utilized. "
            f"{suggestion}"
        )
        super().__init__(msg, error_code="ERR_TIER_LIMIT_EXCEEDED", context=context)
        self.resource_name = resource_name
        self.current_count = current_count
        self.limit = limit
        self.tier = tier
        self.suggestion = suggestion


class FeatureLockedError(DocuVaultError):
    """Raised when an attempt is made to access a Pro-exclusive feature from a Free plan."""

    def __init__(
        self,
        feature_name: str,
        required_tier: str = "Pro",
        current_tier: str = "Free",
    ) -> None:
        suggestion = f"Upgrade to {required_tier} Plan to unlock {feature_name}."
        context = {
            "feature": feature_name,
            "required_tier": required_tier,
            "current_tier": current_tier,
            "suggestion": suggestion,
        }
        msg = f"Feature '{feature_name}' is locked. Requires {required_tier} Plan (Current: {current_tier}). {suggestion}"
        super().__init__(msg, error_code="ERR_FEATURE_LOCKED", context=context)
        self.feature_name = feature_name
        self.required_tier = required_tier
        self.current_tier = current_tier
        self.tier = current_tier
        self.suggestion = suggestion


class AuthenticationError(DocuVaultError):
    """Raised when user credential validation, Keycloak OIDC, or token refresh fails."""

    def __init__(self, reason: str, username_or_email: Optional[str] = None) -> None:
        context = {"user": username_or_email} if username_or_email else {}
        msg = f"Authentication failed: {reason}"
        super().__init__(msg, error_code="ERR_AUTH_FAILED", context=context)
        self.username_or_email = username_or_email

