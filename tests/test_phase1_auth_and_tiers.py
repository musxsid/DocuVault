"""
DocuVault — Unit Tests for Phase 1: Authentication, Subscription Tiers, & Exceptions
Validates TierManager quotas, session caching, PBKDF2 local hashing, and exceptions.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Setup project root import
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from auth.tier_manager import TierManager, UserTier, require_pro
from auth.session_manager import SessionManager
from auth.local_auth import LocalAuthManager
from auth.keycloak_client import KeycloakClient
from core.exceptions import (
    AuthenticationError,
    FeatureLockedError,
    TierLimitExceededError,
)


class TestTierManager(unittest.TestCase):
    """Validates subscription tier limits and @require_pro decorator."""

    def test_free_tier_document_limit(self):
        # 5 documents max on Free tier
        self.assertTrue(TierManager.check_document_limit("Free", 0))
        self.assertTrue(TierManager.check_document_limit("Free", 4))
        with self.assertRaises(TierLimitExceededError) as ctx:
            TierManager.check_document_limit("Free", 5)
        self.assertEqual(ctx.exception.current_count, 5)
        self.assertEqual(ctx.exception.limit, 5)

    def test_pro_tier_unlimited_documents(self):
        # Unlimited on Pro tier
        self.assertTrue(TierManager.check_document_limit("Pro", 5))
        self.assertTrue(TierManager.check_document_limit("Pro", 50000))

    def test_free_tier_chat_limit(self):
        # 10 queries max on Free tier
        self.assertTrue(TierManager.check_chat_limit("Free", 9))
        with self.assertRaises(TierLimitExceededError) as ctx:
            TierManager.check_chat_limit("Free", 10)
        self.assertEqual(ctx.exception.limit, 10)

    def test_pro_tier_unlimited_chat(self):
        self.assertTrue(TierManager.check_chat_limit("Pro", 100))

    def test_feature_gating_pro_features(self):
        # Free users are blocked from Pro features
        for feat in ["cloud_sync", "smart_diff", "pii_redaction", "calendar_export"]:
            self.assertFalse(TierManager.is_feature_unlocked("Free", feat))
            with self.assertRaises(FeatureLockedError):
                TierManager.check_feature_access("Free", feat)

            # Pro users have full access
            self.assertTrue(TierManager.is_feature_unlocked("Pro", feat))
            self.assertTrue(TierManager.check_feature_access("Pro", feat))

    def test_require_pro_decorator(self):
        class Service:
            def __init__(self, tier="Free"):
                self.user_tier = tier

            @require_pro("cloud_sync")
            def sync_to_cloud(self):
                return "SYNC_SUCCESS"

        free_svc = Service("Free")
        with self.assertRaises(FeatureLockedError):
            free_svc.sync_to_cloud()

        pro_svc = Service("Pro")
        self.assertEqual(pro_svc.sync_to_cloud(), "SYNC_SUCCESS")


class TestLocalAuth(unittest.TestCase):
    """Validates air-gapped local authentication with salted PBKDF2 hashing."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_users.db")
        self.auth = LocalAuthManager(db_path=self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_register_and_authenticate(self):
        user = self.auth.register_user(
            email="test@docuvault.io",
            password="secretpassword123",
            full_name="Test User",
            country="United States",
            tier="Free",
        )
        self.assertEqual(user["email"], "test@docuvault.io")
        self.assertEqual(user["tier"], "Free")

        # Authenticate valid
        authed = self.auth.authenticate_user("test@docuvault.io", "secretpassword123")
        self.assertIsNotNone(authed)
        self.assertEqual(authed["full_name"], "Test User")

        # Wrong password
        with self.assertRaises(AuthenticationError):
            self.auth.authenticate_user("test@docuvault.io", "wrong_password")

    def test_duplicate_registration_fails(self):
        self.auth.register_user("dupe@domain.com", "pass123", "First")
        with self.assertRaises(AuthenticationError):
            self.auth.register_user("dupe@domain.com", "pass123", "Second")

    def test_tier_upgrade(self):
        self.auth.register_user("upgrade@domain.com", "pass123", "Upgrade User", tier="Free")
        user_before = self.auth.get_user("upgrade@domain.com")
        self.assertEqual(user_before["tier"], "Free")

        self.auth.update_user_tier("upgrade@domain.com", "Pro")
        user_after = self.auth.get_user("upgrade@domain.com")
        self.assertEqual(user_after["tier"], "Pro")


class TestSessionManager(unittest.TestCase):
    """Validates credential persistence and onboarding flags."""

    def test_onboarding_flag(self):
        SessionManager.set_onboarding_completed(False)
        self.assertFalse(SessionManager.is_onboarding_completed())
        SessionManager.set_onboarding_completed(True)
        self.assertTrue(SessionManager.is_onboarding_completed())

    def test_save_and_load_session(self):
        user_info = {
            "email": "session.user@docuvault.io",
            "full_name": "Session User",
            "tier": "Pro",
            "country": "Germany",
        }
        SessionManager.save_session(user_info, token="jwt_test_token_123", remember_me=True)
        loaded = SessionManager.load_session()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["email"], "session.user@docuvault.io")
        self.assertEqual(loaded["tier"], "Pro")

        SessionManager.clear_session()
        cleared = SessionManager.load_session()
        self.assertIsNone(cleared)


class TestKeycloakClient(unittest.TestCase):
    """Validates Keycloak client and air-gapped offline fallback."""

    def setUp(self):
        self.kc = KeycloakClient()

    def test_offline_detection(self):
        # When local Keycloak server is not running, gracefully returns False without throwing
        self.assertIsInstance(self.kc.is_keycloak_available(), bool)

    def test_offline_registration_and_auth_fallback(self):
        # Should register in local store and authenticate
        import uuid
        test_email = f"kc_fallback_{uuid.uuid4().hex[:6]}@docuvault.io"
        user = self.kc.register_user(
            email=test_email,
            password="pass_kc_offline_123",
            full_name="KC Fallback User",
            country="France",
            tier="Free",
        )
        self.assertEqual(user["email"], test_email)

        # Authenticate via fallback
        authed = self.kc.authenticate_password(test_email, "pass_kc_offline_123")
        self.assertIsNotNone(authed)
        self.assertEqual(authed["full_name"], "KC Fallback User")
        self.assertEqual(authed["auth_source"], "local_sqlite_offline")

        # Bad password
        with self.assertRaises(AuthenticationError):
            self.kc.authenticate_password(test_email, "wrong_pass")


if __name__ == "__main__":
    unittest.main()
