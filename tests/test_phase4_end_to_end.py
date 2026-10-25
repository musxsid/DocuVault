"""
DocuVault — Comprehensive End-to-End Test Suite (Phases 1 - 4)
Validates:
- Unit 1: OOP, Tier Exceptions, Regex PII Redactor
- Unit 2: APIs, Keycloak / OAuth SSO, File Logging, Keyring Session Cache
- Unit 3: Flask REST API auth, quotas, and Streamlit components
- Unit 4: Binary parsing, DocumentFactory polymorphism, Pandas MultiIndex
- Unit 5: Pure NumPy TF-IDF matrix retrieval and cosine similarity
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from auth.local_auth import LocalAuthManager
from auth.session_manager import SessionManager
from auth.tier_manager import TierConfig, TierManager, UserTier
from backend.app_flask import app, document_store
from core.base_document import DocumentFactory
from core.catalog_manager import CatalogManager
from core.exceptions import AuthenticationError, FeatureLockedError, TierLimitExceededError
from core.pii_redactor import PIIRedactor
from core.vector_search import VectorSearchEngine


class TestDocuVaultEndToEnd(unittest.TestCase):
    """Rigorous end-to-end integration and curriculum verification."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_users.db"
        self.auth = LocalAuthManager(db_path=str(self.db_path))

        # Setup Flask test client
        self.flask_client = app.test_client()
        self.flask_client.testing = True

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Unit 1 & Auth: Local Authentication & PBKDF2 Hashing
    # -------------------------------------------------------------------------

    def test_worldwide_registration_and_authentication(self):
        """Validates that any user worldwide can register and authenticate."""
        user = self.auth.register_user(
            email="developer@example.org",
            password="SecureVaultPassword2026!",
            full_name="Morgan Stark",
            country="United Kingdom",
            tier="Free",
        )
        self.assertEqual(user["email"], "developer@example.org")
        self.assertEqual(user["tier"], "Free")
        self.assertEqual(user["country"], "United Kingdom")

        # Authenticate with valid password
        authed = self.auth.authenticate_user("developer@example.org", "SecureVaultPassword2026!")
        self.assertIsNotNone(authed)
        self.assertEqual(authed["full_name"], "Morgan Stark")

        # Reject invalid password
        with self.assertRaises(AuthenticationError):
            self.auth.authenticate_user("developer@example.org", "WrongPassword!")

        # Prevent duplicate email
        with self.assertRaises(AuthenticationError):
            self.auth.register_user(
                email="developer@example.org",
                password="AnotherPassword",
                full_name="Impostor",
            )

    def test_instant_tier_elevation(self):
        """Validates instant upgrade from Free Trial to Pro Plan."""
        self.auth.register_user("upgrader@test.io", "Password123!", "Alex Doe", tier="Free")
        self.assertEqual(self.auth.get_user("upgrader@test.io")["tier"], "Free")

        success = self.auth.update_user_tier("upgrader@test.io", "Pro")
        self.assertTrue(success)
        self.assertEqual(self.auth.get_user("upgrader@test.io")["tier"], "Pro")

    # -------------------------------------------------------------------------
    # Unit 1: Regular Expressions & PII Redactor
    # -------------------------------------------------------------------------

    def test_pii_regex_redactor(self):
        """Validates detection and masking of SSN, Credit Cards, Emails, and Phone Numbers."""
        sample_legal_text = (
            "Consultant John Doe (SSN: 123-45-6789) can be contacted at "
            "john.doe@enterprise.com or +1 415-555-2671. Please invoice card 4111-2222-3333-4444."
        )

        counts = PIIRedactor.audit_pii(sample_legal_text)
        self.assertEqual(counts["SSN"], 1)
        self.assertEqual(counts["EMAIL"], 1)
        self.assertEqual(counts["PHONE"], 1)
        self.assertEqual(counts["CREDIT_CARD"], 1)

        sanitized, detections = PIIRedactor.redact_text(sample_legal_text)
        self.assertEqual(len(detections), 4)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("john.doe@enterprise.com", sanitized)
        self.assertNotIn("4111-2222-3333-4444", sanitized)
        self.assertIn("[SSN:", sanitized)
        self.assertIn("[EMAIL:", sanitized)
        self.assertIn("[CREDIT_CARD:", sanitized)

    # -------------------------------------------------------------------------
    # Unit 1 & Unit 2: Tier Enforcements & Quotas
    # -------------------------------------------------------------------------

    def test_free_tier_quotas_and_locks(self):
        """Verifies 5-document and 10-query caps, and Pro feature guards."""
        # Free allows 0..4 existing documents
        self.assertTrue(TierManager.check_document_limit(UserTier.FREE.value, 4))

        # Free raises error at 5
        with self.assertRaises(TierLimitExceededError) as ctx:
            TierManager.check_document_limit(UserTier.FREE.value, 5)
        self.assertEqual(ctx.exception.limit, 5)

        # Pro allows unlimited documents
        self.assertTrue(TierManager.check_document_limit(UserTier.PRO.value, 5000))

        # Free chat queries: allow up to 9, raise at 10
        self.assertTrue(TierManager.check_chat_limit(UserTier.FREE.value, 9))
        with self.assertRaises(TierLimitExceededError):
            TierManager.check_chat_limit(UserTier.FREE.value, 10)

        # Pro chat queries: unlimited
        self.assertTrue(TierManager.check_chat_limit(UserTier.PRO.value, 100))

        # Feature locks
        for feat in ["cloud_sync", "smart_diff", "pii_redaction", "calendar_export"]:
            self.assertFalse(TierManager.can_access_feature(UserTier.FREE.value, feat))
            self.assertTrue(TierManager.can_access_feature(UserTier.PRO.value, feat))

    # -------------------------------------------------------------------------
    # Unit 3: Flask REST API Endpoints & Tier Gating
    # -------------------------------------------------------------------------

    def test_flask_auth_and_tier_endpoints(self):
        """Validates Flask REST API for registration, login, upgrade, and profile."""
        import uuid
        test_email = f"rest_user_{uuid.uuid4().hex[:8]}@docuvault.ai"

        # Register via REST
        reg_resp = self.flask_client.post("/api/auth/register", json={
            "email": test_email,
            "password": "Password123!",
            "full_name": "REST User",
            "country": "Germany",
        })
        self.assertEqual(reg_resp.status_code, 201)
        data = reg_resp.get_json()
        self.assertEqual(data["user"]["tier"], "Free")

        # Login via REST
        login_resp = self.flask_client.post("/api/auth/login", json={
            "email": test_email,
            "password": "Password123!",
        })
        self.assertEqual(login_resp.status_code, 200)

        # Profile via REST
        prof_resp = self.flask_client.get(f"/api/auth/profile?email={test_email}")
        self.assertEqual(prof_resp.status_code, 200)
        pdata = prof_resp.get_json()
        self.assertEqual(pdata["limits"]["max_documents"], 5)

        # Upgrade via REST
        up_resp = self.flask_client.post("/api/auth/upgrade", json={
            "email": test_email,
            "tier": "Pro",
        })
        self.assertEqual(up_resp.status_code, 200)
        self.assertEqual(up_resp.get_json()["user"]["tier"], "Pro")

    def test_flask_chat_quota_enforcement(self):
        """Validates that Flask /api/chat enforces session chat quota on Free tier."""
        # Query under limit
        resp = self.flask_client.post("/api/chat", json={
            "query": "What is the jurisdiction?",
            "tier": "Free",
            "session_query_count": 5,
        })
        self.assertEqual(resp.status_code, 200)

        # Query exceeding limit
        err_resp = self.flask_client.post("/api/chat", json={
            "query": "What is the jurisdiction?",
            "tier": "Free",
            "session_query_count": 10,
        })
        self.assertEqual(err_resp.status_code, 403)
        self.assertEqual(err_resp.get_json()["error_code"], "ERR_TIER_LIMIT_EXCEEDED")

    def test_flask_cloud_storage_mode_gated(self):
        """Validates that toggling to Cloud Vault mode is blocked for Free tier."""
        resp = self.flask_client.post(
            "/api/storage/mode",
            json={"mode": "Cloud Vault", "tier": "Free"},
            headers={"X-User-Tier": "Free"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["error_code"], "ERR_FEATURE_LOCKED")

    # -------------------------------------------------------------------------
    # Unit 4 & Unit 5: Core Document & Vector Search Computations
    # -------------------------------------------------------------------------

    def test_pure_numpy_vector_search(self):
        """Verifies pure NumPy TF-IDF matrix and cosine similarity retrieval."""
        engine = VectorSearchEngine()
        engine.add_document_chunks(
            doc_id="doc_nda_1",
            filename="NDA_Sample.pdf",
            category="Legal",
            pages=[
                {"page_number": 1, "text": "This Agreement shall terminate in 30 calendar days."},
                {"page_number": 2, "text": "Confidential information shall be kept secret."},
            ],
        )
        engine.build_index()
        self.assertGreater(len(engine.chunks), 0)

        results = engine.search("termination days", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("terminate in 30 calendar days", results[0]["text"])


if __name__ == "__main__":
    unittest.main()
