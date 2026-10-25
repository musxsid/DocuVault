"""
DocuVault — Multi-Tenant Authentication & Tier Management Package
Provides Keycloak OIDC, local PBKDF2 authentication fallback, session caching,
and Free vs. Pro subscription access enforcement.
"""

from auth.tier_manager import TierManager, UserTier, require_pro
from auth.session_manager import SessionManager
from auth.local_auth import LocalAuthManager
from auth.keycloak_client import KeycloakClient

__all__ = [
    "TierManager",
    "UserTier",
    "require_pro",
    "SessionManager",
    "LocalAuthManager",
    "KeycloakClient",
]
