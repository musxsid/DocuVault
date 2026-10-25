import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from ui.desktop_pyqt import DocuVault, DARK, LIGHT
from ui.components.login_dialog import EmbeddedAuthWidget
from auth.session_manager import SessionManager

def capture_ui():
    app = QApplication.instance() or QApplication(sys.argv)
    output_dir = Path(r"C:\Users\siddh\.gemini\antigravity-ide\brain\b6d2c48b-dac1-447b-ba18-3ce7f04f23d0\.tempmediaStorage")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Capture Auth Screen Dark
    auth_dark = EmbeddedAuthWidget(theme_mode="dark")
    auth_dark.resize(1180, 720)
    auth_dark.show()
    app.processEvents()
    pix = auth_dark.grab()
    pix.save(str(output_dir / "auth_dark_centered.png"))
    auth_dark.close()

    # 2. Capture Auth Screen Light
    auth_light = EmbeddedAuthWidget(theme_mode="light")
    auth_light.resize(1180, 720)
    auth_light.show()
    app.processEvents()
    pix = auth_light.grab()
    pix.save(str(output_dir / "auth_light_centered.png"))
    auth_light.close()

    # 3. Capture AI Assistant Page in Workspace (Dark Mode)
    SessionManager.set_theme_mode("dark")
    mock_user = {"email": "siddharth@docuvault.ai", "full_name": "Siddharth", "tier": "Pro"}
    win_dark = DocuVault(current_user=mock_user, start_at_splash=False)
    win_dark.resize(1380, 880)
    win_dark.show()
    app.processEvents()
    # Add a sample grounded query so we can see the chat response & citations
    win_dark.page_ai.ask_query("What is the termination notice period across my contracts?")
    # Let ticks run for background animation
    for _ in range(10):
        app.processEvents()
    pix = win_dark.grab()
    pix.save(str(output_dir / "ai_chat_dark.png"))

    # 4. Open AI Drawer on Documents Page and capture
    win_dark._on_page_selected(1)  # Documents page
    win_dark._toggle_ai_drawer()   # Open AI Drawer
    for _ in range(10):
        app.processEvents()
    pix_drawer = win_dark.grab()
    pix_drawer.save(str(output_dir / "ai_drawer_dark.png"))

    # 5. Toggle to Light Mode on AI Assistant page and capture
    win_dark._on_page_selected(0)  # Back to AI Assistant page
    win_dark._toggle_theme()
    for _ in range(10):
        app.processEvents()
    pix = win_dark.grab()
    pix.save(str(output_dir / "ai_chat_light.png"))

    win_dark.close()
    print("UI Captures saved successfully!")

if __name__ == "__main__":
    capture_ui()
