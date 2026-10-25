"""
DocuVault — Tier Management & Subscription Access Control
Enforces two-tier subscription rules (Free Trial vs. Pro Plan) across desktop,
cloud web, and API layers using OOP guards and decorators.
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

from core.exceptions import FeatureLockedError, TierLimitExceededError


class UserTier(str, Enum):
    """Supported multi-tenant subscription tiers."""
    FREE = "Free"
    PRO = "Pro"

    @classmethod
    def from_str(cls, val: Optional[str]) -> "UserTier":
        if not val:
            return cls.FREE
        val_clean = str(val).strip().capitalize()
        if val_clean in ("Pro", "Professional", "Upgraded"):
            return cls.PRO
        return cls.FREE


class TierConfig:
    """Explicit quota and feature configuration per subscription tier."""

    LIMITS = {
        UserTier.FREE: {
            "name": "Free Trial Plan",
            "max_documents": 5,
            "max_chat_queries_per_session": 10,
            "cloud_sync_enabled": False,
            "smart_diff_enabled": False,
            "pii_redaction_enabled": False,
            "calendar_export_enabled": False,
            "vector_search_unlimited": False,
            "badge_label": "FREE TIER",
            "badge_color": "#6B7280",  # Gray
            "badge_bg": "#F3F4F6",
        },
        UserTier.PRO: {
            "name": "Pro / Upgraded Plan",
            "max_documents": float("inf"),
            "max_chat_queries_per_session": float("inf"),
            "cloud_sync_enabled": True,
            "smart_diff_enabled": True,
            "pii_redaction_enabled": True,
            "calendar_export_enabled": True,
            "vector_search_unlimited": True,
            "badge_label": "PRO PLAN",
            "badge_color": "#2563EB",  # Electric Blue
            "badge_bg": "rgba(37, 99, 235, 0.12)",
        },
    }

    @classmethod
    def get(cls, tier: UserTier) -> Dict[str, Any]:
        return cls.LIMITS.get(tier, cls.LIMITS[UserTier.FREE])


class TierManager:
    """
    Business logic and guardrails for verifying tier quotas and gated features.
    Thread-safe and decoupled for use across PyQt6, Flask, and Streamlit.
    """

    @classmethod
    def check_document_limit(cls, user_tier: str, current_doc_count: int) -> bool:
        """
        Validates if user can ingest an additional document.
        Raises TierLimitExceededError if limit is reached on Free Trial.
        """
        tier = UserTier.from_str(user_tier)
        cfg = TierConfig.get(tier)
        max_docs = cfg["max_documents"]

        if current_doc_count >= max_docs:
            raise TierLimitExceededError(
                resource_name="documents",
                current_count=current_doc_count,
                limit=int(max_docs),
                tier=tier.value,
                suggestion="Upgrade to Pro Plan for unlimited document indexing and cloud sync.",
            )
        return True

    @classmethod
    def check_chat_limit(cls, user_tier: str, session_chat_count: int) -> bool:
        """
        Validates if user can submit another RAG chat query in the current session.
        Raises TierLimitExceededError if 10-query limit reached on Free Trial.
        """
        tier = UserTier.from_str(user_tier)
        cfg = TierConfig.get(tier)
        max_chats = cfg["max_chat_queries_per_session"]

        if session_chat_count >= max_chats:
            raise TierLimitExceededError(
                resource_name="AI chat queries",
                current_count=session_chat_count,
                limit=int(max_chats),
                tier=tier.value,
                suggestion="Upgrade to Pro Plan for unlimited AI document queries with citations.",
            )
        return True

    @classmethod
    def check_feature_access(cls, user_tier: str, feature_key: str) -> bool:
        """
        Validates access to Pro-exclusive features.
        Raises FeatureLockedError if feature is not enabled for the user's tier.
        """
        tier = UserTier.from_str(user_tier)
        cfg = TierConfig.get(tier)

        feature_map = {
            "cloud_sync": "cloud_sync_enabled",
            "smart_diff": "smart_diff_enabled",
            "pii_redaction": "pii_redaction_enabled",
            "calendar_export": "calendar_export_enabled",
        }
        cfg_key = feature_map.get(feature_key, f"{feature_key}_enabled")
        is_allowed = cfg.get(cfg_key, False)

        if not is_allowed:
            feature_display_names = {
                "cloud_sync": "Cloud Storage Federation",
                "smart_diff": "Contract Amendment Smart Diff",
                "pii_redaction": "Automated PII Redaction",
                "calendar_export": "Google / iCal (.ics) Calendar Export",
            }
            display_name = feature_display_names.get(feature_key, feature_key.replace("_", " ").title())
            raise FeatureLockedError(
                feature_name=display_name,
                required_tier=UserTier.PRO.value,
                current_tier=tier.value,
            )
        return True

    @classmethod
    def is_feature_unlocked(cls, user_tier: str, feature_key: str) -> bool:
        """Non-raising boolean check for UI visibility and badges."""
        try:
            return cls.check_feature_access(user_tier, feature_key)
        except FeatureLockedError:
            return False

    @classmethod
    def can_access_feature(cls, user_tier: str, feature_key: str) -> bool:
        """Alias for is_feature_unlocked for readable capability checks."""
        return cls.is_feature_unlocked(user_tier, feature_key)

    @classmethod
    def get_tier_badge_info(cls, user_tier: str) -> Dict[str, str]:
        """Returns visual styling information for rendering user tier badges."""
        tier = UserTier.from_str(user_tier)
        cfg = TierConfig.get(tier)
        return {
            "label": cfg["badge_label"],
            "color": cfg["badge_color"],
            "bg": cfg["badge_bg"],
            "tier": tier.value,
            "name": cfg["name"],
        }


def require_pro(feature_name: str):
    """
    Decorator for Python methods/functions requiring Pro tier.
    Inspects self.user_tier, kwargs['user_tier'], or session object.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Attempt to extract user tier from arguments or caller instance
            user_tier = "Free"
            if args and hasattr(args[0], "user_tier"):
                user_tier = getattr(args[0], "user_tier")
            elif args and hasattr(args[0], "current_user") and isinstance(getattr(args[0], "current_user"), dict):
                user_tier = getattr(args[0], "current_user").get("tier", "Free")
            elif "user_tier" in kwargs:
                user_tier = kwargs["user_tier"]
            elif "current_user" in kwargs and isinstance(kwargs["current_user"], dict):
                user_tier = kwargs["current_user"].get("tier", "Free")

            TierManager.check_feature_access(user_tier, feature_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator
