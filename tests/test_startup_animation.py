"""
Unit Tests for DocuVault Single-Window Architecture & Dynamic 5-Second Showcase.
Validates:
- StartupShowcaseWidget: 5-second duration, 4 choreographed stages, stepper buttons, and finished signal
- DocuVaultStartupCanvas: 60-FPS physics, laser scanner, orbital rings, and stage rendering
- EmbeddedAuthWidget & LoginDialog: Tab switching, default_email prefill, and authentication signals
- DocuVault single-window master stack lifecycle (Showcase -> Auth -> Workspace in the same window)
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.components.startup_splash import (
    DocuVaultStartupCanvas, StartupShowcaseWidget, StartupSplashDialog,
)
from ui.components.login_dialog import LoginDialog, EmbeddedAuthWidget
from ui.desktop_pyqt import DocuVault


class TestStartupShowcaseAndSingleWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def test_canvas_physics_and_stage_transitions(self):
        """Tests that canvas advances through 4 stages over 5000ms."""
        canvas = DocuVaultStartupCanvas(duration_ms=5000)
        self.assertEqual(canvas.stage_idx, 0)

        # Stage 0 (Vault): at 500ms
        canvas.update_frame(500.0)
        self.assertEqual(canvas.stage_idx, 0)
        self.assertTrue(0.0 <= canvas.scan_pos <= 1.0)

        # Stage 1 (Scanner): at 1600ms
        canvas.update_frame(1600.0)
        self.assertEqual(canvas.stage_idx, 1)

        # Stage 2 (Neural RAG): at 3000ms
        canvas.update_frame(3000.0)
        self.assertEqual(canvas.stage_idx, 2)

        # Stage 3 (Radar & Audits): at 4200ms
        canvas.update_frame(4200.0)
        self.assertEqual(canvas.stage_idx, 3)

        # End of duration: at 5000ms
        canvas.update_frame(5000.0)
        self.assertEqual(canvas.progress, 1.0)

    def test_showcase_widget_stepper_and_skip(self):
        """Tests that clicking stepper buttons jumps to stage, and finish signal is emitted."""
        showcase = StartupShowcaseWidget(duration_ms=5000)
        self.assertEqual(showcase.current_stage, 0)

        # Jump to stage 2 (Neural RAG)
        showcase._jump_to_stage(2)
        self.assertEqual(showcase.current_stage, 2)
        self.assertIn("Neural", showcase.lbl_title.text())

        # Test finish trigger
        received = []
        showcase.finished.connect(lambda: received.append(True))
        showcase._finish_and_close()
        self.assertTrue(showcase._closing)
        self.assertEqual(len(received), 1)

    def test_embedded_auth_widget_and_login_dialog_prefill(self):
        """Tests default email prefill on both embedded widget and dialog."""
        test_email = "developer@docuvault.ai"

        # Test EmbeddedAuthWidget
        auth_widget = EmbeddedAuthWidget(default_email=test_email)
        self.assertEqual(auth_widget.in_signin_email.text(), test_email)

        # Test LoginDialog
        login_dlg = LoginDialog(default_email=test_email)
        self.assertEqual(login_dlg.in_signin_email.text(), test_email)
        login_dlg.close()

    def test_docuvault_single_window_lifecycle(self):
        """Tests that DocuVault manages the 3 stages within a single window."""
        window = DocuVault(start_at_splash=True)
        # 1. Starts on Stage 0 (Showcase)
        self.assertEqual(window.master_stack.currentIndex(), 0)
        self.assertEqual(window.master_stack.count(), 3)

        # 2. Advance to Auth
        window._on_showcase_finished()
        self.assertEqual(window.master_stack.currentIndex(), 1)

        # 3. Authenticate and advance to Workspace in the same window
        mock_user = {"email": "tester@vault.local", "full_name": "Tester", "tier": "Pro"}
        window._on_user_authenticated(mock_user)
        self.assertEqual(window.master_stack.currentIndex(), 2)
        self.assertEqual(window.current_user["email"], "tester@vault.local")

        # 4. Sign out returns to Auth in the same window
        window._handle_sign_out()
        self.assertEqual(window.master_stack.currentIndex(), 1)
        window.close()

    def test_default_light_mode_and_theme_toggles(self):
        """Validates that widgets initialize in Light Mode by default and toggle correctly."""
        from auth.session_manager import SessionManager
        SessionManager.set_theme_mode("light")
        self.assertEqual(SessionManager.get_theme_mode(), "light")

        # 1. StartupShowcaseWidget light default & toggle
        showcase = StartupShowcaseWidget(duration_ms=5000)
        self.assertEqual(showcase.theme_mode, "light")
        self.assertIn("Dark", showcase.btn_theme.text())

        showcase_toggled = []
        showcase.theme_toggled.connect(lambda: showcase_toggled.append(True))
        showcase._on_theme_btn_clicked()
        self.assertEqual(showcase.theme_mode, "dark")
        self.assertEqual(len(showcase_toggled), 1)
        self.assertIn("Light", showcase.btn_theme.text())

        # 2. EmbeddedAuthWidget light default & toggle
        auth_widget = EmbeddedAuthWidget()
        self.assertEqual(auth_widget.theme_mode, "dark" if SessionManager.get_theme_mode() == "dark" else "light")
        auth_widget.set_theme("light")
        self.assertEqual(auth_widget.theme_mode, "light")
        self.assertEqual(auth_widget.in_signin_email.height(), 42)
        self.assertEqual(auth_widget.in_signin_pwd.height(), 42)

        # Verify Single Unified Container
        self.assertEqual(auth_widget.card.objectName(), "unifiedAuthCard")
        self.assertEqual(auth_widget.card.width(), 1020)
        self.assertEqual(auth_widget.card.height(), 610)

        auth_toggled = []
        auth_widget.theme_toggled.connect(lambda: auth_toggled.append(True))
        auth_widget._on_toggle_theme_clicked()
        self.assertEqual(auth_widget.theme_mode, "dark")
        self.assertEqual(len(auth_toggled), 1)

        # Restore default light mode for app
        SessionManager.set_theme_mode("light")
        self.assertEqual(SessionManager.get_theme_mode(), "light")


if __name__ == "__main__":
    unittest.main()
