"""
DocuVault — Air-Gapped Local User Authentication Store
Provides offline authentication using SQLite and salted PBKDF2-HMAC password hashing.
Ensures zero-cloud dependency when operating in restricted air-gapped environments.
"""

import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.exceptions import AuthenticationError


from contextlib import contextmanager


class LocalAuthManager:
    """
    Manages offline-first user accounts, password hashing, and subscription tiers
    stored in a local SQLite database with zero administrative role hierarchies.
    """

    DB_PATH = Path("vault/users.db")

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(db_path).resolve() if db_path else self.DB_PATH.resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes the users table if not already present."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY COLLATE NOCASE,
                    full_name TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'Free',
                    country TEXT DEFAULT 'Global',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    @staticmethod
    def _hash_password(password: str, salt_bytes: Optional[bytes] = None) -> tuple[str, str]:
        """Generates salted PBKDF2-HMAC SHA-256 hash (100,000 iterations)."""
        if salt_bytes is None:
            salt_bytes = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            100_000,
        )
        return salt_bytes.hex(), pwd_hash.hex()

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        country: str = "Global",
        tier: str = "Free",
    ) -> Dict[str, Any]:
        """
        Registers a new user worldwide with default 'Free' tier.
        Raises AuthenticationError if email is already registered.
        """
        email_clean = email.strip().lower()
        if not email_clean or "@" not in email_clean:
            raise AuthenticationError("Invalid email address format.", username_or_email=email)
        if len(password) < 6:
            raise AuthenticationError("Password must be at least 6 characters.", username_or_email=email)

        salt_hex, hash_hex = self._hash_password(password)
        now_iso = datetime.now().isoformat()
        tier_clean = "Pro" if str(tier).capitalize() == "Pro" else "Free"

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (email, full_name, salt, password_hash, tier, country, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (email_clean, full_name.strip(), salt_hex, hash_hex, tier_clean, country.strip(), now_iso, now_iso),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            raise AuthenticationError(f"Account with email '{email_clean}' already exists.", username_or_email=email_clean)

        return {
            "email": email_clean,
            "full_name": full_name.strip(),
            "tier": tier_clean,
            "country": country.strip(),
            "created_at": now_iso,
        }

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verifies credentials against PBKDF2 hash.
        Returns user dictionary if valid, or raises AuthenticationError.
        """
        email_clean = email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email_clean,)
            ).fetchone()

        if not row:
            raise AuthenticationError("Account not found. Please check your email or register.", username_or_email=email_clean)

        salt_bytes = bytes.fromhex(row["salt"])
        _, test_hash = self._hash_password(password, salt_bytes)

        if test_hash != row["password_hash"]:
            raise AuthenticationError("Incorrect password. Please try again.", username_or_email=email_clean)

        return {
            "email": row["email"],
            "full_name": row["full_name"],
            "tier": row["tier"],
            "country": row["country"],
            "created_at": row["created_at"],
        }

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves user profile data by email."""
        email_clean = email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email_clean,)).fetchone()
        if not row:
            return None
        return {
            "email": row["email"],
            "full_name": row["full_name"],
            "tier": row["tier"],
            "country": row["country"],
            "created_at": row["created_at"],
        }

    def update_user_tier(self, email: str, new_tier: str = "Pro") -> bool:
        """Instantly upgrades or modifies a user's subscription tier."""
        email_clean = email.strip().lower()
        now_iso = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET tier = ?, updated_at = ? WHERE email = ?",
                (new_tier, now_iso, email_clean),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_users(self) -> List[Dict[str, Any]]:
        """Returns a list of all local accounts."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT email, full_name, tier, country, created_at FROM users").fetchall()
        return [dict(r) for r in rows]
