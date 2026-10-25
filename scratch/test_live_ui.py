import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from ui.desktop_pyqt import DocuVault, DARK, LIGHT
from auth.session_manager import SessionManager

def test_live_ui():
    app = QApplication.instance() or QApplication(sys.argv)
    output_dir = Path(r"C:\Users\siddh\.gemini\antigravity-ide\brain\b6d2c48b-dac1-447b-ba18-3ce7f04f23d0\.tempmediaStorage")
    output_dir.mkdir(parents=True, exist_ok=True)

    SessionManager.set_theme_mode("dark")
    mock_user = {"email": "siddharth@docuvault.ai", "full_name": "Siddharth", "tier": "Pro"}

    win = DocuVault(current_user=mock_user, start_at_splash=False)
    win.resize(1400, 900)
    win.show()
    app.processEvents()

    # 1. Documents page is default on startup (Index 0)
    print("Default page index:", win.stack.currentIndex())
    assert win.stack.currentIndex() == 0, f"Expected 0, got {win.stack.currentIndex()}"

    for _ in range(15):
        app.processEvents()

    # Capture default Documents page (Clean empty state ready for tracking)
    pix_empty = win.grab()
    pix_empty.save(str(output_dir / "docs_default_empty_dark.png"))
    print("Saved docs_default_empty_dark.png")

    # 2. Test tracking directory / adding a document to demonstrate live ingestion
    test_doc = {
        "doc_id": "test_nda_001",
        "filename": "Mutual_Non_Disclosure_Agreement.pdf",
        "category": "Legal",
        "status": "Verified",
        "size_bytes": 245760,
        "page_count": 3,
        "created_at": "2026-10-26T01:00:00",
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "pages": [{"page_number": 1, "text": "This Mutual Non-Disclosure Agreement is entered into by Apex Dynamics and Quantum Labs."}],
        "counterparties": ["Apex Dynamics", "Quantum Labs"],
        "clauses": {"Governing Law": "State of Delaware", "Term": "3 years from effective date"},
        "risk_profile": {"score": 15, "level": "Low", "color": "#10B981"}
    }
    win.docs[test_doc["doc_id"]] = test_doc
    win.mongo.save_document(test_doc)
    win._render_documents()
    win._update_metrics_bar()
    for _ in range(15):
        app.processEvents()

    # Capture Documents page with document row
    pix_docs = win.grab()
    pix_docs.save(str(output_dir / "docs_with_document_row.png"))
    print("Saved docs_with_document_row.png")

    # 3. Open Details Drawer side-by-side in center_splitter
    win._select_document(test_doc, open_drawer=True)
    for _ in range(20):
        app.processEvents()

    pix_drawer = win.grab()
    pix_drawer.save(str(output_dir / "docs_details_drawer_open.png"))
    print("Saved docs_details_drawer_open.png")

    # 4. Open AI Drawer alongside Details Drawer (both side-by-side in center_splitter)
    win._toggle_ai_drawer()
    for _ in range(20):
        app.processEvents()

    pix_dual = win.grab()
    pix_dual.save(str(output_dir / "docs_dual_drawers_open.png"))
    print("Saved docs_dual_drawers_open.png")

    # Clean up test doc from Mongo
    win.mongo.delete_document("test_nda_001")
    if "test_nda_001" in win.docs:
        del win.docs["test_nda_001"]
    win._render_documents()
    win._update_metrics_bar()

    win.close()
    print("Live UI verification complete!")

if __name__ == "__main__":
    test_live_ui()
