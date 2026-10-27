import os
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QColor

# Set offscreen for headless render if needed, or normal
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.desktop_pyqt import AIFileOrganizerPage, InteractiveBackground, DARK, LIGHT
from core.organizer import FileOrganizerDaemon
from core.mongo_database import MongoDatabase

def test_file_organizer():
    app = QApplication.instance() or QApplication(sys.argv)
    
    organizer = FileOrganizerDaemon(vault_root="vault")
    mongo = MongoDatabase()
    
    # 1. Create a dummy parent window with interactive background to test translucency
    win = QMainWindow()
    win.resize(1200, 800)
    
    central = QWidget()
    win.setCentralWidget(central)
    c_lay = QVBoxLayout(central)
    c_lay.setContentsMargins(0, 0, 0, 0)
    
    # Add interactive constellation background
    bg = InteractiveBackground(theme=DARK, parent=central)
    bg.setGeometry(0, 0, 1200, 800)
    
    page = AIFileOrganizerPage(organizer=organizer, mongo=mongo, theme=DARK, parent=central)
    page.setGeometry(0, 0, 1200, 800)
    
    # Check metrics
    from PyQt6.QtWidgets import QLabel
    tot = page.card_total.findChild(QLabel, "cardVal").text()
    intake = page.card_intake.findChild(QLabel, "cardVal").text()
    quar = page.card_quarantine.findChild(QLabel, "cardVal").text()
    ops = page.card_ops.findChild(QLabel, "cardVal").text()
    
    print(f"Total Vault Files Card: {tot}")
    print(f"Intake Pending Card: {intake}")
    print(f"Quarantined Card: {quar}")
    print(f"Audit Ops Card: {ops}")
    print(f"Table Row Count: {page.table.rowCount()}")
    
    assert int(tot) > 0, f"Expected total vault files > 0, got {tot}"
    assert int(intake) > 0, f"Expected intake pending > 0, got {intake}"
    assert page.table.rowCount() > 0, f"Expected table rows > 0, got {page.table.rowCount()}"
    
    for r in range(min(5, page.table.rowCount())):
        fn = page.table.item(r, 1).text()
        sn = page.table.item(r, 2).text()
        print(f"  Row {r}: File={fn} | SmartName={sn}")
    
    # Render dark screenshot
    win.show()
    pix = QPixmap(1200, 800)
    win.render(pix)
    out_dir = Path("vault/plots")
    out_dir.mkdir(parents=True, exist_ok=True)
    dark_path = str(out_dir / "organizer_glass_dark.png")
    pix.save(dark_path)
    print(f"Dark mode screenshot saved to {dark_path} ({os.path.getsize(dark_path)} bytes)")
    
    # Test Light mode
    page.update_theme(LIGHT)
    pix_light = QPixmap(1200, 800)
    win.render(pix_light)
    light_path = str(out_dir / "organizer_glass_light.png")
    pix_light.save(light_path)
    print(f"Light mode screenshot saved to {light_path} ({os.path.getsize(light_path)} bytes)")
    
    print("ALL VERIFICATIONS PASSED!")

if __name__ == "__main__":
    test_file_organizer()
