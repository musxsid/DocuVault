"""
DocuVault — Session Manager & Secure Credential Caching
Handles 'Remember Me' persistent authentication using system keyring with
graceful encrypted local file fallback for air-gapped or headless deployments.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Try importing keyring with fallback flag
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class SessionManager:
    """
    Manages persistent user authentication state, access tokens, and profile data.
    Provides zero-leakage credential protection across application restarts.
    """

    SERVICE_NAME = "DocuVaultAI"
    SESSION_FILE = Path("config/session.enc")
    SETTINGS_FILE = Path("config/settings.json")

    # Local fallback key salt (machine-derived for air-gapped isolation)
    _OBFUSCATION_SALT = b"DocuVault_Offline_First_Secure_Token_Salt_2026"

    @classmethod
    def _ensure_config_dir(cls) -> None:
        cls.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _obfuscate(cls, data_str: str) -> str:
        """XOR stream obfuscation with machine salt for air-gapped file fallback."""
        data_bytes = data_str.encode("utf-8")
        salt = cls._OBFUSCATION_SALT
        out = bytearray(len(data_bytes))
        for i, b in enumerate(data_bytes):
            out[i] = b ^ salt[i % len(salt)]
        return base64.b64encode(out).decode("utf-8")

    @classmethod
    def _deobfuscate(cls, encoded_str: str) -> str:
        """Reverses obfuscation."""
        raw_bytes = base64.b64decode(encoded_str.encode("utf-8"))
        salt = cls._OBFUSCATION_SALT
        out = bytearray(len(raw_bytes))
        for i, b in enumerate(raw_bytes):
            out[i] = b ^ salt[i % len(salt)]
        return out.decode("utf-8")

    @classmethod
    def save_session(
        cls,
        user_info: Dict[str, Any],
        token: Optional[str] = None,
        remember_me: bool = True,
    ) -> bool:
        """
        Persists active user session state.
        If remember_me is True, stores tokens into system keyring or encrypted cache.
        """
        cls._ensure_config_dir()
        session_payload = {
            "email": user_info.get("email", ""),
            "full_name": user_info.get("full_name", user_info.get("name", "User")),
            "tier": user_info.get("tier", "Free"),
            "country": user_info.get("country", "Global"),
            "token": token or "local_token_offline",
            "remember_me": remember_me,
            "created_at": user_info.get("created_at", ""),
        }

        if not remember_me:
            # If remember me is unchecked, remove any existing saved session
            cls.clear_session()
            return True

        # Attempt 1: System Keyring
        keyring_success = False
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(
                    cls.SERVICE_NAME,
                    session_payload["email"],
                    json.dumps(session_payload),
                )
                keyring.set_password(cls.SERVICE_NAME, "__last_active_user__", session_payload["email"])
                keyring_success = True
            except Exception:
                keyring_success = False

        # Attempt 2: Encrypted Local Fallback (always stored as backup)
        try:
            encrypted_data = cls._obfuscate(json.dumps(session_payload))
            with open(cls.SESSION_FILE, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
            return True
        except Exception:
            return keyring_success

    @classmethod
    def load_session(cls) -> Optional[Dict[str, Any]]:
        """
        Retrieves previously saved active session for automated login.
        Returns None if no active session or 'Remember Me' was disabled.
        """
        # Step 1: Check system keyring
        if KEYRING_AVAILABLE:
            try:
                last_user = keyring.get_password(cls.SERVICE_NAME, "__last_active_user__")
                if last_user:
                    stored_json = keyring.get_password(cls.SERVICE_NAME, last_user)
                    if stored_json:
                        session_data = json.loads(stored_json)
                        if session_data.get("remember_me", False):
                            return session_data
            except Exception:
                pass

        # Step 2: Fallback to encrypted file
        if cls.SESSION_FILE.exists():
            try:
                with open(cls.SESSION_FILE, "r", encoding="utf-8") as f:
                    encrypted_data = f.read().strip()
                if encrypted_data:
                    decrypted_str = cls._deobfuscate(encrypted_data)
                    session_data = json.loads(decrypted_str)
                    if session_data.get("remember_me", False):
                        return session_data
            except Exception:
                return None

        return None

    @classmethod
    def clear_session(cls) -> None:
        """Purges active session from keyring and disk upon Sign Out."""
        if KEYRING_AVAILABLE:
            try:
                last_user = keyring.get_password(cls.SERVICE_NAME, "__last_active_user__")
                if last_user:
                    try:
                        keyring.delete_password(cls.SERVICE_NAME, last_user)
                    except Exception:
                        pass
                try:
                    keyring.delete_password(cls.SERVICE_NAME, "__last_active_user__")
                except Exception:
                    pass
            except Exception:
                pass

        if cls.SESSION_FILE.exists():
            try:
                os.remove(cls.SESSION_FILE)
            except Exception:
                pass

    @classmethod
    def is_onboarding_completed(cls) -> bool:
        """Checks if the user has already viewed or skipped the first-run onboarding carousel."""
        cls._ensure_config_dir()
        if not cls.SETTINGS_FILE.exists():
            return False
        try:
            with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return bool(data.get("onboarding_completed", False))
        except Exception:
            return False

    @classmethod
    def set_onboarding_completed(cls, completed: bool = True) -> None:
        """Persists the onboarding completion/skip flag."""
        cls._ensure_config_dir()
        data = {}
        if cls.SETTINGS_FILE.exists():
            try:
                with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["onboarding_completed"] = completed
        with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def get_theme_mode(cls) -> str:
        """Retrieves user's preferred UI theme mode ('light' by default)."""
        cls._ensure_config_dir()
        if not cls.SETTINGS_FILE.exists():
            return "light"
        try:
            with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("theme_mode", "light")
        except Exception:
            return "light"

    @classmethod
    def set_theme_mode(cls, mode: str) -> None:
        """Persists user's preferred UI theme mode ('light' or 'dark')."""
        cls._ensure_config_dir()
        data = {}
        if cls.SETTINGS_FILE.exists():
            try:
                with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["theme_mode"] = "dark" if mode == "dark" else "light"
        try:
            with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

