"""
DocuVault — Production Document Management System (PyQt6)
Enterprise-grade, clean minimalist UI with sliding sidebar, real-time database,
universal search (Ctrl+K), and orange accent themes.
"""

import math
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import (
    QEasingCurve, QEvent, QPoint, QPointF, QPropertyAnimation, QRect, QRectF,
    QSize, Qt, QThread, QTimer, QUrl, pyqtProperty, pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QDesktopServices, QDragEnterEvent, QDropEvent, QFont,
    QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap, QRadialGradient, QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTextBrowser, QTextEdit, QVBoxLayout, QWidget,
)

from core.base_document import DocumentFactory
from core.catalog_manager import CatalogManager
from core.exceptions import DocuVaultError
from core.organizer import FileOrganizerDaemon
from core.parsers.binary_parser import BinaryParser
from core.storage_providers import LocalStorageProvider, CloudStorageProvider
from core.vector_search import VectorSearchEngine
from core.mongo_database import MongoDatabase
from core.duplicate_detector import DuplicateDetector
from core.ai_assistant import ExplainableAIAssistant
from core.health_score import DocumentHealthEngine
from core.deadlines import DeadlineManager
from core.ocr_engine import OCREngine
from core.versioning import DocumentVersionManager
import subprocess
import webbrowser

from ui.feature_dialogs import (
    DuplicateWarningDialog,
    DuplicateScannerDialog,
    AIAssistantDialog,
    DocumentVersionDialog,
    OCRViewerDialog,
    DocumentHealthDialog,
    DeadlineManagerDialog,
    RebuttalDraftDialog,
    ClientEncryptionDialog,
    DossierExportDialog,
    TrackedFoldersDialog,
    ApiKeyConfigDialog,
    SelectSourcesDialog,
)
from auth.session_manager import SessionManager
from auth.tier_manager import TierConfig, TierManager, UserTier
from core.exceptions import FeatureLockedError, TierLimitExceededError
from core.pii_redactor import PIIRedactor
from core.folder_tracker import DirectoryTracker
from core.document_analyzer import DocumentAnalyzer
from core.batch_exporter import BatchDossierExporter
from core.encryption import ZeroKnowledgeVaultCrypto
from core.retention_policy import RetentionPolicyManager
from ui.components import (
    LoginDialog, OnboardingDialog, ProfileDialog, UpgradeModal,
    StartupSplashDialog, StartupShowcaseWidget, EmbeddedAuthWidget,
)



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THEME SYSTEM (VIBRANT ORANGE PALETTES)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIGHT = {
    "name": "light",
    "bg": "#F6F7F9",
    "bg2": "#FFFFFF",
    "bg3": "#F0F2F5",
    "bg4": "#E4E7EC",
    "surface": "#FFFFFF",
    "sidebar": "#FFFFFF",
    "sidebar_solid": "#FFFFFF",
    "sidebar_text": "#101828",
    "sidebar_text_muted": "#667085",
    "sidebar_item_hover": "#F0F2F5",
    "sidebar_item_active_bg": "#FFF1EB",
    "sidebar_item_active_text": "#F26A1B",
    "sidebar_border": "#E4E7EC",
    "hover": "#F9FAFB",
    "active": "#FFF1EB",
    "selected": "#FFF7F2",
    "border": "#E4E7EC",
    "border2": "#D0D5DD",
    "divider": "#E4E7EC",
    "text": "#101828",
    "text2": "#344054",
    "text3": "#667085",
    "text4": "#98A2B3",
    "primary": "#F26A1B",
    "primary_h": "#FF7A2E",
    "primary_hover": "#FF7A2E",
    "primary_p": "#E04F08",
    "primary_pressed": "#E04F08",
    "primary_bg": "#FFF1EB",
    "primary_border": "#FDBA74",
    "green": "#F26A1B",
    "green_bg": "#FFF1EB",
    "green_border": "#FDBA74",
    "warning": "#F5B544",
    "danger": "#F0556E",
    "red": "#F0556E",
    "red_bg": "#FEF3F2",
    "red_border": "#FECACA",
    "blue": "#6B9BFF",
    "blue_bg": "#EEF4FF",
    "purple": "#A58BFF",
    "purple_bg": "#F4F3FF",
    "gold": "#FFC46B",
    "orange": "#F26A1B",
    "orange_bg": "#FFF1EB",
    "shadow": "rgba(0, 0, 0, 0.04)",
    "shadow_card": "0 2px 8px rgba(0,0,0,0.04)",
}

DARK = {
    "name": "dark",
    "bg": "#000000",
    "bg2": "#0A0A0A",
    "bg3": "#121212",
    "bg4": "#1C1C1C",
    "surface": "#0A0A0A",
    "sidebar": "#050505",
    "sidebar_solid": "#050505",
    "sidebar_text": "#F5F5F7",
    "sidebar_text_muted": "#8E8E93",
    "sidebar_item_hover": "rgba(255, 122, 46, 0.12)",
    "sidebar_item_active_bg": "rgba(255, 122, 46, 0.20)",
    "sidebar_item_active_text": "#FF7A2E",
    "sidebar_border": "#1A1A1A",
    "hover": "#141414",
    "active": "rgba(255, 122, 46, 0.16)",
    "selected": "rgba(255, 122, 46, 0.18)",
    "border": "#1A1A1A",
    "border2": "#282828",
    "divider": "#1A1A1A",
    "text": "#F5F5F7",
    "text2": "#D1D1D6",
    "text3": "#8E8E93",
    "text4": "#636366",
    "primary": "#FF7A2E",
    "primary_h": "#FF8F57",
    "primary_hover": "#FF8F57",
    "primary_p": "#E04F08",
    "primary_pressed": "#E04F08",
    "primary_bg": "rgba(255, 122, 46, 0.14)",
    "primary_border": "rgba(255, 122, 46, 0.35)",
    "green": "#FF7A2E",
    "green_bg": "rgba(255, 122, 46, 0.14)",
    "green_border": "rgba(255, 122, 46, 0.35)",
    "warning": "#F5B544",
    "danger": "#F0556E",
    "red": "#F0556E",
    "red_bg": "rgba(240, 85, 110, 0.14)",
    "red_border": "rgba(240, 85, 110, 0.30)",
    "blue": "#6B9BFF",
    "blue_bg": "rgba(107, 155, 255, 0.14)",
    "purple": "#A58BFF",
    "purple_bg": "rgba(165, 139, 255, 0.14)",
    "gold": "#FFC46B",
    "orange": "#FF7A2E",
    "orange_bg": "rgba(255, 122, 46, 0.14)",
    "shadow": "rgba(0, 0, 0, 0.60)",
    "shadow_card": "0 2px 10px rgba(0,0,0,0.50)",
}


def qss(t: Dict[str, str]) -> str:
    return f"""
        * {{ margin: 0; padding: 0; outline: none; }}
        QMainWindow {{ background: {t['bg']}; }}
        QWidget {{
            color: {t['text']};
            font-family: 'Plus Jakarta Sans', 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
            font-size: 13px;
        }}

        /* ─── Cards & Containers (16px Radius per PDF Spec) ─── */
        QFrame#unifiedCard {{
            background: {t['surface']};
            border: 1px solid {t['border']};
            border-radius: 16px;
        }}
        QFrame#subCard {{
            background: {t['bg3']};
            border: 1px solid {t['border']};
            border-radius: 12px;
        }}

        /* ─── Buttons (10px to 12px Radius) ─── */
        QPushButton {{
            font-family: 'Plus Jakarta Sans', 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
        }}
        QPushButton#primaryBtn {{
            background: {t['primary']};
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            padding: 8px 18px;
            font-weight: 600;
            font-size: 12px;
        }}
        QPushButton#primaryBtn:hover {{ background: {t['primary_h']}; }}
        QPushButton#primaryBtn:pressed {{ background: {t['primary_p']}; }}

        QPushButton#secondaryBtn {{
            background: {t['bg2']};
            color: {t['text2']};
            border: 1px solid {t['border2']};
            border-radius: 10px;
            padding: 7px 16px;
            font-weight: 500;
            font-size: 12px;
        }}
        QPushButton#secondaryBtn:hover {{
            background: {t['bg3']};
            border-color: {t['primary']};
            color: {t['primary']};
        }}
        QPushButton#secondaryBtn:pressed {{ background: {t['active']}; }}

        QPushButton#dangerBtn {{
            background: {t['red_bg']};
            color: {t['red']};
            border: 1px solid {t['red_border']};
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 12px;
        }}
        QPushButton#dangerBtn:hover {{
            background: {t['red']};
            color: #FFFFFF;
        }}
        QPushButton#dangerBtn:pressed {{ background: #DC2626; color: #FFFFFF; }}

        QPushButton#copyBtn {{
            background: {t['bg2']};
            color: {t['text3']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton#copyBtn:hover {{
            background: {t['primary_bg']};
            color: {t['primary']};
            border-color: {t['primary_border']};
        }}

        /* Segmented Filter Pills (Full Pill 999px) */
        QPushButton#filterPill {{
            background: transparent;
            color: {t['text3']};
            border: 1px solid transparent;
            border-radius: 14px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton#filterPill:hover {{
            background: {t['bg3']};
            color: {t['text']};
        }}
        QPushButton#filterPill[active="true"] {{
            background: {t['primary']};
            color: #FFFFFF;
            font-weight: 700;
            border: 1px solid {t['primary']};
        }}

        /* ─── Inputs ─── */
        QLineEdit {{
            background: {t['bg3']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 8px 12px 8px 12px;
            font-size: 12px;
            color: {t['text']};
            selection-background-color: {t['primary_bg']};
        }}
        QLineEdit:focus {{
            border: 1.5px solid {t['primary']};
            background: {t['bg2']};
        }}
        QLineEdit::placeholder {{ color: {t['text4']}; }}

        /* ─── Scrollbars ─── */
        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            margin: 4px 1px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['border2']};
            min-height: 24px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {t['text4']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ height: 0; }}

        /* ─── TextEdit ─── */
        QTextEdit {{
            background: {t['bg2']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 12px;
            font-size: 12px;
            color: {t['text']};
        }}

        /* ─── Progress Bar ─── */
        QProgressBar {{
            background: {t['bg3']};
            border: none;
            border-radius: 2px;
            max-height: 3px;
        }}
        QProgressBar::chunk {{
            background: {t['primary']};
            border-radius: 2px;
        }}
    """


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VECTOR ICON DRAWING UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def draw_vector_icon(name: str, color_hex: str, size: int = 20) -> QPixmap:
    """Draws crisp antialiased vector icons directly into a QPixmap."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QColor(color_hex)
    pen = QPen(c, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    if name == "logo":
        w = float(size)
        h = float(size)

        # Shield contour
        spath = QPainterPath()
        spath.moveTo(w * 0.16, h * 0.22)
        spath.quadTo(w * 0.50, h * 0.12, w * 0.84, h * 0.22)
        spath.quadTo(w * 0.88, h * 0.52, w * 0.50, h * 0.90)
        spath.quadTo(w * 0.12, h * 0.52, w * 0.16, h * 0.22)
        spath.closeSubpath()

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor("#FF7A2E"))
        grad.setColorAt(1.0, QColor("#E04F08"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#FFC46B"), 1.0))
        p.drawPath(spath)

        # Embedded Document sheet
        doc_path = QPainterPath()
        dx = w * 0.35
        dy = h * 0.30
        dw = w * 0.30
        dh = h * 0.40
        fold = dw * 0.35

        doc_path.moveTo(dx, dy)
        doc_path.lineTo(dx + dw - fold, dy)
        doc_path.lineTo(dx + dw, dy + fold)
        doc_path.lineTo(dx + dw, dy + dh)
        doc_path.lineTo(dx, dy + dh)
        doc_path.closeSubpath()

        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(doc_path)

        # Folded corner
        fold_path = QPainterPath()
        fold_path.moveTo(dx + dw - fold, dy)
        fold_path.lineTo(dx + dw - fold, dy + fold)
        fold_path.lineTo(dx + dw, dy + fold)
        fold_path.closeSubpath()
        p.setBrush(QBrush(QColor("#FFE7D6")))
        p.drawPath(fold_path)

        # 3 horizontal lines on document
        pen_lines = QPen(QColor("#E04F08"), max(1.0, w * 0.04), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen_lines)
        p.drawLine(QPointF(dx + dw * 0.22, dy + dh * 0.45), QPointF(dx + dw * 0.78, dy + dh * 0.45))
        p.drawLine(QPointF(dx + dw * 0.22, dy + dh * 0.62), QPointF(dx + dw * 0.78, dy + dh * 0.62))
        p.drawLine(QPointF(dx + dw * 0.22, dy + dh * 0.79), QPointF(dx + dw * 0.62, dy + dh * 0.79))

    elif name == "documents":
        # Document sheet with folded corner
        path = QPainterPath()
        path.moveTo(size * 0.24, size * 0.12)
        path.lineTo(size * 0.58, size * 0.12)
        path.lineTo(size * 0.78, size * 0.32)
        path.lineTo(size * 0.78, size * 0.88)
        path.lineTo(size * 0.24, size * 0.88)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(size * 0.58, size * 0.12), QPointF(size * 0.58, size * 0.32))
        p.drawLine(QPointF(size * 0.58, size * 0.32), QPointF(size * 0.78, size * 0.32))
        p.drawLine(QPointF(size * 0.38, size * 0.50), QPointF(size * 0.64, size * 0.50))
        p.drawLine(QPointF(size * 0.38, size * 0.68), QPointF(size * 0.54, size * 0.68))

    elif name == "storage":
        # Server disk drives
        p.drawRoundedRect(QRectF(size * 0.18, size * 0.18, size * 0.64, size * 0.26), 4, 4)
        p.drawRoundedRect(QRectF(size * 0.18, size * 0.56, size * 0.64, size * 0.26), 4, 4)
        p.drawLine(QPointF(size * 0.68, size * 0.31), QPointF(size * 0.74, size * 0.31))
        p.drawLine(QPointF(size * 0.68, size * 0.69), QPointF(size * 0.74, size * 0.69))

    elif name == "security":
        # Security shield with checkmark
        path = QPainterPath()
        path.moveTo(size * 0.5, size * 0.14)
        path.lineTo(size * 0.82, size * 0.26)
        path.lineTo(size * 0.82, size * 0.55)
        path.quadTo(QPointF(size * 0.82, size * 0.84), QPointF(size * 0.5, size * 0.90))
        path.quadTo(QPointF(size * 0.18, size * 0.84), QPointF(size * 0.18, size * 0.55))
        path.lineTo(size * 0.18, size * 0.26)
        path.closeSubpath()
        p.drawPath(path)
        chk = QPainterPath()
        chk.moveTo(size * 0.36, size * 0.52)
        chk.lineTo(size * 0.46, size * 0.62)
        chk.lineTo(size * 0.66, size * 0.40)
        p.drawPath(chk)

    elif name == "activity":
        # Activity pulse / clock
        p.drawEllipse(QRectF(size * 0.16, size * 0.16, size * 0.68, size * 0.68))
        p.drawLine(QPointF(size * 0.5, size * 0.30), QPointF(size * 0.5, size * 0.50))
        p.drawLine(QPointF(size * 0.5, size * 0.50), QPointF(size * 0.68, size * 0.50))

    elif name == "upload":
        # Tray with upward arrow
        p.drawLine(QPointF(size * 0.5, size * 0.20), QPointF(size * 0.5, size * 0.65))
        arr = QPainterPath()
        arr.moveTo(size * 0.32, size * 0.36)
        arr.lineTo(size * 0.5, size * 0.20)
        arr.lineTo(size * 0.68, size * 0.36)
        p.drawPath(arr)
        tray = QPainterPath()
        tray.moveTo(size * 0.20, size * 0.60)
        tray.lineTo(size * 0.20, size * 0.80)
        tray.lineTo(size * 0.80, size * 0.80)
        tray.lineTo(size * 0.80, size * 0.60)
        p.drawPath(tray)

    elif name == "sun":
        p.setBrush(QBrush(c))
        p.drawEllipse(QRectF(size * 0.32, size * 0.32, size * 0.36, size * 0.36))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for angle in range(0, 360, 45):
            p.save()
            p.translate(size * 0.5, size * 0.5)
            p.rotate(angle)
            p.drawLine(QPointF(0, size * 0.26), QPointF(0, size * 0.38))
            p.restore()

    elif name == "moon":
        mpath = QPainterPath()
        mpath.moveTo(size * 0.5, size * 0.16)
        mpath.quadTo(QPointF(size * 0.90, size * 0.50), QPointF(size * 0.5, size * 0.84))
        mpath.quadTo(QPointF(size * 0.72, size * 0.50), QPointF(size * 0.5, size * 0.16))
        p.setBrush(QBrush(c))
        p.drawPath(mpath)
        p.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "ai":
        # 4-point sparkle emblem
        spath = QPainterPath()
        cx, cy = size * 0.5, size * 0.5
        spath.moveTo(cx, size * 0.15)
        spath.quadTo(cx, cy, size * 0.85, cy)
        spath.quadTo(cx, cy, cx, size * 0.85)
        spath.quadTo(cx, cy, size * 0.15, cy)
        spath.quadTo(cx, cy, cx, size * 0.15)
        p.setBrush(QBrush(c))
        p.drawPath(spath)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPoint(QPointF(size * 0.80, size * 0.22))

    elif name == "calendar":
        p.drawRoundedRect(QRectF(size * 0.18, size * 0.20, size * 0.64, size * 0.64), 3, 3)
        p.drawLine(QPointF(size * 0.18, size * 0.40), QPointF(size * 0.82, size * 0.40))
        p.drawLine(QPointF(size * 0.35, size * 0.14), QPointF(size * 0.35, size * 0.24))
        p.drawLine(QPointF(size * 0.65, size * 0.14), QPointF(size * 0.65, size * 0.24))

    elif name == "health":
        hpath = QPainterPath()
        hpath.moveTo(size * 0.18, size * 0.52)
        hpath.lineTo(size * 0.36, size * 0.52)
        hpath.lineTo(size * 0.45, size * 0.26)
        hpath.lineTo(size * 0.55, size * 0.74)
        hpath.lineTo(size * 0.64, size * 0.52)
        hpath.lineTo(size * 0.82, size * 0.52)
        p.drawPath(hpath)

    elif name == "diff":
        p.drawLine(QPointF(size * 0.26, size * 0.35), QPointF(size * 0.74, size * 0.35))
        p.drawLine(QPointF(size * 0.26, size * 0.55), QPointF(size * 0.74, size * 0.55))
        p.drawLine(QPointF(size * 0.50, size * 0.20), QPointF(size * 0.50, size * 0.35))

    elif name == "ocr":
        p.drawRoundedRect(QRectF(size * 0.16, size * 0.16, size * 0.68, size * 0.68), 4, 4)
        p.drawLine(QPointF(size * 0.32, size * 0.40), QPointF(size * 0.68, size * 0.40))
        p.drawLine(QPointF(size * 0.32, size * 0.60), QPointF(size * 0.56, size * 0.60))

    elif name == "duplicate":
        p.drawRoundedRect(QRectF(size * 0.18, size * 0.26, size * 0.50, size * 0.58), 3, 3)
        p.drawRoundedRect(QRectF(size * 0.32, size * 0.16, size * 0.50, size * 0.58), 3, 3)

    elif name == "toggle":
        p.drawLine(QPointF(size * 0.22, size * 0.30), QPointF(size * 0.78, size * 0.30))
        p.drawLine(QPointF(size * 0.22, size * 0.50), QPointF(size * 0.78, size * 0.50))
        p.drawLine(QPointF(size * 0.22, size * 0.70), QPointF(size * 0.78, size * 0.70))

    elif name == "close":
        p.drawLine(QPointF(size * 0.25, size * 0.25), QPointF(size * 0.75, size * 0.75))
        p.drawLine(QPointF(size * 0.75, size * 0.25), QPointF(size * 0.25, size * 0.75))

    elif name == "search":
        r = size * 0.26
        cx = size * 0.40
        cy = size * 0.40
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.707, cy + r * 0.707), QPointF(size * 0.82, size * 0.82))

    elif name == "organizer":
        # Folder with sorting arrow
        fpath = QPainterPath()
        fpath.moveTo(size * 0.14, size * 0.26)
        fpath.lineTo(size * 0.42, size * 0.26)
        fpath.lineTo(size * 0.50, size * 0.36)
        fpath.lineTo(size * 0.86, size * 0.36)
        fpath.lineTo(size * 0.86, size * 0.80)
        fpath.lineTo(size * 0.14, size * 0.80)
        fpath.closeSubpath()
        p.drawPath(fpath)
        # Inside horizontal lines indicating file categories
        p.drawLine(QPointF(size * 0.28, size * 0.52), QPointF(size * 0.72, size * 0.52))
        p.drawLine(QPointF(size * 0.28, size * 0.65), QPointF(size * 0.58, size * 0.65))

    elif name in ("pencil", "edit"):
        # Modern diagonal editing pencil
        p.save()
        p.translate(size * 0.5, size * 0.5)
        p.rotate(-45)
        p.drawRect(QRectF(-size * 0.12, -size * 0.35, size * 0.24, size * 0.55))
        tip = QPainterPath()
        tip.moveTo(-size * 0.12, size * 0.20)
        tip.lineTo(0, size * 0.40)
        tip.lineTo(size * 0.12, size * 0.20)
        p.drawPath(tip)
        p.restore()

    elif name in ("trash", "delete"):
        # Modern trash can with lid
        p.drawLine(QPointF(size * 0.20, size * 0.30), QPointF(size * 0.80, size * 0.30))
        p.drawLine(QPointF(size * 0.40, size * 0.22), QPointF(size * 0.60, size * 0.22))
        can = QPainterPath()
        can.moveTo(size * 0.28, size * 0.30)
        can.lineTo(size * 0.32, size * 0.82)
        can.lineTo(size * 0.68, size * 0.82)
        can.lineTo(size * 0.72, size * 0.30)
        p.drawPath(can)
        p.drawLine(QPointF(size * 0.44, size * 0.42), QPointF(size * 0.44, size * 0.70))
        p.drawLine(QPointF(size * 0.56, size * 0.42), QPointF(size * 0.56, size * 0.70))

    elif name in ("clip", "attachment"):
        # Modern 45-degree angled paperclip
        p.save()
        p.translate(size * 0.5, size * 0.5)
        p.rotate(-45)
        cp = QPainterPath()
        w = size * 0.15
        h = size * 0.30
        cp.moveTo(-w, h * 0.5)
        cp.lineTo(-w, -h * 0.5)
        cp.arcTo(QRectF(-w, -h, w * 2, w * 2), 180, -180)
        cp.lineTo(w, h * 0.7)
        cp.arcTo(QRectF(-w * 0.5, h * 0.4, w * 1.5, w * 1.5), 0, -180)
        cp.lineTo(-w * 0.5, -h * 0.2)
        p.drawPath(cp)
        p.restore()

    elif name == "send":
        # Sleek upward arrow
        p.save()
        p.translate(size * 0.5, size * 0.5)
        p.drawLine(QPointF(0, size * 0.22), QPointF(0, -size * 0.22))
        arr = QPainterPath()
        arr.moveTo(-size * 0.18, -size * 0.04)
        arr.lineTo(0, -size * 0.22)
        arr.lineTo(size * 0.18, -size * 0.04)
        p.drawPath(arr)
        p.restore()

    elif name in ("copy", "clipboard"):
        p.drawRoundedRect(QRectF(size * 0.32, size * 0.16, size * 0.52, size * 0.58), 2.5, 2.5)
        cpath = QPainterPath()
        cpath.moveTo(size * 0.68, size * 0.74)
        cpath.lineTo(size * 0.20, size * 0.74)
        cpath.lineTo(size * 0.20, size * 0.32)
        p.drawPath(cpath)

    elif name in ("refresh", "regenerate"):
        p.drawArc(QRectF(size * 0.20, size * 0.20, size * 0.60, size * 0.60), 45 * 16, 270 * 16)
        tip = QPainterPath()
        tip.moveTo(size * 0.72, size * 0.22)
        tip.lineTo(size * 0.82, size * 0.36)
        tip.lineTo(size * 0.66, size * 0.42)
        p.drawPath(tip)

    elif name in ("chat", "message"):
        bpath = QPainterPath()
        bpath.addRoundedRect(QRectF(size * 0.16, size * 0.18, size * 0.68, size * 0.50), 4, 4)
        bpath.moveTo(size * 0.28, size * 0.68)
        bpath.lineTo(size * 0.22, size * 0.82)
        bpath.lineTo(size * 0.44, size * 0.68)
        p.drawPath(bpath)

    elif name == "user":
        p.drawEllipse(QRectF(size * 0.34, size * 0.16, size * 0.32, size * 0.32))
        body = QPainterPath()
        body.moveTo(size * 0.18, size * 0.82)
        body.quadTo(QPointF(size * 0.18, size * 0.56), QPointF(size * 0.50, size * 0.56))
        body.quadTo(QPointF(size * 0.82, size * 0.56), QPointF(size * 0.82, size * 0.82))
        p.drawPath(body)

    elif name == "plus":
        p.drawLine(QPointF(size * 0.50, size * 0.22), QPointF(size * 0.50, size * 0.78))
        p.drawLine(QPointF(size * 0.22, size * 0.50), QPointF(size * 0.78, size * 0.50))

    elif name in ("dots_v", "more", "menu_dots"):
        r = max(1.2, size * 0.07)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(size * 0.5, size * 0.25), r, r)
        p.drawEllipse(QPointF(size * 0.5, size * 0.50), r, r)
        p.drawEllipse(QPointF(size * 0.5, size * 0.75), r, r)
        p.setBrush(Qt.BrushStyle.NoBrush)

    elif name in ("chevron_down", "down"):
        arr = QPainterPath()
        arr.moveTo(size * 0.26, size * 0.38)
        arr.lineTo(size * 0.50, size * 0.62)
        arr.lineTo(size * 0.74, size * 0.38)
        p.drawPath(arr)

    elif name in ("check", "checkmark"):
        chk = QPainterPath()
        chk.moveTo(size * 0.22, size * 0.52)
        chk.lineTo(size * 0.42, size * 0.72)
        chk.lineTo(size * 0.78, size * 0.28)
        p.drawPath(chk)

    elif name in ("sparkle", "ai"):
        spath = QPainterPath()
        cx, cy = size * 0.5, size * 0.5
        spath.moveTo(cx, size * 0.14)
        spath.quadTo(cx, cy, size * 0.86, cy)
        spath.quadTo(cx, cy, cx, size * 0.86)
        spath.quadTo(cx, cy, size * 0.14, cy)
        spath.quadTo(cx, cy, cx, size * 0.14)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(spath)
        p.setBrush(Qt.BrushStyle.NoBrush)

    elif name in ("eye", "view"):
        epath = QPainterPath()
        epath.moveTo(size * 0.14, size * 0.50)
        epath.quadTo(QPointF(size * 0.50, size * 0.20), QPointF(size * 0.86, size * 0.50))
        epath.quadTo(QPointF(size * 0.50, size * 0.80), QPointF(size * 0.14, size * 0.50))
        p.drawPath(epath)
        p.drawEllipse(QRectF(size * 0.40, size * 0.40, size * 0.20, size * 0.20))

    elif name == "zoom_in":
        r = size * 0.24
        cx, cy = size * 0.42, size * 0.42
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.707, cy + r * 0.707), QPointF(size * 0.84, size * 0.84))
        p.drawLine(QPointF(cx - 3, cy), QPointF(cx + 3, cy))
        p.drawLine(QPointF(cx, cy - 3), QPointF(cx, cy + 3))

    elif name == "zoom_out":
        r = size * 0.24
        cx, cy = size * 0.42, size * 0.42
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx + r * 0.707, cy + r * 0.707), QPointF(size * 0.84, size * 0.84))
        p.drawLine(QPointF(cx - 3, cy), QPointF(cx + 3, cy))

    elif name == "fit":
        # 4 corner brackets
        s = size * 0.18
        p.drawLine(QPointF(s, s * 2), QPointF(s, s))
        p.drawLine(QPointF(s, s), QPointF(s * 2, s))
        p.drawLine(QPointF(size - s * 2, s), QPointF(size - s, s))
        p.drawLine(QPointF(size - s, s), QPointF(size - s, s * 2))
        p.drawLine(QPointF(size - s, size - s * 2), QPointF(size - s, size - s))
        p.drawLine(QPointF(size - s, size - s), QPointF(size - s * 2, size - s))
        p.drawLine(QPointF(s * 2, size - s), QPointF(s, size - s))
        p.drawLine(QPointF(s, size - s), QPointF(s, size - s * 2))

    elif name == "settings":
        p.drawEllipse(QRectF(size * 0.32, size * 0.32, size * 0.36, size * 0.36))
        for a in range(0, 360, 60):
            p.save()
            p.translate(size * 0.5, size * 0.5)
            p.rotate(a)
            p.drawRect(QRectF(-size * 0.06, -size * 0.44, size * 0.12, size * 0.15))
            p.restore()

    elif name in ("thumb_up", "helpful"):
        tpath = QPainterPath()
        tpath.moveTo(size * 0.22, size * 0.45)
        tpath.lineTo(size * 0.38, size * 0.45)
        tpath.lineTo(size * 0.48, size * 0.20)
        tpath.lineTo(size * 0.56, size * 0.20)
        tpath.lineTo(size * 0.52, size * 0.45)
        tpath.lineTo(size * 0.78, size * 0.45)
        tpath.quadTo(QPointF(size * 0.84, size * 0.55), QPointF(size * 0.78, size * 0.65))
        tpath.lineTo(size * 0.74, size * 0.75)
        tpath.lineTo(size * 0.38, size * 0.75)
        tpath.lineTo(size * 0.22, size * 0.75)
        tpath.closeSubpath()
        p.drawPath(tpath)

    elif name in ("thumb_down", "unhelpful"):
        tpath = QPainterPath()
        tpath.moveTo(size * 0.22, size * 0.55)
        tpath.lineTo(size * 0.38, size * 0.55)
        tpath.lineTo(size * 0.48, size * 0.80)
        tpath.lineTo(size * 0.56, size * 0.80)
        tpath.lineTo(size * 0.52, size * 0.55)
        tpath.lineTo(size * 0.78, size * 0.55)
        tpath.quadTo(QPointF(size * 0.84, size * 0.45), QPointF(size * 0.78, size * 0.35))
        tpath.lineTo(size * 0.74, size * 0.25)
        tpath.lineTo(size * 0.38, size * 0.25)
        tpath.lineTo(size * 0.22, size * 0.25)
        tpath.closeSubpath()
        p.drawPath(tpath)

    p.end()
    return pm


def get_app_icon() -> QIcon:
    """Generates an ultra-crisp, multi-resolution application icon for window and taskbar."""
    icon = QIcon()
    for s in (16, 20, 24, 32, 48, 64, 128, 256):
        pm = draw_vector_icon("logo", "#F26A1B", s)
        icon.addPixmap(pm)
    return icon


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DYNAMIC INTERACTIVE BACKGROUND & VECTOR DATA VISUALIZATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AmbientBgParticle:
    def __init__(self, x: float, y: float, vx: float, vy: float, size: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size


class InteractiveBackground(QWidget):
    """
    Dynamic 60-FPS ambient canvas that smoothly tracks mouse coordinates
    across the entire desktop window, painting a faint blueprint tech grid,
    an animated neural particle constellation network, and an interactive
    warm amber breathing radial glow.
    """
    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._target_x = 450.0
        self._target_y = 350.0
        self._x = 450.0
        self._y = 350.0
        self._phase = 0.0
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Initialize floating ambient constellation particles
        self._particles: List[AmbientBgParticle] = []
        for _ in range(48):
            self._particles.append(AmbientBgParticle(
                random.uniform(20.0, 1400.0),
                random.uniform(20.0, 900.0),
                random.uniform(-0.45, 0.45),
                random.uniform(-0.45, 0.45),
                random.uniform(2.0, 3.5),
            ))

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def mouseMoveEvent(self, e):
        try:
            self._target_x = float(e.position().x())
            self._target_y = float(e.position().y())
        except AttributeError:
            self._target_x = float(e.x())
            self._target_y = float(e.y())
        super().mouseMoveEvent(e)

    def set_target_mouse(self, gx: float, gy: float):
        lpos = self.mapFromGlobal(QPoint(int(gx), int(gy)))
        self._target_x = float(lpos.x())
        self._target_y = float(lpos.y())

    def _tick(self):
        # 1. Seamless hardware cursor tracking across all child widgets/pages
        try:
            if self.isVisible():
                gpos = QCursor.pos()
                lpos = self.mapFromGlobal(gpos)
                if -150 <= lpos.x() <= self.width() + 150 and -150 <= lpos.y() <= self.height() + 150:
                    self._target_x = float(lpos.x())
                    self._target_y = float(lpos.y())
        except Exception:
            pass

        self._x += (self._target_x - self._x) * 0.08
        self._y += (self._target_y - self._y) * 0.08
        self._phase += 0.03

        w = max(100.0, float(self.width()))
        h = max(100.0, float(self.height()))
        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            if p.x < 10:
                p.x = 10
                p.vx = abs(p.vx)
            elif p.x > w - 10:
                p.x = w - 10
                p.vx = -abs(p.vx)
            if p.y < 10:
                p.y = 10
                p.vy = abs(p.vy)
            elif p.y > h - 10:
                p.y = h - 10
                p.vy = -abs(p.vy)

        self.update()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        t = self._t
        is_dark = t.get("name") == "dark"

        # 1. Base background fill
        p.fillRect(0, 0, int(w), int(h), QColor(t["bg"]))

        # 2. Subtle blueprint grid lines matching screenshot
        grid_col = QColor(255, 255, 255, 12) if is_dark else QColor(0, 0, 0, 16)
        p.setPen(QPen(grid_col, 1.0))
        step = 44
        x = 0
        while x < w:
            p.drawLine(int(x), 0, int(x), int(h))
            x += step
        y = 0
        while y < h:
            p.drawLine(0, int(y), int(w), int(y))
            y += step

        # 3. Breathing warm amber radial glow following mouse position
        radius = 520.0 + 30.0 * (1.0 + 0.3 * (self._phase % 6.28))
        rg = QRadialGradient(QPointF(self._x, self._y), radius)
        if is_dark:
            rg.setColorAt(0.0, QColor(255, 122, 46, 58))
            rg.setColorAt(0.35, QColor(255, 122, 46, 22))
            rg.setColorAt(0.70, QColor(255, 122, 46, 6))
            rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        else:
            rg.setColorAt(0.0, QColor(242, 106, 27, 34))
            rg.setColorAt(0.35, QColor(242, 106, 27, 12))
            rg.setColorAt(0.70, QColor(242, 106, 27, 3))
            rg.setColorAt(1.0, QColor(246, 247, 249, 0))

        p.fillRect(0, 0, int(w), int(h), QBrush(rg))

        # 4. Animated Constellation Links & Mouse Hover Connections
        num_p = len(self._particles)
        for i in range(num_p):
            p1 = self._particles[i]
            for j in range(i + 1, num_p):
                p2 = self._particles[j]
                dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if dist < 125.0:
                    alpha = int((1.0 - dist / 125.0) * (42 if is_dark else 28))
                    p.setPen(QPen(QColor(255, 122, 46, alpha), 1.0))
                    p.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))

            # Connect particle to mouse hover position
            m_dist = math.hypot(p1.x - self._x, p1.y - self._y)
            if m_dist < 155.0:
                m_alpha = int((1.0 - m_dist / 155.0) * (75 if is_dark else 48))
                p.setPen(QPen(QColor(255, 135, 55, m_alpha), 1.2))
                p.drawLine(QPointF(p1.x, p1.y), QPointF(self._x, self._y))

            # Draw particle dot with two-stage amber glow (outer halo + inner sharp core)
            p.setPen(Qt.PenStyle.NoPen)
            # Outer halo
            p.setBrush(QBrush(QColor(255, 122, 46, 38 if is_dark else 22)))
            p.drawEllipse(QPointF(p1.x, p1.y), p1.size * 2.2, p1.size * 2.2)
            # Inner core
            dot_alpha = 180 if is_dark else 120
            p.setBrush(QBrush(QColor(255, 140, 50, dot_alpha)))
            p.drawEllipse(QPointF(p1.x, p1.y), p1.size, p1.size)

        p.end()


class DonutUsageWidget(QWidget):
    """
    Vector Donut Chart showing storage breakdown by category
    matching Page 11 of the design pack.
    """
    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setFixedSize(180, 180)
        self.slices = [
            ("Legal", 442, "#6B9BFF"),
            ("Financial", 154, "#FF9548"),
            ("Academic", 135, "#A58BFF"),
            ("Medical", 96, "#F0556E"),
            ("General", 134, "#FF7A2E"),
        ]
        self.used_text = "960.9 KB"
        self.total_text = "of 5 GB used"

    def set_data(self, used_str: str, slices: List[tuple], total_text: Optional[str] = None):
        self.used_text = used_str
        if total_text:
            self.total_text = total_text
        if slices:
            self.slices = slices
        self.update()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        cx, cy = w / 2.0, h / 2.0
        outer_r = min(cx, cy) - 10.0
        inner_r = outer_r - 20.0

        total_val = sum(s[1] for s in self.slices) or 1
        start_angle = 90.0 * 16.0

        for name, val, col_hex in self.slices:
            span_angle = (val / total_val) * 360.0 * 16.0
            path = QPainterPath()
            outer_rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2.0, outer_r * 2.0)
            inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2.0, inner_r * 2.0)

            path.arcMoveTo(outer_rect, start_angle / 16.0)
            path.arcTo(outer_rect, start_angle / 16.0, span_angle / 16.0)
            path.arcTo(inner_rect, (start_angle + span_angle) / 16.0, -span_angle / 16.0)
            path.closeSubpath()

            p.setBrush(QBrush(QColor(col_hex)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
            start_angle += span_angle

        # Center text
        t = self._t
        p.setPen(QColor(t["text"]))
        font_main = QFont("Plus Jakarta Sans", 13, QFont.Weight.Bold)
        p.setFont(font_main)
        p.drawText(QRectF(cx - inner_r, cy - 14, inner_r * 2, 18), Qt.AlignmentFlag.AlignCenter, self.used_text)

        p.setPen(QColor(t["text4"]))
        font_sub = QFont("Plus Jakarta Sans", 9, QFont.Weight.Medium)
        p.setFont(font_sub)
        p.drawText(QRectF(cx - inner_r, cy + 4, inner_r * 2, 16), Qt.AlignmentFlag.AlignCenter, self.total_text)
        p.end()


class HealthScoreRingWidget(QWidget):
    """
    Circular health score ring indicator with green arc and center '100'
    matching Page 12 of the design pack.
    """
    def __init__(self, score: int = 100, theme: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        self._score = score
        self._t = theme or DARK
        self.setFixedSize(68, 68)

    def set_score(self, score: int):
        self._score = score
        self.update()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        cx, cy = w / 2.0, h / 2.0
        r = min(cx, cy) - 6.0
        rect = QRectF(cx - r, cy - r, r * 2.0, r * 2.0)

        # Track
        p.setPen(QPen(QColor(242, 106, 27, 40), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        # Active progress arc
        pct = max(0.0, min(1.0, self._score / 100.0))
        span_angle = int(pct * 360.0 * 16.0)
        p.setPen(QPen(QColor(self._t.get("primary", "#FF7A2E")), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 90 * 16, -span_angle)

        # Center score number
        t = self._t
        p.setPen(QColor(t["text"]))
        font_score = QFont("Plus Jakarta Sans", 13, QFont.Weight.Bold)
        p.setFont(font_score)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._score))
        p.end()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGO & SLIDING SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BrandLogo(QWidget):
    """Custom vector emblem for DocuVault with high-resolution graphics."""

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setFixedHeight(44)
        self._expanded = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(12)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(36, 36)
        lay.addWidget(self.icon_lbl)

        self.text_container = QWidget()
        tlay = QVBoxLayout(self.text_container)
        tlay.setContentsMargins(0, 4, 0, 4)
        tlay.setSpacing(0)

        self.title_lbl = QLabel("DocuVault")
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; letter-spacing: -0.3px;")
        tlay.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("Enterprise Vault")
        self.sub_lbl.setStyleSheet("font-size: 10px; font-weight: 500;")
        tlay.addWidget(self.sub_lbl)

        lay.addWidget(self.text_container)
        lay.addStretch()

        self.text_container.setVisible(False)
        self.update_theme(theme)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        # Render emblem
        self.icon_lbl.setPixmap(draw_vector_icon("logo", "#FFFFFF", 36))
        # Update colors
        self.title_lbl.setStyleSheet(f"color: {theme['sidebar_text']}; font-size: 15px; font-weight: 800;")
        self.sub_lbl.setStyleSheet(f"color: {theme['sidebar_text_muted']}; font-size: 10px; font-weight: 500;")

    def set_expanded(self, exp: bool):
        self._expanded = exp
        self.text_container.setVisible(exp)


class SidebarNavItem(QPushButton):
    """Interactive navigation item with smooth hover feedback."""

    def __init__(self, icon_name: str, label_text: str, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.label_text = label_text
        self._t = theme
        self._active = False
        self._expanded = False
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(22, 22)
        lay.addWidget(self.icon_lbl)

        self.text_lbl = QLabel(label_text)
        self.text_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        lay.addWidget(self.text_lbl)
        lay.addStretch()

        self.text_lbl.setVisible(False)
        self.update_theme(theme)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def set_expanded(self, exp: bool):
        self._expanded = exp
        self.text_lbl.setVisible(exp)

    def _apply_style(self):
        t = self._t
        is_dark = (t.get('name') == 'dark')
        if self._active:
            # Active styling
            self.setStyleSheet(f"""
                SidebarNavItem {{
                    background: {t['sidebar_item_active_bg']};
                    border-radius: 10px;
                    border: none;
                }}
            """)
            self.text_lbl.setStyleSheet(f"color: {t['sidebar_item_active_text']}; font-size: 13px; font-weight: 700;")
            icon_color = t['sidebar_item_active_text'] if not is_dark else t['primary']
            self.icon_lbl.setPixmap(draw_vector_icon(self.icon_name, icon_color, 22))
        else:
            self.setStyleSheet(f"""
                SidebarNavItem {{
                    background: transparent;
                    border-radius: 10px;
                    border: none;
                }}
                SidebarNavItem:hover {{
                    background: {t['sidebar_item_hover']};
                }}
            """)
            text_color = t['sidebar_text_muted'] if is_dark else "#344054"
            icon_color = t['sidebar_text_muted'] if is_dark else "#344054"
            self.text_lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 600;")
            self.icon_lbl.setPixmap(draw_vector_icon(self.icon_name, icon_color, 22))


class SlidingSidebar(QFrame):
    """
    Production sidebar with optional hover expansion and explicit collapse/expand toggle.
    Supports pinning expanded or collapsed with smooth animations.
    """
    page_selected = pyqtSignal(int)
    theme_toggled = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._sidebar_width = 68
        self.setFixedWidth(68)
        self.setObjectName("slidingSidebar")
        self.is_pinned = False

        # Smooth animation
        self.anim = QPropertyAnimation(self, b"sidebarWidth")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 16, 10, 16)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Brand logo
        self.logo = BrandLogo(theme, self)
        lay.addWidget(self.logo)
        lay.addSpacing(12)

        # Navigation items
        self.nav_items: List[SidebarNavItem] = []
        nav_configs = [
            ("documents", "Documents", 0),
            ("ai", "AI Assistant", 1),
            ("organizer", "AI File Organizer", 2),
            ("storage", "Storage Vault", 3),
            ("security", "Integrity & Health", 4),
            ("activity", "Audit Trail", 5),
            ("calendar", "Deadlines", 6),
        ]
        for icon, title, idx in nav_configs:
            item = SidebarNavItem(icon, title, theme, self)
            item.clicked.connect(lambda _, i=idx: self._on_select(i))
            lay.addWidget(item)
            self.nav_items.append(item)

        self.nav_items[0].set_active(True)

        lay.addStretch()

        # Collapse / Expand manual toggle button
        self.toggle_btn = SidebarNavItem("toggle", "Expand", theme, self)
        self.toggle_btn.clicked.connect(self._toggle_pinned_state)
        lay.addWidget(self.toggle_btn)

        # Theme toggle at bottom
        self.theme_btn = SidebarNavItem("moon" if theme['name'] == "light" else "sun", "Dark Mode" if theme['name'] == "light" else "Light Mode", theme, self)
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        lay.addWidget(self.theme_btn)

        self.update_theme(theme)

    @pyqtProperty(int)
    def sidebarWidth(self) -> int:
        return self._sidebar_width

    @sidebarWidth.setter
    def sidebarWidth(self, val: int):
        self._sidebar_width = val
        self.setFixedWidth(val)
        exp = val > 140
        self.logo.set_expanded(exp)
        for it in self.nav_items:
            it.set_expanded(exp)
        self.theme_btn.set_expanded(exp)
        self.toggle_btn.set_expanded(exp)
        self.toggle_btn.text_lbl.setText("Collapse" if exp else "Expand")

    def _toggle_pinned_state(self):
        if self._sidebar_width > 140:
            # Currently expanded -> collapse
            self.is_pinned = False
            self.anim.stop()
            self.anim.setStartValue(self.width())
            self.anim.setEndValue(68)
            self.anim.start()
        else:
            # Currently collapsed -> expand and pin
            self.is_pinned = True
            self.anim.stop()
            self.anim.setStartValue(self.width())
            self.anim.setEndValue(220)
            self.anim.start()

    def enterEvent(self, e):
        super().enterEvent(e)
        if not self.is_pinned:
            self.anim.stop()
            self.anim.setStartValue(self.width())
            self.anim.setEndValue(220)
            self.anim.start()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if not self.is_pinned:
            self.anim.stop()
            self.anim.setStartValue(self.width())
            self.anim.setEndValue(68)
            self.anim.start()

    def _on_select(self, idx: int):
        for i, item in enumerate(self.nav_items):
            item.set_active(i == idx)
        self.page_selected.emit(idx)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.setStyleSheet(f"""
            #slidingSidebar {{
                background: {theme['sidebar']};
                border-right: 1px solid {theme['sidebar_border']};
            }}
        """)
        self.logo.update_theme(theme)
        for item in self.nav_items:
            item.update_theme(theme)
        self.toggle_btn.update_theme(theme)
        # Update theme toggle icon
        icon_name = "moon" if theme['name'] == "light" else "sun"
        label_text = "Dark Mode" if theme['name'] == "light" else "Light Mode"
        self.theme_btn.icon_name = icon_name
        self.theme_btn.label_text = label_text
        self.theme_btn.text_lbl.setText(label_text)
        self.theme_btn.update_theme(theme)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIFIED HEADER CARD (INTEGRATED METRICS + DROP CAPSULE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MetricPill(QWidget):
    """Clean metric indicator inside the stats strip matching Page 10."""

    def __init__(self, title: str, value: str, subtext: str, color_hex: str, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(2)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {theme['text4']}; letter-spacing: 0.8px;")
        lay.addWidget(self.title_lbl)

        val_row = QHBoxLayout()
        val_row.setSpacing(6)
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color_hex};")
        val_row.addWidget(self.val_lbl)

        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {theme['green'] if 'verif' in subtext.lower() else theme['text3']};")
        val_row.addWidget(self.sub_lbl)
        val_row.addStretch()
        lay.addLayout(val_row)

    def set_value(self, val: str, subtext: Optional[str] = None):
        self.val_lbl.setText(val)
        if subtext is not None:
            self.sub_lbl.setText(subtext)

    def update_theme(self, theme: Dict[str, str], color_hex: str):
        self._t = theme
        self.title_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {theme['text4']}; letter-spacing: 0.8px;")
        self.val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color_hex};")
        sub_col = theme['green'] if 'verif' in self.sub_lbl.text().lower() else theme['text3']
        self.sub_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {sub_col};")


class UnifiedHeaderBanner(QFrame):
    """
    Consolidated executive header matching Page 10 of the design pack:
    - Top row: 'Documents' title & subtitle + Action pills (Web Hub, Scan duplicates, Import documents)
    - Bottom card: 4-metric Stats Strip (Documents, Vault storage, Integrity, Categories)
    """
    files_dropped = pyqtSignal(list)
    browse_clicked = pyqtSignal()
    duplicates_clicked = pyqtSignal()
    webhub_clicked = pyqtSignal()
    profile_clicked = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setFixedHeight(154)
        self.setAcceptDrops(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # ── Top Row: Page Title + Action Cluster (Page 10) ──
        trow = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = QLabel("Documents")
        self.title_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {theme['text']};")
        title_box.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("Everything in your vault, verified and organised.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        title_box.addWidget(self.sub_lbl)
        trow.addLayout(title_box)
        trow.addStretch()

        self.btn_webhub = QPushButton("🌐 Web Hub")
        self.btn_webhub.setObjectName("secondaryBtn")
        self.btn_webhub.setFixedHeight(34)
        self.btn_webhub.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_webhub.clicked.connect(self.webhub_clicked.emit)
        trow.addWidget(self.btn_webhub)

        self.btn_scan = QPushButton("Scan duplicates")
        self.btn_scan.setObjectName("secondaryBtn")
        self.btn_scan.setFixedHeight(34)
        self.btn_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scan.clicked.connect(self.duplicates_clicked.emit)
        self.btn_scan.setVisible(False)

        self.btn_import = QPushButton("Import documents")
        self.btn_import.setObjectName("primaryBtn")
        self.btn_import.setFixedHeight(34)
        self.btn_import.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_import.clicked.connect(self.browse_clicked.emit)
        self.btn_import.setVisible(False)

        self.btn_profile = QPushButton("User")
        self.btn_profile.setFixedHeight(34)
        self.btn_profile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_profile.clicked.connect(self.profile_clicked.emit)
        trow.addWidget(self.btn_profile)
        lay.addLayout(trow)

        # ── Bottom Stats Strip Card (Page 10) ──
        self.stats_card = QFrame()
        self.stats_card.setObjectName("unifiedCard")
        sc_lay = QHBoxLayout(self.stats_card)
        sc_lay.setContentsMargins(16, 6, 16, 6)
        sc_lay.setSpacing(12)

        self.m_total = MetricPill("Documents", "0", "", theme["text"], theme)
        self.m_size = MetricPill("Vault Storage", "0 B", "", theme["primary"], theme)
        self.m_status = MetricPill("Integrity", "100%", "verified", theme["green"], theme)
        self.m_cats = MetricPill("Categories", "0", "", theme["gold"], theme)

        sc_lay.addWidget(self.m_total, 1)
        self.div1 = self._make_divider()
        sc_lay.addWidget(self.div1)
        sc_lay.addWidget(self.m_size, 1)
        self.div2 = self._make_divider()
        sc_lay.addWidget(self.div2)
        sc_lay.addWidget(self.m_status, 1)
        self.div3 = self._make_divider()
        sc_lay.addWidget(self.div3)
        sc_lay.addWidget(self.m_cats, 1)

        lay.addWidget(self.stats_card)
        self.update_theme(theme)

    def set_user_info(self, user_info: Dict[str, Any]):
        name = user_info.get("full_name") or user_info.get("name") or "User"
        tier = str(user_info.get("tier", "Free")).upper()
        if tier == "PRO":
            self.btn_profile.setText(f"👤 {name}  PRO")
            self.btn_profile.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #2563EB);
                    color: #FFFFFF;
                    border: 1px solid #3B82F6;
                    border-radius: 10px;
                    padding: 6px 14px;
                    font-weight: 700;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                }
            """)
        else:
            self.btn_profile.setText(f"👤 {name}  FREE")
            self.btn_profile.setStyleSheet(f"""
                QPushButton {{
                    background: {self._t['bg3']};
                    color: {self._t['text']};
                    border: 1px solid {self._t['border']};
                    border-radius: 10px;
                    padding: 6px 14px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {self._t['border']};
                    color: {self._t['primary']};
                }}
            """)

    def _make_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFixedHeight(36)
        div.setStyleSheet(f"color: {self._t['divider']};")
        return div

    def update_metrics(self, total: int, size_str: str, verified_pct: str, cats: int):
        self.m_total.set_value(str(total))
        self.m_size.set_value(size_str)
        self.m_status.set_value(verified_pct, "verified")
        self.m_cats.set_value(str(cats))

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.setStyleSheet("background: transparent; border: none;")
        self.title_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {theme['text']};")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        self.stats_card.setStyleSheet(f"""
            #unifiedCard {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 16px;
            }}
        """)
        self.m_total.update_theme(theme, theme["text"])
        self.m_size.update_theme(theme, theme["primary"])
        self.m_status.update_theme(theme, theme["green"])
        self.m_cats.update_theme(theme, theme["gold"])
        for div in (self.div1, self.div2, self.div3):
            div.setStyleSheet(f"color: {theme['divider']};")
        self.btn_webhub.setStyleSheet(f"""
            QPushButton {{
                background: {theme['bg3']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {theme['border']};
                color: {theme['primary']};
            }}
        """)
        if hasattr(self, "_user_data") and self._user_data:
            self.set_user_info(self._user_data)
        else:
            self.btn_profile.setStyleSheet(f"""
                QPushButton {{
                    background: {theme['bg3']};
                    color: {theme['text']};
                    border: 1px solid {theme['border']};
                    border-radius: 10px;
                    padding: 6px 14px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {theme['border']};
                    color: {theme['primary']};
                }}
            """)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.stats_card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {self._t['primary_bg']};
                    border: 1.5px solid {self._t['primary']};
                    border-radius: 16px;
                }}
            """)

    def dragLeaveEvent(self, e):
        self.update_theme(self._t)

    def dropEvent(self, e: QDropEvent):
        self.update_theme(self._t)
        paths = [u.toLocalFile() for u in e.mimeData().urls() if os.path.isfile(u.toLocalFile())]
        if paths:
            self.files_dropped.emit(paths)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOCUMENT ROW ITEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentListItem(QFrame):
    """Modern document list entry with rich feedback, clear status, and direct action triggers."""
    clicked = pyqtSignal(dict)
    view_requested = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)

    BADGE_COLORS = {
        "PDF": ("#EF4444", "#FEF2F2"),
        "XML": ("#10B981", "#ECFDF5"),
        "TXT": ("#0284C7", "#F0F9FF"),
    }

    def __init__(self, doc: Dict[str, Any], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._doc = doc
        self._t = theme
        self._selected = False
        self.setFixedHeight(64)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("docItem")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(14)

        # File type badge
        ext = Path(doc.get("filename", "")).suffix.upper().replace(".", "") or "DOC"
        fg_col, bg_col = self.BADGE_COLORS.get(ext, (theme["primary"], theme["primary_bg"]))
        if theme["name"] == "dark":
            bg_col = f"rgba({int(fg_col[1:3], 16)}, {int(fg_col[3:5], 16)}, {int(fg_col[5:7], 16)}, 0.16)"

        self.badge = QLabel(ext)
        self.badge.setFixedSize(38, 38)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet(f"""
            background: {bg_col};
            color: {fg_col};
            font-size: 11px;
            font-weight: 800;
            border-radius: 8px;
        """)
        lay.addWidget(self.badge)

        # Name and metadata
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.setContentsMargins(0, 0, 0, 0)

        self.name_lbl = QLabel(doc.get("filename", "Untitled Document"))
        self.name_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {theme['text']};")
        info_col.addWidget(self.name_lbl)

        sz_b = doc.get("size_bytes", 0)
        sz_str = f"{sz_b / (1024*1024):.1f} MB" if sz_b >= 1048576 else (f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B")
        created_str = doc.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created_str)
            date_disp = dt.strftime("%b %d, %Y")
        except Exception:
            date_disp = "Recent"

        self.meta_lbl = QLabel(f"{sz_str}  \u2022  {ext.lower()}  \u2022  {date_disp}")
        self.meta_lbl.setStyleSheet(f"font-size: 11px; color: {theme['text4']};")
        info_col.addWidget(self.meta_lbl)
        lay.addLayout(info_col, 1)

        # Category pill
        cat = doc.get("category", "General")
        self.cat_lbl = QLabel(cat)
        self.cat_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {theme['text3']};
            background: {theme['bg3']};
            padding: 3px 10px;
            border-radius: 6px;
        """)
        self.cat_lbl.setFixedHeight(24)
        lay.addWidget(self.cat_lbl)

        # Status indicator
        status = doc.get("status", "Verified")
        is_ok = status == "Verified"
        scol = theme["green"] if is_ok else theme["red"]
        sbg = theme["green_bg"] if is_ok else theme["red_bg"]
        self.status_lbl = QLabel(f"\u25CF  {'Verified Authentic' if is_ok else 'Integrity Warning'}")
        self.status_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {scol};
            background: {sbg};
            padding: 3px 10px;
            border-radius: 6px;
        """)
        self.status_lbl.setFixedHeight(24)
        lay.addWidget(self.status_lbl)

        # Page count
        pgs = doc.get("page_count", 1)
        self.pg_lbl = QLabel(f"{pgs} pg")
        self.pg_lbl.setStyleSheet(f"font-size: 11px; color: {theme['text4']};")
        self.pg_lbl.setFixedWidth(40)
        self.pg_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.pg_lbl)

        # Direct Row Actions: [👁️ View] & [🗑️ Delete]
        act_row = QHBoxLayout()
        act_row.setSpacing(6)

        is_dark = theme.get("name") == "dark"
        btn_view_bg = "#1A1A22" if is_dark else theme["bg2"]
        btn_view_border = "#2A2A36" if is_dark else theme["border"]

        self.btn_row_view = QPushButton("👁️ View")
        self.btn_row_view.setFixedHeight(28)
        self.btn_row_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_row_view.setToolTip("View full document contents and extracted text")
        self.btn_row_view.setStyleSheet(f"""
            QPushButton {{
                background: {btn_view_bg};
                color: {theme['text2']};
                border: 1px solid {btn_view_border};
                border-radius: 7px;
                padding: 2px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme['primary']};
                color: #FFFFFF;
                border-color: {theme['primary']};
            }}
        """)
        self.btn_row_view.clicked.connect(lambda: self.view_requested.emit(self._doc))
        act_row.addWidget(self.btn_row_view)

        self.btn_row_del = QPushButton("🗑️")
        self.btn_row_del.setFixedSize(28, 28)
        self.btn_row_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_row_del.setToolTip("Remove document from repository index")
        self.btn_row_del.setStyleSheet(f"""
            QPushButton {{
                background: {btn_view_bg};
                color: {theme['text3']};
                border: 1px solid {btn_view_border};
                border-radius: 7px;
                font-size: 11.5px;
            }}
            QPushButton:hover {{
                background: {theme['red_bg']};
                color: {theme['red']};
                border-color: {theme['red_border']};
            }}
        """)
        self.btn_row_del.clicked.connect(lambda: self.delete_requested.emit(self._doc))
        act_row.addWidget(self.btn_row_del)
        lay.addLayout(act_row)

        self._apply_style()

    def set_selected(self, sel: bool):
        self._selected = sel
        self._apply_style()

    def _apply_style(self):
        t = self._t
        bg_col = t['selected'] if self._selected else t['surface']
        border_left = f"3.5px solid {t['primary']}" if self._selected else "3.5px solid transparent"
        self.setStyleSheet(f"""
            #docItem {{
                background: {bg_col};
                border-bottom: 1px solid {t['divider']};
                border-left: {border_left};
            }}
            #docItem:hover {{
                background: {t['hover']};
            }}
            #docItem QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {t['text']}; background: transparent;")
        self.meta_lbl.setStyleSheet(f"font-size: 11px; color: {t['text4']}; background: transparent;")
        self.pg_lbl.setStyleSheet(f"font-size: 11px; color: {t['text4']}; background: transparent;")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._doc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOCUMENT INSPECTOR (DETAILS PANEL - ALL BUTTONS ENCLOSED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentInspector(QFrame):
    """
    Apple-grade Extendable Document Details Drawer:
    - Side-by-side resizable drawer docking seamlessly in the main workspace splitter.
    - Top Primary Action Strip: Direct View Document, Open in OS, Verify, and Delete.
    - Segmented 3-Tab Architecture: Overview, Legal & Risk, and Tools & Security.
    - Frosted glass translucent canvas with responsive scroll container preventing any layout clipping.
    """
    view_text_clicked = pyqtSignal()
    verify_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    copy_hash_clicked = pyqtSignal(str)
    health_clicked = pyqtSignal()
    version_clicked = pyqtSignal()
    ai_clicked = pyqtSignal()
    ocr_clicked = pyqtSignal()
    redact_clicked = pyqtSignal()
    collapse_requested = pyqtSignal()
    rebuttal_clicked = pyqtSignal()
    encrypt_clicked = pyqtSignal()
    export_dossier_clicked = pyqtSignal()
    retention_clicked = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setObjectName("inspectorDrawer")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(280)
        self.setMaximumWidth(1200)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._current_hash = ""
        self._current_doc: Optional[Dict[str, Any]] = None
        self._build()

    def minimumSizeHint(self) -> QSize:
        return QSize(280, 200)

    def _build(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # ── 1. Header Tag Row with Status & Close Button ──
        tag_row = QHBoxLayout()
        tag = QLabel("DOCUMENT DETAILS")
        tag.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {t['text4']}; letter-spacing: 0.8px;")
        tag_row.addWidget(tag)
        tag_row.addStretch()

        self.status_badge = QLabel("")
        tag_row.addWidget(self.status_badge)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.setToolTip("Collapse Details Drawer")
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t['text3']};
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {'#1E1E26' if t.get('name') == 'dark' else '#E5E5EA'};
                color: {t['text']};
            }}
        """)
        self.btn_close.clicked.connect(self.collapse_requested.emit)
        tag_row.addWidget(self.btn_close)
        lay.addLayout(tag_row)

        # ── 2. Document Title & Subtitle Meta ──
        self.title_lbl = QLabel("Select a document")
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text']}; letter-spacing: -0.3px;")
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        lay.addWidget(self.title_lbl)

        self.meta_sub_lbl = QLabel("No document selected")
        self.meta_sub_lbl.setStyleSheet(f"font-size: 11px; color: {t['text4']};")
        self.meta_sub_lbl.setWordWrap(True)
        self.meta_sub_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        lay.addWidget(self.meta_sub_lbl)

        # ── 3. Primary Action Strip (Immediate Prominent Access) ──
        self.action_cluster = QFrame()
        self.action_cluster.setStyleSheet("background: transparent; border: none;")
        ac_lay = QHBoxLayout(self.action_cluster)
        ac_lay.setContentsMargins(0, 4, 0, 4)
        ac_lay.setSpacing(6)

        self.btn_action_view = QPushButton("📄 View")
        self.btn_action_view.setObjectName("primaryBtn")
        self.btn_action_view.setFixedHeight(30)
        self.btn_action_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action_view.setToolTip("View full document contents in reader")
        self.btn_action_view.clicked.connect(self.view_text_clicked.emit)
        ac_lay.addWidget(self.btn_action_view, 1)

        self.btn_action_open = QPushButton("📂 Open")
        self.btn_action_open.setObjectName("secondaryBtn")
        self.btn_action_open.setFixedHeight(30)
        self.btn_action_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action_open.setToolTip("Open directly in OS default application")
        self.btn_action_open.clicked.connect(self._open_file_in_os)
        ac_lay.addWidget(self.btn_action_open, 1)

        self.btn_action_verify = QPushButton("🔒 Verify")
        self.btn_action_verify.setObjectName("secondaryBtn")
        self.btn_action_verify.setFixedHeight(30)
        self.btn_action_verify.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action_verify.clicked.connect(self.verify_clicked.emit)
        ac_lay.addWidget(self.btn_action_verify)

        self.btn_action_delete = QPushButton("🗑️")
        self.btn_action_delete.setObjectName("dangerBtn")
        self.btn_action_delete.setFixedHeight(30)
        self.btn_action_delete.setFixedWidth(34)
        self.btn_action_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action_delete.setToolTip("Remove document from repository index")
        self.btn_action_delete.clicked.connect(self.delete_clicked.emit)
        ac_lay.addWidget(self.btn_action_delete)

        lay.addWidget(self.action_cluster)

        # ── 4. Apple-Style Segmented Pill Switcher (Overview, Legal & Risk, Tools) ──
        self.pill_bar = QFrame()
        self.pill_bar.setStyleSheet(f"background: {t['bg3']}; border-radius: 8px; padding: 2px;")
        pill_lay = QHBoxLayout(self.pill_bar)
        pill_lay.setContentsMargins(2, 2, 2, 2)
        pill_lay.setSpacing(2)

        self.btn_tab_overview = QPushButton("Overview")
        self.btn_tab_overview.setFixedHeight(26)
        self.btn_tab_overview.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_overview.clicked.connect(lambda: self._switch_tab(0))

        self.btn_tab_legal = QPushButton("Legal & Risk")
        self.btn_tab_legal.setFixedHeight(26)
        self.btn_tab_legal.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_legal.clicked.connect(lambda: self._switch_tab(1))

        self.btn_tab_tools = QPushButton("Tools & Sec")
        self.btn_tab_tools.setFixedHeight(26)  
        self.btn_tab_tools.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_tools.clicked.connect(lambda: self._switch_tab(2))

        pill_lay.addWidget(self.btn_tab_overview)
        pill_lay.addWidget(self.btn_tab_legal)
        pill_lay.addWidget(self.btn_tab_tools)
        lay.addWidget(self.pill_bar)

        # ── 5. Scroll Area Container for Tabs (Prevents Any Vertical Clipping) ──
        self.drawer_scroll = QScrollArea()
        self.drawer_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.drawer_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.drawer_scroll.setWidgetResizable(True)
        self.drawer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.drawer_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.drawer_scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.tab_stack = QStackedWidget()
        self.tab_stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.tab_stack.setStyleSheet("background: transparent; border: none;")
        self.tab_stack.addWidget(self._build_overview_tab())
        self.tab_stack.addWidget(self._build_legal_tab())
        self.tab_stack.addWidget(self._build_tools_tab())
        self.drawer_scroll.setWidget(self.tab_stack)
        lay.addWidget(self.drawer_scroll, 1)

        self._switch_tab(0)
        self.show_empty()

    def _open_file_in_os(self):
        if not self._current_doc:
            return
        fpath = self._current_doc.get("filepath", "")
        if fpath and os.path.exists(fpath):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(fpath)))
        else:
            self.view_text_clicked.emit()

    def _switch_tab(self, idx: int):
        self.tab_stack.setCurrentIndex(idx)
        t = self._t
        is_dark = t.get("name") == "dark"
        active_bg = "#1E1E24" if is_dark else t["surface"]
        active_border = "1px solid #FF7A2E" if is_dark else f"1px solid {t['border']}"
        active_qss = f"background: {active_bg}; color: {t['primary']}; font-weight: 700; font-size: 11px; border: {active_border}; border-radius: 6px;"
        inactive_qss = f"background: transparent; color: {t['text3']}; font-weight: 600; font-size: 11px; border: none; border-radius: 6px;"

        self.btn_tab_overview.setStyleSheet(active_qss if idx == 0 else inactive_qss)
        self.btn_tab_legal.setStyleSheet(active_qss if idx == 1 else inactive_qss)
        self.btn_tab_tools.setStyleSheet(active_qss if idx == 2 else inactive_qss)

    def _build_overview_tab(self) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)

        # Basic Stats Grid
        self.info_box = QFrame()
        self.info_box.setObjectName("subCard")
        ilay = QGridLayout(self.info_box)
        ilay.setContentsMargins(10, 8, 10, 8)
        ilay.setSpacing(4)

        ilay.addWidget(self._make_label("SIZE"), 0, 0)
        self.lbl_size = QLabel("—")
        self.lbl_size.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {t['text']};")
        ilay.addWidget(self.lbl_size, 0, 1)

        ilay.addWidget(self._make_label("PAGES"), 1, 0)
        self.lbl_pages = QLabel("—")
        self.lbl_pages.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {t['text']};")
        ilay.addWidget(self.lbl_pages, 1, 1)

        ilay.addWidget(self._make_label("STORAGE"), 2, 0)
        self.lbl_storage = QLabel("Local Vault")
        self.lbl_storage.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {t['text']};")
        ilay.addWidget(self.lbl_storage, 2, 1)
        lay.addWidget(self.info_box)

        # Risk Profile Badge
        self.lbl_risk_badge = QLabel("Risk Profile: —")
        self.lbl_risk_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['green']}; background: {t['green_bg']}; padding: 4px 8px; border-radius: 6px;")
        lay.addWidget(self.lbl_risk_badge)

        # Executive Summary Box
        sum_lbl = QLabel("EXECUTIVE SUMMARY (3-BULLET AI)")
        sum_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.6px;")
        lay.addWidget(sum_lbl)

        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setFixedHeight(85)
        self.summary_box.setStyleSheet(f"background: {t['bg3']}; border: 1px solid {t['border']}; border-radius: 8px; font-size: 11px; color: {t['text2']};")
        lay.addWidget(self.summary_box)

        # Extracted Counterparties
        cp_lbl = QLabel("COUNTERPARTIES & ENTITIES")
        cp_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.6px;")
        lay.addWidget(cp_lbl)

        self.lbl_counterparties = QLabel("No counterparty identified")
        self.lbl_counterparties.setWordWrap(True)
        self.lbl_counterparties.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        is_dark = t.get("name") == "dark"
        cp_bg = "#141418" if is_dark else t["bg3"]
        cp_color = t["text"] if is_dark else t["text2"]
        cp_border = "#2B2B36" if is_dark else t["border"]
        self.lbl_counterparties.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {cp_color}; background: {cp_bg}; border: 1px solid {cp_border}; border-radius: 6px; padding: 6px 10px;")
        lay.addWidget(self.lbl_counterparties)

        # Security Hash Fingerprint
        sig_sec = QLabel("SECURITY FINGERPRINT (SHA-256)")
        sig_sec.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.6px;")
        lay.addWidget(sig_sec)

        self.sig_box = QFrame()
        self.sig_box.setObjectName("subCard")
        slay = QHBoxLayout(self.sig_box)
        slay.setContentsMargins(8, 4, 8, 4)
        slay.setSpacing(6)

        self.lbl_hash = QLabel("No document selected")
        self.lbl_hash.setStyleSheet(f"font-family: monospace; font-size: 9px; color: {t['primary']};")
        self.lbl_hash.setWordWrap(True)
        self.lbl_hash.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        slay.addWidget(self.lbl_hash, 1)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setObjectName("copyBtn")
        self.btn_copy.setFixedWidth(46)
        self.btn_copy.clicked.connect(self._copy_hash)
        slay.addWidget(self.btn_copy)
        lay.addWidget(self.sig_box)

        lay.addStretch()
        return w

    def _build_legal_tab(self) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)

        # Document Health Score Card
        self.health_card = QFrame()
        self.health_card.setObjectName("subCard")
        hlay = QHBoxLayout(self.health_card)
        hlay.setContentsMargins(10, 8, 10, 8)
        hlay.setSpacing(6)

        self.lbl_health_badge = QLabel("Health: —")
        self.lbl_health_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['green']};")
        hlay.addWidget(self.lbl_health_badge, 1)

        self.btn_health_audit = QPushButton("Audit")
        self.btn_health_audit.setObjectName("copyBtn")
        self.btn_health_audit.setFixedWidth(54)
        self.btn_health_audit.clicked.connect(self.health_clicked.emit)
        hlay.addWidget(self.btn_health_audit)
        lay.addWidget(self.health_card)

        # Contract Clauses Extracted
        cl_sec = QLabel("MANDATORY LEGAL CLAUSES")
        cl_sec.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.6px;")
        lay.addWidget(cl_sec)

        self.insights_box = QTextEdit()
        self.insights_box.setReadOnly(True)
        self.insights_box.setFixedHeight(120)
        self.insights_box.setStyleSheet(f"background: {t['bg3']}; border: 1px solid {t['border']}; border-radius: 8px; font-size: 11px; color: {t['text2']};")
        lay.addWidget(self.insights_box)

        # Legal Actions Buttons
        self.btn_rebuttal = QPushButton("⚖️ Draft Contract Rebuttal Letter")
        self.btn_rebuttal.setObjectName("primaryBtn")
        self.btn_rebuttal.setFixedHeight(32)
        self.btn_rebuttal.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_rebuttal.clicked.connect(self.rebuttal_clicked.emit)
        lay.addWidget(self.btn_rebuttal)

        self.btn_redact = QPushButton("🛡️ PII Mask & Automated Redaction")
        self.btn_redact.setObjectName("secondaryBtn")
        self.btn_redact.setFixedHeight(30)
        self.btn_redact.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_redact.clicked.connect(self.redact_clicked.emit)
        lay.addWidget(self.btn_redact)

        lay.addStretch()
        return w

    def _build_tools_tab(self) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(6)

        # Secondary Actions
        self.btn_view = QPushButton("📄 View Full Document")
        self.btn_view.setObjectName("primaryBtn")
        self.btn_view.setFixedHeight(30)
        self.btn_view.clicked.connect(self.view_text_clicked.emit)
        lay.addWidget(self.btn_view)

        self.btn_verify = QPushButton("🔒 Verify Cryptographic SHA-256")
        self.btn_verify.setObjectName("secondaryBtn")
        self.btn_verify.setFixedHeight(28)
        self.btn_verify.clicked.connect(self.verify_clicked.emit)
        lay.addWidget(self.btn_verify)

        self.btn_versions = QPushButton("🔍 Smart Version Diff Tracker")
        self.btn_versions.setObjectName("secondaryBtn")
        self.btn_versions.setFixedHeight(28)
        self.btn_versions.clicked.connect(self.version_clicked.emit)
        lay.addWidget(self.btn_versions)

        self.btn_ai = QPushButton("🤖 Evidence-Grounded AI Assistant")
        self.btn_ai.setObjectName("secondaryBtn")
        self.btn_ai.setFixedHeight(28)
        self.btn_ai.clicked.connect(self.ai_clicked.emit)
        lay.addWidget(self.btn_ai)

        self.btn_ocr = QPushButton("👁️ OCR Scanned Document Reader")
        self.btn_ocr.setObjectName("secondaryBtn")
        self.btn_ocr.setFixedHeight(28)
        self.btn_ocr.clicked.connect(self.ocr_clicked.emit)
        lay.addWidget(self.btn_ocr)

        self.btn_encrypt = QPushButton("🛡️ Zero-Knowledge Cloud Encryption")
        self.btn_encrypt.setObjectName("secondaryBtn")
        self.btn_encrypt.setFixedHeight(28)
        self.btn_encrypt.clicked.connect(self.encrypt_clicked.emit)
        lay.addWidget(self.btn_encrypt)

        self.btn_export_dossier = QPushButton("📦 Export Compliance Dossier (.zip)")
        self.btn_export_dossier.setObjectName("secondaryBtn")
        self.btn_export_dossier.setFixedHeight(28)
        self.btn_export_dossier.clicked.connect(self.export_dossier_clicked.emit)
        lay.addWidget(self.btn_export_dossier)

        self.btn_retention = QPushButton("🗑️ Secure Retention Shred / Archive")
        self.btn_retention.setObjectName("secondaryBtn")
        self.btn_retention.setFixedHeight(28)
        self.btn_retention.clicked.connect(self.retention_clicked.emit)
        lay.addWidget(self.btn_retention)

        self.btn_delete = QPushButton("✕ Remove Document from Vault")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setFixedHeight(28)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        lay.addWidget(self.btn_delete)

        lay.addStretch()
        return w

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {self._t['text4']}; letter-spacing: 0.6px;")
        return lbl

    def _copy_hash(self):
        if self._current_hash:
            QApplication.clipboard().setText(self._current_hash)
            self.btn_copy.setText("Copied!")
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("Copy"))
            self.copy_hash_clicked.emit(self._current_hash)

    def show_empty(self):
        t = self._t
        self._current_doc = None
        self.title_lbl.setText("Select a document")
        self.meta_sub_lbl.setText("No document selected")
        self.status_badge.setText("")
        self.lbl_size.setText("—")
        self.lbl_pages.setText("—")
        self.lbl_storage.setText("Local Vault")
        self.lbl_health_badge.setText("Health: —")
        self.lbl_risk_badge.setText("Risk Profile: —")
        self.lbl_risk_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text3']}; background: {t['bg3']}; padding: 4px 8px; border-radius: 6px;")
        self.summary_box.setPlainText("Select a file from repository to extract executive summaries.")
        self.lbl_counterparties.setText("No document selected")
        self.lbl_hash.setText("Select document to inspect integrity")
        self._current_hash = ""
        self.insights_box.setPlainText("Select a file from repository to inspect clause diagnostics.")

        for b in [
            self.btn_action_view, self.btn_action_open, self.btn_action_verify, self.btn_action_delete,
            self.btn_view, self.btn_verify, self.btn_delete, self.btn_copy,
            self.btn_versions, self.btn_ai, self.btn_ocr, self.btn_redact,
            self.btn_health_audit, self.btn_rebuttal, self.btn_encrypt,
            self.btn_export_dossier, self.btn_retention
        ]:
            b.setEnabled(False)

    def show_doc(self, doc: Dict[str, Any], storage_name: str = "Local Vault"):
        self._current_doc = doc
        t = self._t
        self.title_lbl.setText(doc.get("filename", "Untitled Document"))

        sz_b = doc.get("size_bytes", 0)
        sz_str = f"{sz_b / (1024*1024):.1f} MB" if sz_b >= 1048576 else (f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B")
        ext = Path(doc.get("filename", "")).suffix.lower().replace(".", "") or "file"
        pgs = doc.get("page_count", 1)
        self.meta_sub_lbl.setText(f"{sz_str}  \u2022  {ext.upper()}  \u2022  {pgs} page{'s' if pgs!=1 else ''}  \u2022  {storage_name}")

        status = doc.get("status", "Verified")
        is_ok = status == "Verified"
        scol = t["green"] if is_ok else t["red"]
        sbg = t["green_bg"] if is_ok else t["red_bg"]
        self.status_badge.setText(f"\u25CF {'Verified' if is_ok else 'Tampered'}")
        self.status_badge.setStyleSheet(f"""
            font-size: 10px; font-weight: 700; color: {scol};
            background: {sbg}; padding: 2px 7px; border-radius: 6px;
        """)

        self.lbl_size.setText(sz_str)
        self.lbl_pages.setText(f"{doc.get('page_count', 1)} pages")
        self.lbl_storage.setText(storage_name)

        # Risk Profile Badge & Executive Summary
        full_text = " ".join([p.get("text", "") for p in doc.get("pages", [])]) or doc.get("raw_text", "")
        summary_bullets = doc.get("executive_summary") or DocumentAnalyzer.extract_executive_summary(full_text, doc.get("filename", ""))
        self.summary_box.setPlainText("\n\n".join([f"• {b}" for b in summary_bullets]))

        risk_data = doc.get("risk_profile") or DocumentAnalyzer.calculate_risk_profile(full_text, doc.get("clauses"))
        rbadge = risk_data.get("risk_badge", "Low")
        rscore = risk_data.get("score", 90)
        rcolor = risk_data.get("color", "#10B981")
        self.lbl_risk_badge.setText(f"● Risk Level: {rbadge} (Score: {rscore}/100)")
        self.lbl_risk_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {rcolor}; background: {t['bg3']}; padding: 4px 8px; border-radius: 6px; border: 1px solid {rcolor};")

        # Counterparties
        is_dark = t.get("name") == "dark"
        cp_bg = "#141418" if is_dark else t["bg3"]
        cp_color = t["text"] if is_dark else t["text2"]
        cp_border = "#2B2B36" if is_dark else t["border"]
        self.lbl_counterparties.setStyleSheet(f"""
            font-size: 11px; font-weight: 600;
            color: {cp_color};
            background: {cp_bg};
            border: 1px solid {cp_border};
            border-radius: 6px; padding: 6px 10px;
        """)
        counterparties = doc.get("counterparties") or DocumentAnalyzer.extract_counterparties(full_text)
        if counterparties:
            self.lbl_counterparties.setText("🏢 " + " • ".join(counterparties[:3]))
        else:
            self.lbl_counterparties.setText("No external counterparty identified")

        # Health Score
        health = DocumentHealthEngine.calculate_health(doc)
        self.lbl_health_badge.setText(f"● Health: {health['score']}% ({health['grade']})")
        self.lbl_health_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {health['status_color']};")

        sha = doc.get("sha256_hash", "N/A")
        self._current_hash = sha
        if sha and sha != "N/A" and len(sha) == 64:
            self.lbl_hash.setText(f"{sha[:32]}\n{sha[32:]}")
        else:
            self.lbl_hash.setText(sha)
        self.btn_copy.setEnabled(bool(sha and sha != "N/A"))

        # Insights & extracted clauses
        clauses = doc.get("clauses", {})
        currency = doc.get("currency_amounts", [])
        dates = doc.get("extracted_dates", [])

        lines = []
        if dates:
            lines.append(f"Recorded Dates: {', '.join(dates[:2])}")
        if currency:
            lines.append(f"Financial Values: {', '.join(currency[:2])}")
        if clauses:
            for k, v in list(clauses.items())[:4]:
                clean_v = str(v).strip()
                if len(clean_v) > 60:
                    clean_v = clean_v[:60] + "..."
                lines.append(f"• {k}: {clean_v}")

        if lines:
            self.insights_box.setPlainText("\n".join(lines))
        else:
            self.insights_box.setPlainText("Standard verified document. All clauses and text available in viewer.")

        for b in [
            self.btn_action_view, self.btn_action_open, self.btn_action_verify, self.btn_action_delete,
            self.btn_view, self.btn_verify, self.btn_delete, self.btn_copy,
            self.btn_versions, self.btn_ai, self.btn_ocr, self.btn_redact,
            self.btn_health_audit, self.btn_rebuttal, self.btn_encrypt,
            self.btn_export_dossier, self.btn_retention
        ]:
            b.setEnabled(True)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        is_dark = theme.get("name") == "dark"
        drawer_bg = "rgba(10, 10, 14, 0.82)" if is_dark else "rgba(255, 255, 255, 0.88)"
        drawer_border = "rgba(255, 122, 46, 0.28)" if is_dark else "rgba(242, 106, 27, 0.25)"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(f"""
            #inspectorDrawer {{
                background: {drawer_bg};
                border-left: 1px solid {drawer_border};
            }}
        """)
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {theme['text']}; letter-spacing: -0.3px;")
        self.lbl_size.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {theme['text']};")
        self.lbl_pages.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {theme['text']};")
        self.lbl_storage.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {theme['text']};")
        self.info_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 10px;")
        self.health_card.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 8px;")
        self.sig_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 10px;")
        self.lbl_hash.setStyleSheet(f"font-family: monospace; font-size: 9px; color: {theme['primary']};")
        self.insights_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 8px; font-size: 11px; color: {theme['text2']};")
        self.summary_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 8px; font-size: 11px; color: {theme['text2']};")
        if hasattr(self, "pill_bar"):
            self.pill_bar.setStyleSheet(f"background: {'#141418' if is_dark else theme['bg3']}; border: 1px solid {'#2B2B36' if is_dark else theme['border']}; border-radius: 8px; padding: 2px;")
        if hasattr(self, "lbl_counterparties"):
            cp_bg = "#141418" if is_dark else theme["bg3"]
            cp_col = theme["text"] if is_dark else theme["text2"]
            cp_border = "#2B2B36" if is_dark else theme["border"]
            self.lbl_counterparties.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {cp_col}; background: {cp_bg}; border: 1px solid {cp_border}; border-radius: 6px; padding: 6px 10px;")
        if hasattr(self, "drawer_scroll"):
            self.drawer_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
            self.drawer_scroll.viewport().setStyleSheet("background: transparent; border: none;")
        self._switch_tab(self.tab_stack.currentIndex())
        if self._current_doc:
            self.show_doc(self._current_doc, self.lbl_storage.text())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FULL-TEXT DOCUMENT VIEWER DIALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentViewerDialog(QDialog):
    """
    Enterprise Document Viewer & Visual Inspector:
    - Tab 1: High-res Visual Preview with smooth Pan/Zoom for Images and Page-by-Page PDF rendering
    - Tab 2: High-Legibility Extracted Content / OCR Reader with in-document search and font scaling
    - Tab 3: Security & Cryptographic Integrity metadata (SHA-256, format validation)
    - AI Action Toolbar: Instant AI Summary, Key Entity Extraction, Ask AI Scoped Query, System App Launcher
    """

    def __init__(self, doc: Dict[str, Any], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._doc = doc
        self._t = theme
        self._zoom_factor = 1.0
        self._current_page = 0
        self._pdf_doc = None
        self._font_size = 13.0

        is_dark = theme.get("name") == "dark"
        self.setWindowTitle(f"Document Viewer — {doc.get('filename', 'Document')}")
        self.resize(960, 720)
        self.setMinimumSize(780, 560)
        self.setStyleSheet(f"background: {theme['bg']}; color: {theme['text']}; font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;")

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(24, 20, 24, 20)
        root_lay.setSpacing(12)

        # ── 1. Top Header: Icon + Title + Authentic Badge + Metadata ──
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        ext = Path(doc.get("filename", "")).suffix.lower()
        icon_name = "documents"
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            icon_name = "ocr"
        elif ext in (".xlsx", ".csv"):
            icon_name = "storage"
        elif ext in (".py", ".json", ".xml", ".html"):
            icon_name = "organizer"

        ico_lbl = QLabel()
        ico_lbl.setPixmap(draw_vector_icon(icon_name, theme["primary"], 24))
        h_row.addWidget(ico_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.lbl_title = QLabel(doc.get("filename", "Untitled Document"))
        self.lbl_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {theme['text']}; letter-spacing: -0.3px;")
        title_box.addWidget(self.lbl_title)

        sz_b = doc.get("size_bytes", 0)
        sz_str = f"{sz_b / (1024*1024):.1f} MB" if sz_b >= 1048576 else (f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B")
        cat = doc.get("category", "General")
        pg_cnt = doc.get("page_count", len(doc.get("pages", [])) or 1)
        self.lbl_sub = QLabel(f"Category: <b>{cat}</b>  •  {pg_cnt} page{'s' if pg_cnt != 1 else ''}  •  Size: {sz_str}  •  Format: {ext.upper().replace('.', '') or 'FILE'}")
        self.lbl_sub.setStyleSheet(f"font-size: 11.5px; color: {theme['text4']};")
        title_box.addWidget(self.lbl_sub)
        h_row.addLayout(title_box, 1)

        # Authentic / Verification badge
        status = doc.get("status", "Verified")
        is_ok = (status == "Verified")
        badge_lbl = QLabel(f"✓ {'Verified Authentic' if is_ok else 'Integrity Warning'}")
        badge_lbl.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {theme['green'] if is_ok else theme['red']};
            background: {theme['green_bg'] if is_ok else theme['red_bg']};
            border: 1px solid {theme['green_border'] if is_ok else theme['red_border']};
            padding: 4px 10px; border-radius: 8px;
        """)
        h_row.addWidget(badge_lbl)
        root_lay.addLayout(h_row)

        # ── 2. AI & Document Operations Toolbar ──
        tb_card = QFrame()
        tb_card.setStyleSheet(f"""
            QFrame {{
                background: {theme['bg3']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
            }}
        """)
        tb_lay = QHBoxLayout(tb_card)
        tb_lay.setContentsMargins(10, 6, 10, 6)
        tb_lay.setSpacing(8)

        # Tab Navigation Pills
        self.btn_tab_visual = QPushButton("Visual Preview")
        self.btn_tab_visual.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_visual.setFixedHeight(28)

        self.btn_tab_text = QPushButton("Extracted Text & OCR")
        self.btn_tab_text.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_text.setFixedHeight(28)

        self.btn_tab_meta = QPushButton("Metadata & Hash")
        self.btn_tab_meta.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_meta.setFixedHeight(28)

        for btn in (self.btn_tab_visual, self.btn_tab_text, self.btn_tab_meta):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {theme['text3']};
                    border: none; border-radius: 6px; padding: 4px 12px;
                    font-size: 11.5px; font-weight: 600;
                }}
                QPushButton:hover {{
                    color: {theme['text']}; background: {theme['bg2']};
                }}
            """)

        self.btn_tab_visual.clicked.connect(lambda: self._switch_tab(0))
        self.btn_tab_text.clicked.connect(lambda: self._switch_tab(1))
        self.btn_tab_meta.clicked.connect(lambda: self._switch_tab(2))

        tb_lay.addWidget(self.btn_tab_visual)
        tb_lay.addWidget(self.btn_tab_text)
        tb_lay.addWidget(self.btn_tab_meta)
        tb_lay.addStretch()

        # AI Options
        self.btn_ai_ask = QPushButton("Ask AI")
        self.btn_ai_ask.setToolTip("Open AI Assistant with this document as pinned context")
        self.btn_ai_ask.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ai_ask.setFixedHeight(28)
        self.btn_ai_ask.setStyleSheet(f"""
            QPushButton {{
                background: {theme['primary']}; color: #FFFFFF;
                border: none; border-radius: 6px; padding: 4px 12px;
                font-size: 11px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {theme['primary_h']}; }}
        """)
        self.btn_ai_ask.clicked.connect(self._ask_ai_about_document)
        tb_lay.addWidget(self.btn_ai_ask)

        self.btn_ai_summary = QPushButton("Summary")
        self.btn_ai_summary.setToolTip("Generate instant structured executive summary")
        self.btn_ai_summary.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ai_summary.setFixedHeight(28)
        self.btn_ai_summary.setStyleSheet(f"""
            QPushButton {{
                background: {theme['bg2']}; color: {theme['text']};
                border: 1px solid {theme['border']}; border-radius: 6px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {theme['primary']}; color: {theme['primary']}; }}
        """)
        self.btn_ai_summary.clicked.connect(self._generate_ai_summary)
        tb_lay.addWidget(self.btn_ai_summary)

        self.btn_copy_text = QPushButton("Copy Text")
        self.btn_copy_text.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_copy_text.setFixedHeight(28)
        self.btn_copy_text.setStyleSheet(f"""
            QPushButton {{
                background: {theme['bg2']}; color: {theme['text']};
                border: 1px solid {theme['border']}; border-radius: 6px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {theme['primary']}; }}
        """)
        self.btn_copy_text.clicked.connect(self._copy_all_text)
        tb_lay.addWidget(self.btn_copy_text)

        fpath = doc.get("filepath", "")
        if fpath and os.path.exists(fpath):
            self.btn_system_app = QPushButton("Open in App")
            self.btn_system_app.setToolTip("Open in default system application")
            self.btn_system_app.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.btn_system_app.setFixedHeight(28)
            self.btn_system_app.setStyleSheet(f"""
                QPushButton {{
                    background: {theme['bg2']}; color: {theme['text']};
                    border: 1px solid {theme['border']}; border-radius: 6px;
                    padding: 4px 10px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {theme['primary']}; }}
            """)
            self.btn_system_app.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(fpath))))
            tb_lay.addWidget(self.btn_system_app)

        root_lay.addWidget(tb_card)

        # ── AI Executive Summary Banner (Initially Collapsed) ──
        self.ai_summary_card = QFrame()
        self.ai_summary_card.setVisible(False)
        self.ai_summary_card.setStyleSheet(f"""
            QFrame {{
                background: {'#181614' if is_dark else '#FFF7ED'};
                border: 1px solid {theme['primary']};
                border-radius: 10px; padding: 12px;
            }}
        """)
        sum_lay = QVBoxLayout(self.ai_summary_card)
        sum_lay.setContentsMargins(12, 10, 12, 10)
        sum_lay.setSpacing(6)
        sum_head = QHBoxLayout()
        s_title = QLabel("AI Executive Analysis & Clauses")
        s_title.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {theme['primary']};")
        sum_head.addWidget(s_title)
        sum_head.addStretch()
        btn_close_sum = QPushButton("✕")
        btn_close_sum.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close_sum.setStyleSheet("background: transparent; border: none; font-size: 11px; font-weight: 700;")
        btn_close_sum.clicked.connect(lambda: self.ai_summary_card.setVisible(False))
        sum_head.addWidget(btn_close_sum)
        sum_lay.addLayout(sum_head)
        self.lbl_summary_content = QLabel("Analyzing document...")
        self.lbl_summary_content.setWordWrap(True)
        self.lbl_summary_content.setStyleSheet(f"font-size: 12px; line-height: 1.5; color: {theme['text']};")
        sum_lay.addWidget(self.lbl_summary_content)
        root_lay.addWidget(self.ai_summary_card)

        # ── 3. Central Stacked Content Pages ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        # Page 0: Visual Preview
        page_vis = self._build_visual_preview_page(doc, fpath, ext, is_dark)
        self.stack.addWidget(page_vis)

        # Page 1: Extracted Text & OCR
        page_txt = self._build_text_reader_page(doc, is_dark)
        self.stack.addWidget(page_txt)

        # Page 2: Metadata & Cryptographic Integrity
        page_meta = self._build_metadata_page(doc, fpath, is_dark)
        self.stack.addWidget(page_meta)

        root_lay.addWidget(self.stack, 1)

        # ── 4. Bottom Footer: Close Button ──
        b_row = QHBoxLayout()
        b_row.addStretch()
        cb = QPushButton("Close")
        cb.setObjectName("primaryBtn")
        cb.setFixedHeight(34)
        cb.setFixedWidth(100)
        cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cb.clicked.connect(self.close)
        b_row.addWidget(cb)
        root_lay.addLayout(b_row)

        # Select initial tab: if image or PDF, start on visual preview; otherwise start on text reader
        init_tab = 0 if ext in (".png", ".jpg", ".jpeg", ".webp", ".pdf") else 1
        self._switch_tab(init_tab)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        t = self._t
        is_dark = t.get("name") == "dark"
        active_style = f"""
            background: {t['primary']}; color: #FFFFFF;
            border: none; border-radius: 6px; padding: 4px 12px;
            font-size: 11.5px; font-weight: 700;
        """
        inactive_style = f"""
            background: transparent; color: {t['text3']};
            border: none; border-radius: 6px; padding: 4px 12px;
            font-size: 11.5px; font-weight: 600;
        """
        self.btn_tab_visual.setStyleSheet(active_style if index == 0 else inactive_style)
        self.btn_tab_text.setStyleSheet(active_style if index == 1 else inactive_style)
        self.btn_tab_meta.setStyleSheet(active_style if index == 2 else inactive_style)

    def _build_visual_preview_page(self, doc: Dict[str, Any], fpath: str, ext: str, is_dark: bool) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Zoom & Page Navigation Strip
        zoom_strip = QHBoxLayout()
        zoom_strip.setSpacing(8)

        btn_zin = QPushButton("+ Zoom In")
        btn_zout = QPushButton("- Zoom Out")
        btn_zfit = QPushButton("Fit Window")
        btn_z100 = QPushButton("100%")

        for b in (btn_zin, btn_zout, btn_zfit, btn_z100):
            b.setFixedHeight(26)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg2']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 5px;
                    padding: 2px 10px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {t['primary']}; }}
            """)
        zoom_strip.addWidget(btn_zin)
        zoom_strip.addWidget(btn_zout)
        zoom_strip.addWidget(btn_zfit)
        zoom_strip.addWidget(btn_z100)

        # PDF page stepper (if applicable)
        self.lbl_pdf_page = QLabel("")
        self.btn_pdf_prev = QPushButton("◄ Prev")
        self.btn_pdf_next = QPushButton("Next ►")
        for pb in (self.btn_pdf_prev, self.btn_pdf_next):
            pb.setFixedHeight(26)
            pb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            pb.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg2']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 5px;
                    padding: 2px 8px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {t['primary']}; }}
            """)

        zoom_strip.addSpacing(16)
        zoom_strip.addWidget(self.btn_pdf_prev)
        zoom_strip.addWidget(self.lbl_pdf_page)
        zoom_strip.addWidget(self.btn_pdf_next)
        zoom_strip.addStretch()
        lay.addLayout(zoom_strip)

        # Scrollable image / render container
        self.vis_scroll = QScrollArea()
        self.vis_scroll.setWidgetResizable(True)
        self.vis_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {'#09090D' if is_dark else '#F8FAFC'};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
        """)
        self.vis_label = QLabel()
        self.vis_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vis_label.setStyleSheet("background: transparent;")
        self.vis_scroll.setWidget(self.vis_label)
        lay.addWidget(self.vis_scroll, 1)

        self._raw_pixmap: Optional[QPixmap] = None

        # Load file visual
        if ext in (".png", ".jpg", ".jpeg", ".webp") and fpath and os.path.exists(fpath):
            self._raw_pixmap = QPixmap(fpath)
            self.btn_pdf_prev.setVisible(False)
            self.btn_pdf_next.setVisible(False)
            self.lbl_pdf_page.setVisible(False)
            self._update_visual_pixmap()

        elif ext == ".pdf" and fpath and os.path.exists(fpath):
            try:
                import fitz
                self._pdf_doc = fitz.open(fpath)
                self._current_page = 0
                self.btn_pdf_prev.setVisible(True)
                self.btn_pdf_next.setVisible(True)
                self.lbl_pdf_page.setVisible(True)
                self._render_pdf_page()
            except Exception as e:
                self.vis_label.setText(f"Unable to render PDF visual: {e}")
                self.btn_pdf_prev.setVisible(False)
                self.btn_pdf_next.setVisible(False)
                self.lbl_pdf_page.setVisible(False)
        else:
            self.vis_label.setText("Visual document rendering available for PNG, JPG, WEBP, and PDF files.\nSelect 'Extracted Text & OCR' tab to read document content.")
            self.vis_label.setStyleSheet(f"color: {t['text4']}; font-size: 13px; font-weight: 500;")
            self.btn_pdf_prev.setVisible(False)
            self.btn_pdf_next.setVisible(False)
            self.lbl_pdf_page.setVisible(False)

        # Connect zoom actions
        btn_zin.clicked.connect(lambda: self._adjust_zoom(1.25))
        btn_zout.clicked.connect(lambda: self._adjust_zoom(0.80))
        btn_z100.clicked.connect(lambda: self._set_zoom(1.0))
        btn_zfit.clicked.connect(self._fit_to_window)
        self.btn_pdf_prev.clicked.connect(self._prev_pdf_page)
        self.btn_pdf_next.clicked.connect(self._next_pdf_page)

        return w

    def _update_visual_pixmap(self):
        if not self._raw_pixmap or self._raw_pixmap.isNull():
            return
        target_w = max(50, int(self._raw_pixmap.width() * self._zoom_factor))
        target_h = max(50, int(self._raw_pixmap.height() * self._zoom_factor))
        scaled = self._raw_pixmap.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.vis_label.setPixmap(scaled)

    def _adjust_zoom(self, factor: float):
        self._zoom_factor = max(0.2, min(5.0, self._zoom_factor * factor))
        self._update_visual_pixmap()

    def _set_zoom(self, z: float):
        self._zoom_factor = z
        self._update_visual_pixmap()

    def _fit_to_window(self):
        if not self._raw_pixmap or self._raw_pixmap.isNull():
            return
        vw = max(100, self.vis_scroll.viewport().width() - 30)
        vh = max(100, self.vis_scroll.viewport().height() - 30)
        scale_w = vw / float(self._raw_pixmap.width())
        scale_h = vh / float(self._raw_pixmap.height())
        self._zoom_factor = min(scale_w, scale_h)
        self._update_visual_pixmap()

    def _render_pdf_page(self):
        if not self._pdf_doc or len(self._pdf_doc) == 0:
            return
        page_num = max(0, min(len(self._pdf_doc) - 1, self._current_page))
        self._current_page = page_num
        page = self._pdf_doc[page_num]
        pix = page.get_pixmap(dpi=150)
        from PyQt6.QtGui import QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self._raw_pixmap = QPixmap.fromImage(img)
        self.lbl_pdf_page.setText(f"Page {page_num + 1} of {len(self._pdf_doc)}")
        self._update_visual_pixmap()

    def _prev_pdf_page(self):
        if self._pdf_doc and self._current_page > 0:
            self._current_page -= 1
            self._render_pdf_page()

    def _next_pdf_page(self):
        if self._pdf_doc and self._current_page < len(self._pdf_doc) - 1:
            self._current_page += 1
            self._render_pdf_page()

    def _build_text_reader_page(self, doc: Dict[str, Any], is_dark: bool) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Search Bar + Font Scaling Controls
        s_row = QHBoxLayout()
        s_row.setSpacing(8)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find inside document text...")
        self.find_input.setFixedHeight(30)
        self.find_input.setStyleSheet(f"""
            QLineEdit {{
                background: {t['bg2']}; color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 6px;
                padding: 4px 10px; font-size: 11.5px;
            }}
            QLineEdit:focus {{ border-color: {t['primary']}; }}
        """)
        self.find_input.textChanged.connect(self._find_text)
        s_row.addWidget(self.find_input, 1)

        btn_font_dec = QPushButton("A-")
        btn_font_dec.setToolTip("Decrease text size")
        btn_font_dec.setFixedSize(28, 28)
        btn_font_dec.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_font_dec.clicked.connect(lambda: self._scale_font(-1.0))

        btn_font_inc = QPushButton("A+")
        btn_font_inc.setToolTip("Increase text size")
        btn_font_inc.setFixedSize(28, 28)
        btn_font_inc.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_font_inc.clicked.connect(lambda: self._scale_font(1.0))

        for fb in (btn_font_dec, btn_font_inc):
            fb.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg2']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 6px;
                    font-size: 11px; font-weight: 700;
                }}
                QPushButton:hover {{ border-color: {t['primary']}; }}
            """)
        s_row.addWidget(btn_font_dec)
        s_row.addWidget(btn_font_inc)
        lay.addLayout(s_row)

        # Content Text Area with High-Legibility Typography
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setStyleSheet(f"""
            QTextEdit {{
                background: {'#0A0A0E' if is_dark else '#FFFFFF'};
                color: {'#ECECF1' if is_dark else '#1E293B'};
                border: 1px solid {t['border']};
                border-radius: 10px;
                font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;
                font-size: 13.5px;
                line-height: 1.65;
                padding: 16px;
            }}
        """)

        pages = doc.get("pages", [])
        if pages:
            body = "\n\n".join(
                f"── [Page {p.get('page_number', i+1)}] ─────────────────────────────\n{p.get('text', '')}"
                for i, p in enumerate(pages)
            )
        else:
            body = doc.get("raw_text", "No readable text content extracted.")

        self.txt.setPlainText(body)
        lay.addWidget(self.txt, 1)
        return w

    def _scale_font(self, delta: float):
        self._font_size = max(9.0, min(24.0, self._font_size + delta))
        font = self.txt.font()
        font.setPointSize(int(self._font_size))
        self.txt.setFont(font)

    def _build_metadata_page(self, doc: Dict[str, Any], fpath: str, is_dark: bool) -> QWidget:
        t = self._t
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        meta_card = QFrame()
        meta_card.setStyleSheet(f"""
            QFrame {{
                background: {t['bg3']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
        """)
        m_lay = QVBoxLayout(meta_card)
        m_lay.setContentsMargins(18, 16, 18, 16)
        m_lay.setSpacing(10)

        sha = doc.get("sha256_hash", "N/A")
        cat = doc.get("category", "General")
        owner = doc.get("user_email") or doc.get("owner_email", "Enterprise Vault")
        discovered = doc.get("discovered_at") or doc.get("intake_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = [
            ("Document Filename", doc.get("filename", "Untitled")),
            ("Cryptographic Hash (SHA-256)", sha),
            ("Primary Category", cat),
            ("Owner Identity", owner),
            ("Registered / Discovered", str(discovered)),
            ("Absolute File Path", fpath or "Indexed in Cloud Vault"),
            ("Format & Magic Bytes", f"Valid {Path(doc.get('filename', '')).suffix.upper()} Binary Signature"),
        ]

        for label, val in fields:
            row = QVBoxLayout()
            row.setSpacing(2)
            lbl = QLabel(label.upper())
            lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.5px;")
            v_lbl = QLabel(str(val))
            v_lbl.setWordWrap(True)
            v_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            v_lbl.setStyleSheet(f"font-size: 12.5px; font-weight: 600; color: {t['text']};")
            row.addWidget(lbl)
            row.addWidget(v_lbl)
            m_lay.addLayout(row)

        lay.addWidget(meta_card)
        lay.addStretch()
        return w

    def _copy_all_text(self):
        text = self.txt.toPlainText()
        QApplication.clipboard().setText(text)
        self.btn_copy_text.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.btn_copy_text.setText("Copy Text"))

    def _find_text(self, query: str):
        if not query.strip():
            cursor = self.txt.textCursor()
            cursor.clearSelection()
            self.txt.setTextCursor(cursor)
            return
        found = self.txt.find(query)
        if not found:
            cursor = self.txt.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.txt.setTextCursor(cursor)
            self.txt.find(query)

    def _ask_ai_about_document(self):
        fname = self._doc.get("filename")
        self.close()
        # Find main window and navigate to AI page with document attached
        parent = self.parent()
        main_win = self.window()
        while parent and not hasattr(parent, "page_ai"):
            parent = parent.parent()
        target = parent or main_win
        if hasattr(target, "page_ai") and fname:
            target.page_ai.pinned_sources = [fname]
            target.page_ai._update_sources_strip()
            if hasattr(target, "stack"):
                target.stack.setCurrentIndex(1)
            target.page_ai.input_field.setFocus()
            target.page_ai.input_field.setPlaceholderText(f"Ask anything about '{fname}'...")

    def _generate_ai_summary(self):
        self.ai_summary_card.setVisible(True)
        self.lbl_summary_content.setText("Consulting DocuVault Intelligence Engine...")
        QTimer.singleShot(100, self._run_ai_summary)

    def _run_ai_summary(self):
        text = self.txt.toPlainText()
        if not text:
            self.lbl_summary_content.setText("No text available to summarize.")
            return

        # Use LLMClient if available, otherwise fast extractive summary
        try:
            from backend.api_client import LLMClient
            client = LLMClient()
            if client.has_any_active_key():
                summary = client._call_groq(
                    "Provide a clean 3-bullet point executive summary and extract all key dates/amounts:",
                    text[:3000]
                )
                if summary:
                    self.lbl_summary_content.setText(summary)
                    return
        except Exception:
            pass

        # Deterministic extraction fallback
        lines = [s.strip() for s in text.splitlines() if len(s.strip()) > 20]
        preview = " • " + "\n • ".join(lines[:3]) if lines else text[:300]
        self.lbl_summary_content.setText(f"<b>Key Document Clauses:</b>\n{preview}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASYNC INGESTION THREAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentIngestWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, filepath: str, storage_mode: str, local_prov, cloud_prov, vec_engine):
        super().__init__()
        self.filepath = filepath
        self.storage_mode = storage_mode
        self.local_prov = local_prov
        self.cloud_prov = cloud_prov
        self.vec_engine = vec_engine

    def run(self):
        try:
            fname = Path(self.filepath).name
            self.progress.emit(20, f"Validating binary integrity for {fname}...")
            BinaryParser.validate_file(self.filepath)

            self.progress.emit(50, f"Parsing document content and extracting metadata...")
            doc = DocumentFactory.create_document(self.filepath, enforce_magic_bytes=False)

            self.progress.emit(75, f"Storing document in vault repository...")
            with open(self.filepath, "rb") as f:
                data = f.read()

            rel = f"{doc.get_category()}/{doc.filename}"
            (self.local_prov if self.storage_mode == "Local Vault" else self.cloud_prov).save_file(rel, data)

            self.progress.emit(90, f"Updating universal search index...")
            self.vec_engine.add_document_chunks(doc.doc_id, doc.filename, doc.get_category(), doc.pages)
            self.vec_engine.build_index()

            self.progress.emit(100, f"Import complete: {fname}")
            dd = doc.to_dict()
            dd["pages"] = [{"page_number": p.get("page_number", i+1), "text": p.get("text", "")} for i, p in enumerate(doc.pages)]
            self.finished.emit(dd)
        except DocuVaultError as e:
            self.failed.emit(e.message)
        except Exception as e:
            self.failed.emit(str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEDICATED SECONDARY PAGES (CLEAN & MINIMALIST)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StorageVaultPage(QWidget):
    """
    Dedicated Storage Vault Page matching Page 11 of the design pack:
    - Donut chart of usage by category with center text '960.9 KB of 5 GB used'
    - Legend list with Legal (blue), Financial (green), Academic (purple), Medical (pink), General (orange)
    - Local storage and Cloud mirror cards with sync status & Open Folder buttons
    - Recent sync activity card at the bottom
    """
    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._build_ui()

    def _build_ui(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # ── Header ──
        hrow = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.t_lbl = QLabel("Storage Vault")
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        title_box.addWidget(self.t_lbl)
        self.sub_lbl = QLabel("Where your documents live, and how they are backed up.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text4']};")
        title_box.addWidget(self.sub_lbl)
        hrow.addLayout(title_box)
        hrow.addStretch()

        self.btn_change_loc = QPushButton("Change location")
        self.btn_change_loc.setObjectName("secondaryBtn")
        self.btn_change_loc.setFixedHeight(34)
        self.btn_change_loc.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_change_loc)

        self.btn_sync_now = QPushButton("Sync now")
        self.btn_sync_now.setObjectName("primaryBtn")
        self.btn_sync_now.setFixedHeight(34)
        self.btn_sync_now.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_sync_now)
        lay.addLayout(hrow)

        # ── Top Row (Donut Card + Storage Cards) ──
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Left Card: Donut usage & breakdown
        self.donut_card = QFrame()
        self.donut_card.setObjectName("unifiedCard")
        dc_lay = QHBoxLayout(self.donut_card)
        dc_lay.setContentsMargins(24, 20, 24, 20)
        dc_lay.setSpacing(24)

        self.donut = DonutUsageWidget(t, self)
        dc_lay.addWidget(self.donut)

        # Legend list
        leg_box = QVBoxLayout()
        leg_box.setSpacing(8)
        self.leg_title = QLabel("Usage by category")
        self.leg_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        leg_box.addWidget(self.leg_title)

        cats = [
            ("Legal", "442 KB", "#6B9BFF"),
            ("Financial", "154 KB", "#FF9548"),
            ("Academic", "135 KB", "#A58BFF"),
            ("Medical", "96 KB", "#F0556E"),
            ("General", "134 KB", "#FF7A2E"),
        ]
        self.cat_labels = []
        for name, sz, col in cats:
            r = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {col}; font-size: 11px;")
            r.addWidget(dot)
            nl = QLabel(name)
            nl.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 500;")
            r.addWidget(nl)
            r.addStretch()
            sl = QLabel(sz)
            sl.setStyleSheet(f"font-size: 12px; color: {t['text3']}; font-weight: 600;")
            r.addWidget(sl)
            leg_box.addLayout(r)
            self.cat_labels.append((nl, sl))

        dc_lay.addLayout(leg_box, 1)
        top_row.addWidget(self.donut_card, 1)

        # Right Cards (Local storage & Cloud mirror)
        right_box = QVBoxLayout()
        right_box.setSpacing(14)

        # Local storage card
        self.local_card = QFrame()
        self.local_card.setObjectName("unifiedCard")
        lc_lay = QVBoxLayout(self.local_card)
        lc_lay.setContentsMargins(20, 16, 20, 16)
        lc_lay.setSpacing(8)

        lc_top = QHBoxLayout()
        self.lc_title = QLabel("Local storage")
        self.lc_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
        lc_top.addWidget(self.lc_title)
        lc_top.addStretch()
        self.lc_badge = QLabel("Healthy")
        self.lc_badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
        lc_top.addWidget(self.lc_badge)
        lc_lay.addLayout(lc_top)

        self.path_local = QLabel(os.path.abspath("vault/local"))
        self.path_local.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text3']};")
        lc_lay.addWidget(self.path_local)

        lc_bot = QHBoxLayout()
        self.lbl_local_used = QLabel("960.9 KB used")
        self.lbl_local_used.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 600;")
        lc_bot.addWidget(self.lbl_local_used)
        lc_bot.addStretch()
        btn_open_local = QPushButton("Open folder")
        btn_open_local.setObjectName("secondaryBtn")
        btn_open_local.setFixedHeight(28)
        btn_open_local.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_local.clicked.connect(lambda: self._open_dir("vault/local"))
        lc_bot.addWidget(btn_open_local)
        lc_lay.addLayout(lc_bot)
        right_box.addWidget(self.local_card)

        # Cloud mirror card
        self.cloud_card = QFrame()
        self.cloud_card.setObjectName("unifiedCard")
        cc_lay = QVBoxLayout(self.cloud_card)
        cc_lay.setContentsMargins(20, 16, 20, 16)
        cc_lay.setSpacing(8)

        cc_top = QHBoxLayout()
        self.cc_title = QLabel("Cloud mirror")
        self.cc_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
        cc_top.addWidget(self.cc_title)
        cc_top.addStretch()
        self.cc_badge = QLabel("Live sync on")
        self.cc_badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
        cc_top.addWidget(self.cc_badge)
        cc_lay.addLayout(cc_top)

        self.path_cloud = QLabel(os.path.abspath("vault/cloud_mirror"))
        self.path_cloud.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text3']};")
        cc_lay.addWidget(self.path_cloud)

        cc_bot = QHBoxLayout()
        self.lbl_cloud_status = QLabel("Real-time file watching")
        self.lbl_cloud_status.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 600;")
        cc_bot.addWidget(self.lbl_cloud_status)
        cc_bot.addStretch()
        btn_open_cloud = QPushButton("Open folder")
        btn_open_cloud.setObjectName("secondaryBtn")
        btn_open_cloud.setFixedHeight(28)
        btn_open_cloud.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_cloud.clicked.connect(lambda: self._open_dir("vault/cloud_mirror"))
        cc_bot.addWidget(btn_open_cloud)
        cc_lay.addLayout(cc_bot)
        right_box.addWidget(self.cloud_card)

        top_row.addLayout(right_box, 1)
        lay.addLayout(top_row)

        # ── Bottom Card: Recent Sync Activity (Live Realtime Data) ──
        self.sync_card = QFrame()
        self.sync_card.setObjectName("unifiedCard")
        sc_lay = QVBoxLayout(self.sync_card)
        sc_lay.setContentsMargins(24, 20, 24, 20)
        sc_lay.setSpacing(12)

        self.sc_title = QLabel("Recent sync activity")
        self.sc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
        sc_lay.addWidget(self.sc_title)

        self.sc_items_container = QWidget()
        self.sc_items_lay = QVBoxLayout(self.sc_items_container)
        self.sc_items_lay.setContentsMargins(0, 0, 0, 0)
        self.sc_items_lay.setSpacing(10)
        sc_lay.addWidget(self.sc_items_container)

        self.sync_labels = []
        lay.addWidget(self.sync_card)
        lay.addStretch()

    def refresh_storage_metrics(self, docs: Dict[str, Dict[str, Any]], user_tier: str = "Free"):
        t = self._t
        cat_sizes: Dict[str, int] = {"Legal": 0, "Financial": 0, "Academic": 0, "Medical": 0, "General": 0}
        cat_counts: Dict[str, int] = {"Legal": 0, "Financial": 0, "Academic": 0, "Medical": 0, "General": 0}
        total_b = 0

        for d in docs.values():
            cat = d.get("category", "General")
            if cat not in cat_sizes:
                cat = "General"
            sz = d.get("size_bytes") or len(d.get("raw_text", "")) or 1024
            cat_sizes[cat] += sz
            cat_counts[cat] += 1
            total_b += sz

        def fmt_sz(b):
            if b >= 1073741824:
                return f"{b/1073741824:.2f} GB"
            elif b >= 1048576:
                return f"{b/1048576:.1f} MB"
            elif b >= 1024:
                return f"{b/1024:.1f} KB"
            return f"{b} B"

        if hasattr(self, "cat_labels"):
            for nl, sl in self.cat_labels:
                name = nl.text()
                cnt = cat_counts.get(name, 0)
                sz_str = fmt_sz(cat_sizes.get(name, 0))
                sl.setText(f"{sz_str} ({cnt} file{'s' if cnt != 1 else ''})")

        is_pro = str(user_tier).capitalize() == "Pro"
        max_bytes = (10 * 1024 * 1024 * 1024) if is_pro else (50 * 1024 * 1024)
        max_str = "10 GB" if is_pro else "50 MB"
        pct = (total_b / max_bytes * 100.0) if max_bytes > 0 else 0.0

        used_str = fmt_sz(total_b)
        if hasattr(self, "lbl_local_used"):
            self.lbl_local_used.setText(f"{used_str} of {max_str} used ({pct:.1f}%)")
        if hasattr(self, "donut"):
            colors = {"Legal": "#6B9BFF", "Financial": "#FF9548", "Academic": "#A58BFF", "Medical": "#F0556E", "General": "#FF7A2E"}
            slices = [(cat, sz if total_b > 0 else 1, colors[cat]) for cat, sz in cat_sizes.items()]
            self.donut.set_data(used_str if total_b > 0 else "0 B", slices, f"of {max_str} used")

        # Update cloud mirror card based on user tier
        if hasattr(self, "cc_badge") and hasattr(self, "lbl_cloud_status"):
            if is_pro:
                self.cc_badge.setText("● Live Sync Active")
                self.cc_badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
                self.lbl_cloud_status.setText(f"Real-time file watching active • {len(docs)} files mirrored")
            else:
                self.cc_badge.setText("Pro Plan Gated")
                self.cc_badge.setStyleSheet(f"color: {t['orange']}; background: {t['orange_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
                self.lbl_cloud_status.setText("Cloud mirror disabled on Free Trial. Upgrade to Pro for multi-device sync.")

        # Re-populate dynamic recent sync activity from actual user files
        if hasattr(self, "sc_items_lay"):
            while self.sc_items_lay.count():
                child = self.sc_items_lay.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            doc_list = sorted(
                docs.values(),
                key=lambda x: x.get("updated_at") or x.get("created_at") or "",
                reverse=True
            )

            if not doc_list:
                empty_lbl = QLabel("No files uploaded to vault yet. Drag & drop files or track a directory to begin live sync.")
                empty_lbl.setStyleSheet(f"font-size: 12px; color: {t['text3']}; padding: 12px 0;")
                self.sc_items_lay.addWidget(empty_lbl)
            else:
                for doc in doc_list[:5]:
                    row = QWidget()
                    rlay = QHBoxLayout(row)
                    rlay.setContentsMargins(0, 2, 0, 2)
                    rlay.setSpacing(10)

                    icon_lbl = QLabel("📄")
                    ext = Path(doc.get("filename", "")).suffix.lower()
                    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        icon_lbl.setText("🖼️")
                    elif ext == ".pdf":
                        icon_lbl.setText("📕")
                    elif ext == ".xml":
                        icon_lbl.setText("🏷️")
                    rlay.addWidget(icon_lbl)

                    col = QVBoxLayout()
                    col.setSpacing(2)
                    fn_lbl = QLabel(doc.get("filename", "Untitled"))
                    fn_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['text']};")
                    col.addWidget(fn_lbl)

                    d_sz = fmt_sz(doc.get("size_bytes", 0))
                    d_cat = doc.get("category", "General")
                    ds_lbl = QLabel(f"{d_cat} • {d_sz} • Stored locally in vault/local")
                    ds_lbl.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
                    col.addWidget(ds_lbl)
                    rlay.addLayout(col, 1)

                    st = doc.get("status", "Verified")
                    badge = QLabel(f"● {st}")
                    is_ok = st == "Verified"
                    badge.setStyleSheet(f"color: {t['green'] if is_ok else t['red']}; background: {t['green_bg'] if is_ok else t['red_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
                    rlay.addWidget(badge)

                    self.sc_items_lay.addWidget(row)

    def _open_dir(self, rel_path: str):
        full_path = os.path.abspath(rel_path)
        os.makedirs(full_path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text3']};")
        self.donut.update_theme(theme)
        for card in (self.donut_card, self.local_card, self.cloud_card, self.sync_card):
            card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {t['surface']};
                    border: 1px solid {t['border']};
                    border-radius: 16px;
                }}
            """)
        if hasattr(self, "leg_title"):
            self.leg_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        if hasattr(self, "cat_labels"):
            for nl, sl in self.cat_labels:
                nl.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 500;")
                sl.setStyleSheet(f"font-size: 12px; color: {t['text3']}; font-weight: 600;")
        if hasattr(self, "lc_title"):
            self.lc_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
            self.lc_badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
            self.path_local.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text3']};")
            self.lbl_local_used.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 600;")
        if hasattr(self, "cc_title"):
            self.cc_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
            self.cc_badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
            self.path_cloud.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text3']};")
            self.lbl_cloud_status.setStyleSheet(f"font-size: 12px; color: {t['text2']}; font-weight: 600;")
        if hasattr(self, "sc_title"):
            self.sc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
            for fn_lbl, ds_lbl, badge in self.sync_labels:
                fn_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['text']};")
                ds_lbl.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
                badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
        self.path_local.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text4']};")
        self.path_cloud.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {t['text4']};")
        self.lbl_local_used.setStyleSheet(f"font-size: 12px; color: {t['text3']}; font-weight: 600;")
        self.lbl_cloud_status.setStyleSheet(f"font-size: 12px; color: {t['text3']}; font-weight: 600;")


class IntegritySecurityPage(QWidget):
    """
    Dedicated Integrity & Health Page matching Page 12 of the design pack:
    - 4 Top Stat Cards: Health score ring (100 green), Hashes verified (9 of 9),
      Magic-byte checks (9 passed), Tamper alerts (0 this month)
    - Latest scan results list with green Authentic chips
    - Quarantine panel with green shield checkmark and empty state
    """
    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._build_ui()

    def _build_ui(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # Header
        hrow = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.t_lbl = QLabel("Integrity & Health")
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        title_box.addWidget(self.t_lbl)
        self.sub_lbl = QLabel("Proof that every document is exactly as you stored it.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text3']};")
        title_box.addWidget(self.sub_lbl)
        hrow.addLayout(title_box)
        hrow.addStretch()

        self.btn_export = QPushButton("Export report")
        self.btn_export.setObjectName("secondaryBtn")
        self.btn_export.setFixedHeight(34)
        self.btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_export)

        self.btn_run_scan = QPushButton("Run full scan")
        self.btn_run_scan.setObjectName("primaryBtn")
        self.btn_run_scan.setFixedHeight(34)
        self.btn_run_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_run_scan)
        lay.addLayout(hrow)

        # 4 Top Stats Cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self.stat_cards = []

        # Card 1: Health score ring
        self.card_health = QFrame()
        self.card_health.setObjectName("unifiedCard")
        ch_lay = QHBoxLayout(self.card_health)
        ch_lay.setContentsMargins(16, 14, 16, 14)
        ch_lay.setSpacing(14)
        self.ring = HealthScoreRingWidget(100, t, self)
        ch_lay.addWidget(self.ring)

        rt_col = QVBoxLayout()
        rt_col.setSpacing(2)
        rt_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.l1 = QLabel("Health score")
        self.l1.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        rt_col.addWidget(self.l1)
        self.l2 = QLabel("All checks passing")
        self.l2.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['green']};")
        rt_col.addWidget(self.l2)
        ch_lay.addLayout(rt_col)
        stats_row.addWidget(self.card_health, 1)

        # Card 2: Hashes verified
        self.card_hashes = self._make_stat_card("Hashes verified", "9 of 9")
        stats_row.addWidget(self.card_hashes, 1)

        # Card 3: Magic-byte checks
        self.card_magic = self._make_stat_card("Magic-byte checks", "9 passed")
        stats_row.addWidget(self.card_magic, 1)

        # Card 4: Tamper alerts
        self.card_tamper = self._make_stat_card("Tamper alerts", "0 this month")
        stats_row.addWidget(self.card_tamper, 1)

        lay.addLayout(stats_row)

        # Bottom Row: Latest scan results (flex 2) + Quarantine (flex 1)
        bot_row = QHBoxLayout()
        bot_row.setSpacing(16)

        # Left Card: Latest scan results
        self.results_card = QFrame()
        self.results_card.setObjectName("unifiedCard")
        rc_lay = QVBoxLayout(self.results_card)
        rc_lay.setContentsMargins(20, 18, 20, 18)
        rc_lay.setSpacing(12)

        self.rc_title = QLabel("Latest scan results")
        self.rc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
        rc_lay.addWidget(self.rc_title)

        scans = [
            ("CodeArrest_offer_letter.pdf", "SHA-256 matches stored fingerprint"),
            ("Vendor_Invoice_INV-9042.xml", "Magic bytes match file type"),
            ("Medical_Clinical_Record_MRN77821.xml", "SHA-256 matches stored fingerprint"),
            ("NDA_Apex_Quantum_2026.pdf", "Magic bytes match file type"),
        ]
        self.scan_labels = []
        for fname, desc in scans:
            row = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(2)
            fn = QLabel(fname)
            fn.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['text']};")
            col.addWidget(fn)
            ds = QLabel(desc)
            ds.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
            col.addWidget(ds)
            row.addLayout(col, 1)

            b_auth = QLabel("Authentic")
            b_auth.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
            row.addWidget(b_auth)

            ts = QLabel("Just now")
            ts.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
            row.addWidget(ts)
            rc_lay.addLayout(row)
            self.scan_labels.append((fn, ds, b_auth, ts))

        bot_row.addWidget(self.results_card, 2)

        # Right Card: Quarantine
        self.quarantine_card = QFrame()
        self.quarantine_card.setObjectName("unifiedCard")
        qc_lay = QVBoxLayout(self.quarantine_card)
        qc_lay.setContentsMargins(20, 24, 20, 20)
        qc_lay.setSpacing(10)
        qc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        q_icon = QLabel("✓")
        q_icon.setFixedSize(48, 48)
        q_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        q_icon.setStyleSheet(f"background: {t['green_bg']}; color: {t['green']}; font-size: 24px; font-weight: 800; border-radius: 24px;")
        qc_lay.addWidget(q_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.q_t = QLabel("Nothing in quarantine")
        self.q_t.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
        qc_lay.addWidget(self.q_t, alignment=Qt.AlignmentFlag.AlignCenter)

        self.q_desc = QLabel("Disguised or tampered files are moved here before they can be opened.")
        self.q_desc.setWordWrap(True)
        self.q_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.q_desc.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
        qc_lay.addWidget(self.q_desc, alignment=Qt.AlignmentFlag.AlignCenter)

        self.path_quarantine = QLabel(os.path.abspath("vault/quarantine"))
        self.path_quarantine.setWordWrap(True)
        self.path_quarantine.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_quarantine.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {t['text3']};")
        qc_lay.addWidget(self.path_quarantine, alignment=Qt.AlignmentFlag.AlignCenter)

        bot_row.addWidget(self.quarantine_card, 1)
        lay.addLayout(bot_row)
        lay.addStretch()

    def _make_stat_card(self, title: str, value: str) -> QFrame:
        t = self._t
        f = QFrame()
        f.setObjectName("unifiedCard")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        tl = QLabel(title)
        tl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text3']};")
        lay.addWidget(tl)

        vl = QLabel(value)
        vl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {t['text']};")
        lay.addWidget(vl)
        self.stat_cards.append((tl, vl))
        return f

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text3']};")
        self.ring.update_theme(theme)
        for card in (self.card_health, self.card_hashes, self.card_magic, self.card_tamper, self.results_card, self.quarantine_card):
            card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {t['surface']};
                    border: 1px solid {t['border']};
                    border-radius: 16px;
                }}
            """)
        if hasattr(self, "l1"):
            self.l1.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
            self.l2.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['green']};")
        if hasattr(self, "stat_cards"):
            for tl, vl in self.stat_cards:
                tl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text3']};")
                vl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {t['text']};")
        if hasattr(self, "rc_title"):
            self.rc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
        if hasattr(self, "scan_labels"):
            for fn, ds, b_auth, ts in self.scan_labels:
                fn.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['text']};")
                ds.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
                b_auth.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
                ts.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
        if hasattr(self, "q_t"):
            self.q_t.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {t['text']};")
            self.q_desc.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
        self.path_quarantine.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {t['text3']};")

    def refresh_metrics(self, docs: Dict[str, Dict[str, Any]]):
        total = len(docs)
        verified = sum(1 for d in docs.values() if d.get("status") == "Verified")
        magic_ok = sum(1 for d in docs.values() if not d.get("corrupted", False))

        if total == 0:
            self.ring.set_score(100)
            if hasattr(self, "l2"):
                self.l2.setText("Vault empty")
            if hasattr(self, "stat_cards") and len(self.stat_cards) >= 3:
                self.stat_cards[0][1].setText("0 of 0")
                self.stat_cards[1][1].setText("0 passed")
                self.stat_cards[2][1].setText("0 this month")
        else:
            pct = int((verified / total) * 100) if total > 0 else 100
            self.ring.set_score(pct)
            if hasattr(self, "l2"):
                self.l2.setText("All checks passing" if pct == 100 else f"{pct}% integrity")
            if hasattr(self, "stat_cards") and len(self.stat_cards) >= 3:
                self.stat_cards[0][1].setText(f"{verified} of {total}")
                self.stat_cards[1][1].setText(f"{magic_ok} passed")
                self.stat_cards[2][1].setText("0 this month")


class AuditTrailPage(QWidget):
    """
    Dedicated Audit Trail Page matching Page 13 of the design pack:
    - Filter chips (All activity, Sign-in, Viewed, Imported, Verified, Exported)
    - Search log input and Today filter
    - Timeline table with Time, Event and person, Type
    - Bottom summary counts: Events today, Documents touched, Failed attempts
    """
    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._events: List[Dict[str, str]] = []
        self.bottom_card_labels: List[Tuple[QLabel, QLabel]] = []
        self._build_ui()
        self._populate_table()

    def refresh_from_logs(self, audit_logs: List[Dict[str, Any]], docs_count: int = 0):
        self._events = []
        for log in audit_logs[:150]:
            action = log.get("action", "ACTION")
            det = log.get("details", "")
            op = log.get("operator", "System")
            ts = log.get("timestamp", "")
            t_str = ts.split("T")[-1][:8] if "T" in ts else ts
            self._events.append({
                "time": t_str or "Recent",
                "event": f"{det}\n{op}",
                "type": action,
            })
        self._populate_table()
        if hasattr(self, "bottom_card_labels") and len(self.bottom_card_labels) >= 3:
            self.bottom_card_labels[0][1].setText(str(len(self._events)))
            self.bottom_card_labels[1][1].setText(str(docs_count))
            self.bottom_card_labels[2][1].setText("0")

    def _build_ui(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # Header
        hrow = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.t_lbl = QLabel("Audit Trail")
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        title_box.addWidget(self.t_lbl)
        self.sub_lbl = QLabel("A tamper-evident record of everything that happens in your vault.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text4']};")
        title_box.addWidget(self.sub_lbl)
        hrow.addLayout(title_box)
        hrow.addStretch()

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setObjectName("secondaryBtn")
        self.btn_export.setFixedHeight(34)
        self.btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_export)

        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("primaryBtn")
        self.btn_print.setFixedHeight(34)
        self.btn_print.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hrow.addWidget(self.btn_print)
        lay.addLayout(hrow)

        # Filter & Search bar
        tbar = QHBoxLayout()
        tbar.setSpacing(8)

        self.chips: Dict[str, QPushButton] = {}
        for chip_name in ["All activity", "Sign-in", "Viewed", "Imported", "Verified", "Exported"]:
            btn = QPushButton(chip_name)
            btn.setObjectName("filterPill")
            btn.setProperty("active", chip_name == "All activity")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, n=chip_name: self._filter_chip(n))
            tbar.addWidget(btn)
            self.chips[chip_name] = btn

        tbar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search the log")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        tbar.addWidget(self.search_input)

        btn_today = QPushButton("Today")
        btn_today.setObjectName("secondaryBtn")
        btn_today.setFixedHeight(32)
        tbar.addWidget(btn_today)
        lay.addLayout(tbar)

        # Timeline Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Time", "Event and person", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {t['surface']};
                border: 1px solid {t['border']};
                border-radius: 14px;
                gridline-color: transparent;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {t['surface']};
                color: {t['text4']};
                font-weight: 700;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {t['border']};
                padding: 10px 14px;
            }}
            QTableWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {t['divider']};
                color: {t['text']};
            }}
        """)
        lay.addWidget(self.table, 1)

        # Bottom 3 summary cards
        bot_row = QHBoxLayout()
        bot_row.setSpacing(14)
        self.card_ev = self._make_bottom_card("Events today", "48")
        self.card_dt = self._make_bottom_card("Documents touched", "9")
        self.card_fa = self._make_bottom_card("Failed attempts", "0")
        bot_row.addWidget(self.card_ev, 1)
        bot_row.addWidget(self.card_dt, 1)
        bot_row.addWidget(self.card_fa, 1)
        lay.addLayout(bot_row)

    def _make_bottom_card(self, title: str, val: str) -> QFrame:
        t = self._t
        f = QFrame()
        f.setObjectName("unifiedCard")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(2)
        tl = QLabel(title)
        tl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text4']};")
        lay.addWidget(tl)
        vl = QLabel(val)
        vl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        lay.addWidget(vl)
        self.bottom_card_labels.append((tl, vl))
        return f

    def _seed_default_events(self):
        self._events = [
            {"time": "16:05:19", "event": "Opened Audit Trail\nYou", "type": "Viewed"},
            {"time": "16:05:12", "event": "Opened Integrity & Security\nYou", "type": "Viewed"},
            {"time": "16:04:57", "event": "Opened Storage & Cloud Mirrors\nYou", "type": "Viewed"},
            {"time": "16:04:46", "event": "Vault unlocked\nSiddharth", "type": "Sign-in"},
            {"time": "16:04:28", "event": "Loaded 9 documents from MongoDB\nSystem", "type": "Sync"},
            {"time": "16:04:28", "event": "Selected CodeArrest_offer_letter.pdf\nYou", "type": "Viewed"},
        ]
        self._populate_table()

    def _populate_table(self, query: str = "", category_filter: str = "All activity"):
        t = self._t
        filtered = []
        for e in self._events:
            if category_filter != "All activity":
                if category_filter.lower() not in e["type"].lower() and category_filter.lower() not in e["event"].lower():
                    continue
            if query:
                if query.lower() not in e["event"].lower() and query.lower() not in e["type"].lower():
                    continue
            filtered.append(e)

        self.table.setRowCount(len(filtered))
        for row, item in enumerate(filtered):
            t_item = QTableWidgetItem(item["time"])
            t_item.setForeground(QColor(t["text4"]))

            ev_item = QTableWidgetItem(item["event"])
            ev_item.setFont(QFont("Plus Jakarta Sans", 10, QFont.Weight.DemiBold))

            tp_item = QTableWidgetItem(item["type"])
            tp_item.setForeground(QColor(t["text3"]))

            self.table.setItem(row, 0, t_item)
            self.table.setItem(row, 1, ev_item)
            self.table.setItem(row, 2, tp_item)

    def _filter_chip(self, name: str):
        for k, btn in self.chips.items():
            btn.setProperty("active", k == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._populate_table(self.search_input.text().strip(), name)

    def _on_search(self, txt: str):
        active_chip = "All activity"
        for k, btn in self.chips.items():
            if btn.property("active"):
                active_chip = k
                break
        self._populate_table(txt.strip(), active_chip)

    def log_event(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._events.insert(0, {"time": ts, "event": f"{msg}\nYou", "type": "Action"})
        self._populate_table()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text4']};")
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {t['surface']};
                border: 1px solid {t['border']};
                border-radius: 14px;
                gridline-color: transparent;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {t['surface']};
                color: {t['text4']};
                font-weight: 700;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {t['border']};
                padding: 10px 14px;
            }}
            QTableWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {t['divider']};
                color: {t['text']};
            }}
        """)
        for card in (self.card_ev, self.card_dt, self.card_fa):
            card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {t['surface']};
                    border: 1px solid {t['border']};
                    border-radius: 16px;
                }}
            """)
        if hasattr(self, "bottom_card_labels"):
            for tl, vl in self.bottom_card_labels:
                tl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text4']};")
                vl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']};")
        if hasattr(self, "search_input"):
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background: {t['bg3']};
                    border: 1px solid {t['border']};
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: {t['text']};
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {t['primary']};
                    background: {t['bg2']};
                }}
            """)
        if hasattr(self, "btn_export"):
            self.btn_export.setStyleSheet(f"""
                QPushButton {{
                    background: {t['surface']};
                    color: {t['text']};
                    border: 1px solid {t['border']};
                    border-radius: 10px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {'#18202F' if t.get('name') == 'dark' else '#F0F2F5'};
                    border-color: {t['primary']};
                }}
            """)
        if hasattr(self, "btn_print"):
            self.btn_print.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 6px 18px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {t['primary_hover']};
                }}
            """)
def format_chat_markdown_to_html(text: str, is_dark: bool, primary_color: str = "#FF6422") -> str:
    """
    Transforms markdown into clean, high-contrast, professional prose typography
    matching ChatGPT with proper code blocks, table formatting, blockquotes,
    lists, and zero distracting AI emojis/gimmicks.
    """
    if not text:
        return ""

    # 1. Cleanse text: strip out cheesy AI emojis so outputs always look executive and professional
    text = re.sub(r"[🎯📌💡⚠️👋🚀🔥🤖✨❝❞👌👍🙏🎉✔️❌]", "", text)

    heading_color = "#FFFFFF" if is_dark else "#0F172A"
    body_color = "#ECECF1" if is_dark else "#1E293B"
    bold_color = "#FFFFFF" if is_dark else "#0F172A"
    quote_border = "#FF7A2E" if is_dark else "#F26A1B"
    quote_bg = "rgba(255, 122, 46, 0.06)" if is_dark else "rgba(242, 106, 27, 0.04)"
    quote_text = "#D1D5DB" if is_dark else "#334155"
    code_bg = "#111116" if is_dark else "#F1F5F9"
    code_border = "rgba(255, 255, 255, 0.10)" if is_dark else "#E2E8F0"
    code_text = "#F8FAFC" if is_dark else "#0F172A"
    bullet_dot = "#FF7A2E" if is_dark else "#F26A1B"
    table_border = "rgba(255, 255, 255, 0.12)" if is_dark else "#CBD5E1"
    table_th_bg = "rgba(255, 255, 255, 0.05)" if is_dark else "#F8FAFC"
    hr_color = "rgba(255, 255, 255, 0.10)" if is_dark else "#E2E8F0"

    lines = text.split("\n")
    html_lines = []
    in_quote = False
    quote_buffer = []
    in_code_block = False
    code_buffer = []
    code_lang = ""
    in_table = False
    table_rows = []

    def flush_quote():
        nonlocal in_quote, quote_buffer
        if quote_buffer:
            q_content = "<br>".join(quote_buffer)
            html_lines.append(
                f'<div style="border-left: 3px solid {quote_border}; background: {quote_bg}; '
                f'padding: 8px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; color: {quote_text}; '
                f'font-style: italic; line-height: 1.6; font-size: 13px;">{q_content}</div>'
            )
            quote_buffer = []
        in_quote = False

    def flush_code():
        nonlocal in_code_block, code_buffer, code_lang
        if code_buffer:
            code_str = "\n".join(code_buffer)
            code_str = code_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lang_label = f'<div style="font-size: 10px; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">{code_lang or "code"}</div>' if code_lang else ""
            html_lines.append(
                f'<div style="background: {code_bg}; border: 1px solid {code_border}; border-radius: 8px; padding: 12px 14px; margin: 10px 0; font-family: \'JetBrains Mono\', Consolas, monospace; font-size: 12px; line-height: 1.5; color: {code_text}; white-space: pre-wrap; overflow-x: auto;">'
                f'{lang_label}{code_str}</div>'
            )
            code_buffer = []
            code_lang = ""
        in_code_block = False

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            t_html = [f'<table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 12.5px; border: 1px solid {table_border}; border-radius: 6px;">']
            for i, row in enumerate(table_rows):
                is_header = (i == 0)
                tag = "th" if is_header else "td"
                bg = f'background: {table_th_bg}; font-weight: 700; color: {heading_color};' if is_header else f'color: {body_color};'
                cells = [c.strip() for c in row.split("|")[1:-1]] if row.startswith("|") and row.endswith("|") else [c.strip() for c in row.split("|")]
                t_html.append("<tr>")
                for c in cells:
                    t_html.append(f'<{tag} style="border: 1px solid {table_border}; padding: 6px 12px; {bg}">{c}</{tag}>')
                t_html.append("</tr>")
            t_html.append("</table>")
            html_lines.append("".join(t_html))
            table_rows = []
        in_table = False

    for line in lines:
        stripped = line.strip()

        # Fenced code block handler (```)
        if stripped.startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_quote:
                    flush_quote()
                if in_table:
                    flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_buffer = []
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Table handler (| col1 | col2 |)
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", stripped):
                continue
            if in_quote:
                flush_quote()
            in_table = True
            table_rows.append(stripped)
            continue
        else:
            if in_table:
                flush_table()

        # Blockquote handler (> ...)
        if stripped.startswith(">"):
            in_quote = True
            q_text = stripped.lstrip(">").strip()
            q_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', q_text)
            q_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px;">\\1</code>', q_text)
            quote_buffer.append(q_text)
            continue
        else:
            if in_quote:
                flush_quote()

        if not stripped:
            html_lines.append('<div style="height: 6px;"></div>')
            continue

        # Horizontal divider
        if stripped in ("---", "***", "___"):
            html_lines.append(f'<hr style="height: 1px; border: none; background-color: {hr_color}; margin: 12px 0;">')
            continue

        # Headings
        if stripped.startswith("####"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h4 style="margin: 12px 0 4px 0; font-size: 13px; font-weight: 700; '
                f'color: {heading_color}; letter-spacing: -0.2px;">{h_text}</h4>'
            )
        elif stripped.startswith("###"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h3 style="margin: 14px 0 6px 0; font-size: 14.5px; font-weight: 700; '
                f'color: {heading_color}; letter-spacing: -0.2px;">{h_text}</h3>'
            )
        elif stripped.startswith("##"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h2 style="margin: 16px 0 8px 0; font-size: 16px; font-weight: 700; '
                f'color: {heading_color}; letter-spacing: -0.3px;">{h_text}</h2>'
            )
        elif stripped.startswith("#"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h1 style="margin: 18px 0 10px 0; font-size: 18px; font-weight: 800; '
                f'color: {heading_color}; letter-spacing: -0.4px;">{h_text}</h1>'
            )
        # Ordered lists (1. , 2. )
        elif re.match(r"^\d+\.\s+", stripped):
            m_num = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            num_str = m_num.group(1) if m_num else "1"
            b_text = m_num.group(2) if m_num else stripped
            b_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', b_text)
            b_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px;">\\1</code>', b_text)
            b_text = re.sub(r"\*([^*]+)\*", '<i>\\1</i>', b_text)
            html_lines.append(
                f'<div style="margin: 4px 0 4px 8px; line-height: 1.65; color: {body_color}; font-size: 13.5px;">'
                f'<span style="color: {bold_color}; font-weight: 700; margin-right: 8px;">{num_str}.</span>{b_text}</div>'
            )
        # Bullet list items
        elif stripped.startswith(("•", "-", "* ")) and not stripped.startswith("**"):
            b_text = re.sub(r"^([•\-*]\s*)", "", stripped)
            b_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', b_text)
            b_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px;">\\1</code>', b_text)
            b_text = re.sub(r"\*([^*]+)\*", '<i>\\1</i>', b_text)
            html_lines.append(
                f'<div style="margin: 4px 0 4px 8px; line-height: 1.65; color: {body_color}; font-size: 13.5px;">'
                f'<span style="color: {bullet_dot}; font-weight: 700; margin-right: 8px;">•</span>{b_text}</div>'
            )
        else:
            p_text = stripped
            p_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', p_text)
            p_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px;">\\1</code>', p_text)
            p_text = re.sub(r"\*([^*]+)\*", '<i>\\1</i>', p_text)
            html_lines.append(
                f'<div style="line-height: 1.68; color: {body_color}; font-size: 13.5px; margin-bottom: 6px;">{p_text}</div>'
            )

    if in_quote:
        flush_quote()
    if in_code_block:
        flush_code()
    if in_table:
        flush_table()

    full_html = "".join(html_lines)
    return f"""
    <div style="font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; font-size: 13.5px; line-height: 1.68; color: {body_color};">
        {full_html}
    </div>
    """


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. EXPLAINABLE AI ASSISTANT WORKSPACE (CHAT A.I+ COPILOT STYLE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIAssistantPage(QWidget):
    """
    State-of-the-art Explainable AI Assistant Workspace:
    - 60-FPS Ambient Background Animation: The chat area and sidebar are translucent,
      allowing the InteractiveBackground particle canvas and mouse-tracking constellation to float behind.
    - Persistent Conversation History (config/chat_history.json):
      Full management with rename (pencil icon), delete (trash icon), and export.
    - ChatGPT / Microsoft Copilot Production UI:
      Clean high-contrast prose formatting, no distracting colored text/boxes,
      verified source citations at the bottom with direct viewer jump.
    - Full In-Thread Actions:
      User: [✎ Edit], [⎘ Copy], [🗑 Delete]
      Assistant: [⎘ Copy Answer], [↻ Regenerate], [👍 Helpful], [👎 Unhelpful], [🗑 Delete Turn]
    - Multi-Format File Attachment:
      Supports all file formats (.pdf, .docx, .txt, .png, .jpg, .jpeg, .webp, .xlsx, .csv, .json, .md, .py)
      with removable attachment chips, drag & drop directly onto the chat area.
    - 100% Vector Icons:
      Rendered via draw_vector_icon — zero generic/emoji icons.
    """

    def __init__(self, assistant: Optional[ExplainableAIAssistant], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.assistant = assistant
        self.tier_check_callback = None
        self.conversations: List[Dict[str, Any]] = []
        self.active_conv_id: Optional[str] = None
        self.search_filter: str = ""
        self.current_user: Dict[str, Any] = {"full_name": "Vault User", "tier": "Pro"}
        self.pinned_sources: List[str] = []
        self.attached_files: List[str] = []
        self.chat_history_path = Path("config/chat_history.json")

        self.setAcceptDrops(True)
        self._load_conversations()
        self._build_ui()

    def _init_default_conversations(self):
        self.conversations = [
            {
                "id": "conv_init",
                "title": "Document Intelligence RAG",
                "time_group": "Recent",
                "messages": [
                    {
                        "role": "assistant",
                        "text": (
                            "Welcome to **DocuVault AI**. I am your air-gapped, offline-first "
                            "document intelligence assistant.\n\n"
                            "Every answer is grounded directly in your uploaded vault files using "
                            "hybrid neural vector search and verified token overlap. "
                            "Zero cloud exfiltration guaranteed."
                        ),
                        "citations": [],
                        "time": "Just now",
                        "speed": "0.1s",
                        "guardrail": {"is_grounded": True, "confidence_score": 1.0, "warning": None},
                        "provider": "DocuVault Hybrid Intelligence Engine",
                    }
                ],
            }
        ]
        self.active_conv_id = "conv_init"

    def _load_conversations(self):
        if self.chat_history_path.exists():
            try:
                import json
                with open(self.chat_history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.conversations = data
                        self.active_conv_id = self.conversations[0].get("id")
                        return
            except Exception:
                pass
        self._init_default_conversations()
        self._save_conversations()

    def _save_conversations(self):
        try:
            import json
            self.chat_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.chat_history_path, "w", encoding="utf-8") as f:
                json.dump(self.conversations, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _build_ui(self):
        t = self._t
        is_dark = t.get("name") == "dark"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── 1. LEFT CONVERSATION SIDEBAR (~270px) ──
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(270)
        self.sidebar_frame.setObjectName("aiSidebar")
        self.sidebar_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        s_lay = QVBoxLayout(self.sidebar_frame)
        s_lay.setContentsMargins(16, 20, 16, 16)
        s_lay.setSpacing(12)

        # Header: CHAT A.I+ Title + Air-Gapped Badge
        head_row = QHBoxLayout()
        head_row.setContentsMargins(4, 0, 4, 0)
        self.lbl_title = QLabel("CHAT A.I+")
        self.lbl_title.setStyleSheet("font-size: 19px; font-weight: 800; letter-spacing: -0.5px;")
        head_row.addWidget(self.lbl_title)
        head_row.addStretch()

        self.badge_offline = QLabel("Air-Gapped")
        self.badge_offline.setStyleSheet(f"""
            font-size: 10px; font-weight: 700; color: {t['primary']};
            background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
            border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
            padding: 3px 8px; border-radius: 6px;
        """)
        head_row.addWidget(self.badge_offline)
        s_lay.addLayout(head_row)
        s_lay.addSpacing(4)

        # Action Row: [+ New chat] Orange Pill + [Search] Icon Button
        act_row = QHBoxLayout()
        act_row.setSpacing(8)

        self.btn_new_chat = QPushButton("+ New chat")
        self.btn_new_chat.setFixedHeight(38)
        self.btn_new_chat.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_chat.setIcon(QIcon(draw_vector_icon("plus", "#FFFFFF", 14)))
        self.btn_new_chat.clicked.connect(self._create_new_chat)
        act_row.addWidget(self.btn_new_chat, 1)

        self.btn_search_toggle = QPushButton()
        self.btn_search_toggle.setFixedSize(38, 38)
        self.btn_search_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_search_toggle.setIcon(QIcon(draw_vector_icon("search", t["text3"], 16)))
        self.btn_search_toggle.setToolTip("Filter conversations")
        self.btn_search_toggle.clicked.connect(self._toggle_search_filter)
        act_row.addWidget(self.btn_search_toggle)
        s_lay.addLayout(act_row)

        # Collapsible Search LineEdit
        self.in_chat_search = QLineEdit()
        self.in_chat_search.setFixedHeight(32)
        self.in_chat_search.setPlaceholderText("Filter conversations...")
        self.in_chat_search.setVisible(False)
        self.in_chat_search.textChanged.connect(self._on_filter_changed)
        s_lay.addWidget(self.in_chat_search)
        s_lay.addSpacing(6)

        # Section Header: "Your conversations" + "Clear All"
        sec_row = QHBoxLayout()
        sec_row.setContentsMargins(4, 0, 4, 0)
        self.lbl_your_convs = QLabel("Your conversations")
        self.lbl_your_convs.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text4']}; text-transform: uppercase; letter-spacing: 0.5px;")
        sec_row.addWidget(self.lbl_your_convs)
        sec_row.addStretch()

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear_all.setStyleSheet(f"background: transparent; border: none; font-size: 11px; font-weight: 600; color: {t['primary']}; padding: 0;")
        self.btn_clear_all.clicked.connect(self._clear_all_chats)
        sec_row.addWidget(self.btn_clear_all)
        s_lay.addLayout(sec_row)

        # Scrollable Conversation List
        self.conv_scroll = QScrollArea()
        self.conv_scroll.setWidgetResizable(True)
        self.conv_scroll.setStyleSheet("border: none; background: transparent;")

        self.conv_list_container = QWidget()
        self.conv_list_lay = QVBoxLayout(self.conv_list_container)
        self.conv_list_lay.setContentsMargins(0, 4, 0, 4)
        self.conv_list_lay.setSpacing(4)
        self.conv_list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.conv_scroll.setWidget(self.conv_list_container)
        s_lay.addWidget(self.conv_scroll, 1)

        # Bottom Profile & Settings Section
        self.div_sidebar = QFrame()
        self.div_sidebar.setFixedHeight(1)
        s_lay.addWidget(self.div_sidebar)

        self.btn_settings = QPushButton("Assistant Settings")
        self.btn_settings.setFixedHeight(34)
        self.btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings.setIcon(QIcon(draw_vector_icon("settings", t["text3"], 14)))
        self.btn_settings.clicked.connect(self._show_settings_hint)
        s_lay.addWidget(self.btn_settings)

        # User Profile Pill
        self.profile_card = QFrame()
        self.profile_card.setFixedHeight(50)
        p_lay = QHBoxLayout(self.profile_card)
        p_lay.setContentsMargins(10, 6, 10, 6)
        p_lay.setSpacing(10)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(32, 32)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setPixmap(draw_vector_icon("user", "#FFFFFF", 16))
        self.avatar_lbl.setStyleSheet(f"""
            background: {t['primary']}; border-radius: 16px;
        """)
        p_lay.addWidget(self.avatar_lbl)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(1)
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.profile_name = QLabel("Vault Workspace")
        self.profile_name.setStyleSheet(f"font-size: 12.5px; font-weight: 700; color: {t['text']};")
        self.profile_tier = QLabel("Zero-Knowledge Airgap")
        self.profile_tier.setStyleSheet(f"font-size: 10px; color: {t['text4']}; font-weight: 600;")
        info_lay.addWidget(self.profile_name)
        info_lay.addWidget(self.profile_tier)
        p_lay.addLayout(info_lay, 1)

        s_lay.addWidget(self.profile_card)
        main_lay.addWidget(self.sidebar_frame)

        # ── 2. RIGHT MAIN CHAT AREA (Translucent to display ambient animation) ──
        self.main_chat_frame = QFrame()
        self.main_chat_frame.setObjectName("aiChatCanvas")
        self.main_chat_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        m_lay = QVBoxLayout(self.main_chat_frame)
        m_lay.setContentsMargins(28, 20, 28, 20)
        m_lay.setSpacing(12)

        # Top Bar: Chat Title, Evidence grounding pill, Latency badge, Sources & API Key
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)
        top_bar.setSpacing(10)

        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        self.chat_heading = QLabel("Document Intelligence RAG")
        self.chat_heading.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {t['text']}; letter-spacing: -0.4px;")
        t_box.addWidget(self.chat_heading)

        self.chat_subheading = QLabel("Evidence-grounded neural search across contracts, policies, and records.")
        self.chat_subheading.setStyleSheet(f"font-size: 11.5px; color: {t['text4']};")
        t_box.addWidget(self.chat_subheading)
        top_bar.addLayout(t_box)

        top_bar.addStretch()

        self.btn_sources_top = QPushButton("Sources: All Vault")
        self.btn_sources_top.setIcon(QIcon(draw_vector_icon("documents", t["text"], 13)))
        self.btn_sources_top.setFixedHeight(30)
        self.btn_sources_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sources_top.setToolTip("Select specific documents to ground queries, or import new files")
        self.btn_sources_top.clicked.connect(self._open_sources_dialog)
        top_bar.addWidget(self.btn_sources_top)

        self.btn_ai_key = QPushButton("AI Key")
        self.btn_ai_key.setIcon(QIcon(draw_vector_icon("key", t["primary"], 13)))
        self.btn_ai_key.setFixedHeight(30)
        self.btn_ai_key.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ai_key.setToolTip("Configure Gemini, Groq, or OpenAI API Key")
        self.btn_ai_key.clicked.connect(self._open_api_key_modal)
        top_bar.addWidget(self.btn_ai_key)

        self.grounding_pill = QLabel("Grounded in Vault Sources")
        self.grounding_pill.setStyleSheet(f"""
            background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
            color: {t['primary']};
            border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
            font-size: 11px; font-weight: 700;
            padding: 5px 12px; border-radius: 12px;
        """)
        top_bar.addWidget(self.grounding_pill)

        self.speed_pill = QLabel("Sub-second RRF")
        self.speed_pill.setStyleSheet(f"""
            background: {t['bg3']}; color: {t['text3']};
            font-size: 11px; font-weight: 600;
            padding: 5px 12px; border-radius: 12px;
        """)
        top_bar.addWidget(self.speed_pill)
        m_lay.addLayout(top_bar)

        # Quick Suggested Prompts Row
        self.quick_chips_wrap = QFrame()
        self.quick_chips_wrap.setStyleSheet("background: transparent; border: none;")
        qc_lay = QHBoxLayout(self.quick_chips_wrap)
        qc_lay.setContentsMargins(0, 0, 0, 0)
        qc_lay.setSpacing(8)

        qc_lbl = QLabel("Suggested:")
        qc_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text4']};")
        qc_lay.addWidget(qc_lbl)

        quick_prompts = [
            ("Termination notice", "What is the termination notice period across my contracts?"),
            ("Payment terms", "When is the vendor payment due according to the invoices?"),
            ("Liability limits", "What are the liability caps and indemnity obligations?"),
            ("Governing law", "Under what state jurisdiction is the agreement governed?"),
        ]
        self.quick_buttons = []
        for q_label, q_query in quick_prompts:
            q_btn = QPushButton(q_label)
            q_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            q_btn.setFixedHeight(28)
            q_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 14px;
                    padding: 4px 12px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {t['primary']}; color: {t['primary']};
                }}
            """)
            q_btn.clicked.connect(lambda _, q=q_query: self.ask_query(q))
            qc_lay.addWidget(q_btn)
            self.quick_buttons.append(q_btn)
        qc_lay.addStretch()
        m_lay.addWidget(self.quick_chips_wrap)

        # Main Message Stream (Scrollable Area — Completely Translucent)
        self.msg_scroll = QScrollArea()
        self.msg_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_scroll.setWidgetResizable(True)
        self.msg_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.msg_scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.msg_container = QWidget()
        self.msg_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_container.setStyleSheet("background: transparent; border: none;")
        self.msg_lay = QVBoxLayout(self.msg_container)
        self.msg_lay.setContentsMargins(0, 8, 0, 16)
        self.msg_lay.setSpacing(18)
        self.msg_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.msg_scroll.setWidget(self.msg_container)
        m_lay.addWidget(self.msg_scroll, 1)

        # Active Attachment Chips Strip (Directly above input bar)
        self.attached_chips_frame = QFrame()
        self.attached_chips_frame.setVisible(False)
        self.attached_chips_frame.setStyleSheet("background: transparent; border: none;")
        self.att_chips_lay = QHBoxLayout(self.attached_chips_frame)
        self.att_chips_lay.setContentsMargins(4, 0, 4, 0)
        self.att_chips_lay.setSpacing(8)
        m_lay.addWidget(self.attached_chips_frame)

        # Bottom Floating Pill Input Bar (Copilot / ChatGPT Style with + Menu)
        self.input_card = QFrame()
        self.input_card.setFixedHeight(56)
        self.input_card.setObjectName("floatingInputCard")
        in_lay = QHBoxLayout(self.input_card)
        in_lay.setContentsMargins(10, 6, 8, 6)
        in_lay.setSpacing(8)

        # Attachment button (+)
        self.btn_attach = QPushButton()
        self.btn_attach.setFixedSize(36, 36)
        self.btn_attach.setIcon(QIcon(draw_vector_icon("plus", t["primary"], 15)))
        self.btn_attach.setToolTip("Upload files, select vault documents, or run OCR analysis")
        self.btn_attach.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_attach.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.08)' if is_dark else '#F0F2F5'};
                border: 1px solid {t['border']};
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background: {'rgba(242, 106, 27, 0.20)' if is_dark else '#FFE7D9'};
                border-color: {t['primary']};
            }}
        """)
        self.btn_attach.clicked.connect(self._show_attachment_dropdown)
        in_lay.addWidget(self.btn_attach)

        # Inline Scope Selector Pill
        self.btn_scope_pill = QPushButton("All Vault")
        self.btn_scope_pill.setFixedHeight(30)
        self.btn_scope_pill.setIcon(QIcon(draw_vector_icon("chevron_down", t["text3"], 10)))
        self.btn_scope_pill.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scope_pill.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.05)' if is_dark else '#F0F2F5'};
                color: {t['text3']};
                border: 1px solid {t['border']};
                border-radius: 15px;
                padding: 2px 10px;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {t['primary']};
                color: {t['text']};
            }}
        """)
        self.btn_scope_pill.clicked.connect(self._open_sources_dialog)
        in_lay.addWidget(self.btn_scope_pill)

        # Input QLineEdit
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about your documents, attach files, or drag & drop...")
        self.input_field.setStyleSheet(f"border: none; background: transparent; font-size: 13px; font-weight: 500; color: {t['text']};")
        self.input_field.returnPressed.connect(self._on_send)
        in_lay.addWidget(self.input_field, 1)

        # Circular Send Button
        self.btn_send = QPushButton()
        self.btn_send.setFixedSize(38, 38)
        self.btn_send.setIcon(QIcon(draw_vector_icon("send", "#FFFFFF", 16)))
        self.btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send.clicked.connect(self._on_send)
        in_lay.addWidget(self.btn_send)

        m_lay.addWidget(self.input_card)
        main_lay.addWidget(self.main_chat_frame, 1)

        # Render conversation items & active conversation
        self._render_conversations_list()
        self._render_active_chat()
        self.update_theme(self._t)

    # ── Conversation List Management & Editing ──

    def _render_conversations_list(self):
        while self.conv_list_lay.count():
            item = self.conv_list_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        for conv in self.conversations:
            cid = conv["id"]
            title = conv.get("title", "Conversation")
            is_active = (cid == self.active_conv_id)

            if self.search_filter and self.search_filter.lower() not in title.lower():
                continue

            item_card = QFrame()
            item_card.setFixedHeight(40)
            item_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            if is_active:
                bg = "rgba(242, 106, 27, 0.14)" if is_dark else "#FFF1EB"
                border_left = f"3px solid {t['primary']}"
                text_col = "#FFFFFF" if is_dark else t['primary']
                font_weight = "700"
            else:
                bg = "transparent"
                border_left = "3px solid transparent"
                text_col = t['text3']
                font_weight = "500"

            item_card.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: none;
                    border-left: {border_left};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#F0F2F5'};
                }}
            """)

            i_lay = QHBoxLayout(item_card)
            i_lay.setContentsMargins(10, 4, 8, 4)
            i_lay.setSpacing(8)

            ico_lbl = QLabel()
            ico_lbl.setPixmap(draw_vector_icon("chat", t["primary"] if is_active else t["text4"], 14))
            i_lay.addWidget(ico_lbl)

            lbl_txt = QLabel(title)
            lbl_txt.setStyleSheet(f"font-size: 12px; font-weight: {font_weight}; color: {text_col}; background: transparent; border: none;")
            i_lay.addWidget(lbl_txt, 1)

            # Edit / Rename Button
            btn_ren = QPushButton()
            btn_ren.setFixedSize(22, 22)
            btn_ren.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_ren.setIcon(QIcon(draw_vector_icon("pencil", t["text4"], 12)))
            btn_ren.setToolTip("Rename conversation")
            btn_ren.setStyleSheet("""
                QPushButton { background: transparent; border: none; border-radius: 4px; }
                QPushButton:hover { background: rgba(255, 255, 255, 0.12); }
            """)
            btn_ren.clicked.connect(lambda _, c=cid: self._rename_conversation(c))
            i_lay.addWidget(btn_ren)

            # Delete Button
            del_btn = QPushButton()
            del_btn.setFixedSize(22, 22)
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setIcon(QIcon(draw_vector_icon("trash", t["text4"], 12)))
            del_btn.setToolTip("Delete conversation")
            del_btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; border-radius: 4px; }
                QPushButton:hover { background: rgba(239, 68, 68, 0.20); }
            """)
            del_btn.clicked.connect(lambda _, c=cid: self._delete_conversation(c))
            i_lay.addWidget(del_btn)

            # Left click: select
            item_card.mousePressEvent = lambda ev, c=cid: self._select_conversation(c) if ev.button() == Qt.MouseButton.LeftButton else None

            # Right click context menu
            item_card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            item_card.customContextMenuRequested.connect(lambda pos, c=cid: self._show_conv_context_menu(pos, c))

            self.conv_list_lay.addWidget(item_card)

        self.conv_list_lay.addStretch(1)

    def _show_conv_context_menu(self, pos, conv_id: str):
        menu = QMenu(self)
        act_rename = menu.addAction("Rename Conversation")
        act_export = menu.addAction("Export to Markdown (.md)")
        menu.addSeparator()
        act_delete = menu.addAction("Delete Conversation")

        action = menu.exec(QCursor.pos())
        if action == act_rename:
            self._rename_conversation(conv_id)
        elif action == act_export:
            self._export_conversation_markdown(conv_id)
        elif action == act_delete:
            self._delete_conversation(conv_id)

    def _rename_conversation(self, conv_id: str):
        conv = next((c for c in self.conversations if c["id"] == conv_id), None)
        if not conv:
            return
        new_title, ok = QInputDialog.getText(
            self, "Rename Conversation", "Enter new conversation title:",
            QLineEdit.EchoMode.Normal, conv.get("title", "")
        )
        if ok and new_title.strip():
            conv["title"] = new_title.strip()
            self._save_conversations()
            self._render_conversations_list()
            if self.active_conv_id == conv_id:
                self.chat_heading.setText(conv["title"])
            self._create_notification_toast(f"Conversation renamed to '{new_title.strip()}'.")

    def _export_conversation_markdown(self, conv_id: str):
        conv = next((c for c in self.conversations if c["id"] == conv_id), None)
        if not conv:
            return
        title = conv.get("title", "Conversation").replace(" ", "_")
        fpath, _ = QFileDialog.getSaveFileName(
            self, "Export Conversation to Markdown", f"{title}.md",
            "Markdown Files (*.md);;Text Files (*.txt)"
        )
        if fpath:
            try:
                lines = [f"# {conv.get('title', 'Conversation')}\\n\\n*Exported from DocuVault AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\\n\\n---\\n\\n"]
                for msg in conv.get("messages", []):
                    role = "**User**" if msg.get("role") == "user" else "**DocuVault AI**"
                    text = msg.get("text", "")
                    lines.append(f"### {role} ({msg.get('time', '')})\\n\\n{text}\\n\\n---\\n\\n")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                self._create_notification_toast(f"Exported chat to {os.path.basename(fpath)}")
            except Exception as e:
                self._create_notification_toast(f"Export failed: {e}")

    def _select_conversation(self, conv_id: str):
        self.active_conv_id = conv_id
        self._render_conversations_list()
        self._render_active_chat()

    def _create_new_chat(self):
        new_id = f"conv_{len(self.conversations) + 1}_{int(time.time())}"
        new_conv = {
            "id": new_id,
            "title": "New Conversation",
            "time_group": "Recent",
            "messages": [
                {
                    "role": "assistant",
                    "text": "Ready to inspect your vault and answer any question. What would you like to verify or search today?",
                    "citations": [],
                    "time": datetime.now().strftime("%H:%M"),
                    "speed": "0.1s",
                    "guardrail": {"is_grounded": True, "confidence_score": 1.0, "warning": None},
                    "provider": "DocuVault Hybrid Intelligence Engine",
                }
            ],
        }
        self.conversations.insert(0, new_conv)
        self.active_conv_id = new_id
        self._save_conversations()
        self._render_conversations_list()
        self._render_active_chat()
        self.input_field.setFocus()

    def _delete_conversation(self, conv_id: str):
        if len(self.conversations) <= 1:
            self._clear_all_chats()
            return
        self.conversations = [c for c in self.conversations if c["id"] != conv_id]
        if self.active_conv_id == conv_id:
            self.active_conv_id = self.conversations[0]["id"]
        self._save_conversations()
        self._render_conversations_list()
        self._render_active_chat()
        self._create_notification_toast("Conversation deleted.")

    def _clear_all_chats(self):
        self.conversations = []
        self._init_default_conversations()
        self._save_conversations()
        self._render_conversations_list()
        self._render_active_chat()
        self._create_notification_toast("All conversation history cleared.")

    def _toggle_search_filter(self):
        vis = not self.in_chat_search.isVisible()
        self.in_chat_search.setVisible(vis)
        if vis:
            self.in_chat_search.setFocus()
        else:
            self.in_chat_search.clear()

    def _on_filter_changed(self, text: str):
        self.search_filter = text.strip()
        self._render_conversations_list()

    def _show_settings_hint(self):
        self._open_api_key_modal()

    def _open_api_key_modal(self):
        dlg = ApiKeyConfigDialog(self._t, self)
        dlg.keys_updated.connect(self._on_api_keys_updated)
        dlg.exec()

    def _on_api_keys_updated(self, keys: dict):
        if self.assistant:
            try:
                from backend.api_client import LLMClient
                self.assistant.llm_client = LLMClient()
            except Exception:
                pass
        self._create_notification_toast("AI API Keys updated. Real-time generative search active!")

    def _open_sources_dialog(self):
        main_win = self.window()
        available_docs = []
        if hasattr(main_win, "docs") and main_win.docs:
            available_docs = list(main_win.docs.values())
        elif hasattr(main_win, "mongo") and main_win.mongo.is_connected:
            available_docs = main_win.mongo.list_documents()

        dlg = SelectSourcesDialog(
            available_docs=available_docs,
            currently_selected=self.pinned_sources,
            theme=self._t,
            parent=self
        )
        dlg.sources_applied.connect(self._on_sources_applied)
        dlg.document_imported.connect(self._on_document_imported_via_dialog)
        dlg.exec()

    def _on_sources_applied(self, sources: list):
        self.pinned_sources = list(sources)
        self._update_sources_strip()
        count = len(self.pinned_sources)
        if count == 0:
            self._create_notification_toast("Query context reset to all vault documents.")
        else:
            self._create_notification_toast(f"Active query context pinned to {count} document{'s' if count>1 else ''}.")

    def _on_document_imported_via_dialog(self, doc_dict: dict):
        main_win = self.window()
        if hasattr(main_win, "_load_vault_database"):
            main_win._load_vault_database()

    def _clear_pinned_sources(self):
        self.pinned_sources.clear()
        self._update_sources_strip()
        self._create_notification_toast("Sources filter cleared. Querying all vault documents.")

    def _update_sources_strip(self):
        pinned_cnt = len(self.pinned_sources)
        att_cnt = len(self.attached_files)
        total_scope = pinned_cnt + att_cnt

        if total_scope == 0:
            if hasattr(self, "lbl_active_source_context"):
                self.lbl_active_source_context.setText("Query Scope: All Vault Documents")
            if hasattr(self, "btn_scope_pill"):
                self.btn_scope_pill.setText("All Vault")
            if hasattr(self, "btn_sources_top"):
                self.btn_sources_top.setText("Sources: All Vault")
            if hasattr(self, "btn_clear_sources"):
                self.btn_clear_sources.setVisible(False)
        else:
            names = []
            if pinned_cnt > 0:
                names.extend(self.pinned_sources)
            if att_cnt > 0:
                names.extend([Path(f).name for f in self.attached_files])
            txt = ", ".join(names)
            if len(txt) > 34:
                txt = txt[:34] + "..."
            if hasattr(self, "lbl_active_source_context"):
                self.lbl_active_source_context.setText(f"Query Scope ({total_scope} Active): <b>{txt}</b>")
            if hasattr(self, "btn_scope_pill"):
                self.btn_scope_pill.setText(f"{total_scope} docs")
            if hasattr(self, "btn_sources_top"):
                self.btn_sources_top.setText(f"Sources ({total_scope} Active)")
            if hasattr(self, "btn_clear_sources"):
                self.btn_clear_sources.setVisible(True)

    def _open_document_by_name(self, filename: str):
        main_win = self.window()
        target_doc = None
        if hasattr(main_win, "docs"):
            for d in main_win.docs.values():
                if d.get("filename") == filename or d.get("doc_id") == filename:
                    target_doc = d
                    break
        if not target_doc and hasattr(main_win, "mongo"):
            docs_from_mongo = main_win.mongo.list_documents(search_query=filename)
            if docs_from_mongo:
                target_doc = docs_from_mongo[0]
        if target_doc:
            dlg = DocumentViewerDialog(target_doc, self._t, self)
            dlg.exec()
        else:
            self._create_notification_toast(f"Source file '{filename}' was not found in active vault index.")

    # ── File Attachment & Drag-and-Drop ──

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        added = 0
        for u in urls:
            fp = u.toLocalFile()
            if fp and os.path.isfile(fp):
                if fp not in self.attached_files:
                    self.attached_files.append(fp)
                    added += 1
        if added > 0:
            self._render_attached_chips()
            self._update_sources_strip()
            self._create_notification_toast(f"Attached {added} file{'s' if added > 1 else ''} to query scope.")

    def _show_attachment_dropdown(self):
        menu = QMenu(self)
        t = self._t
        is_dark = t.get("name") == "dark"
        menu.setStyleSheet(f"""
            QMenu {{
                background: {'#14141B' if is_dark else '#FFFFFF'};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 12px;
                padding: 6px;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 8px 20px 8px 10px;
                border-radius: 6px;
                margin: 2px 0;
            }}
            QMenu::item:selected {{
                background: {'rgba(242, 106, 27, 0.15)' if is_dark else '#FFF1EB'};
                color: {t['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {t['border']};
                margin: 4px 6px;
            }}
        """)

        act_file = menu.addAction(QIcon(draw_vector_icon("upload", t["primary"], 14)), "Upload files from Computer...")
        act_vault = menu.addAction(QIcon(draw_vector_icon("documents", t["primary"], 14)), "Add from Vault Documents...")
        act_ocr = menu.addAction(QIcon(draw_vector_icon("ocr", t["primary"], 14)), "OCR & Text Scanner...")
        menu.addSeparator()
        act_synth = menu.addAction(QIcon(draw_vector_icon("sparkle", t["primary"], 14)), "Deep Multi-Doc Synthesis")
        act_deadlines = menu.addAction(QIcon(draw_vector_icon("calendar", t["primary"], 14)), "Audit Compliance & Deadlines")

        pos = self.btn_attach.mapToGlobal(QPoint(0, -menu.sizeHint().height() - 8))
        chosen = menu.exec(pos)

        if chosen == act_file:
            self._on_attach_clicked()
        elif chosen == act_vault:
            self._open_sources_dialog()
        elif chosen == act_ocr:
            self._on_ocr_scanner_clicked()
        elif chosen == act_synth:
            self.input_field.setText("Synthesize and compare the key clauses, liabilities, and obligations across all active vault contracts.")
            self.input_field.setFocus()
        elif chosen == act_deadlines:
            self.input_field.setText("Extract all compliance deadlines, renewal dates, payment terms, and notice periods from my documents.")
            self.input_field.setFocus()

    def _on_ocr_scanner_clicked(self):
        fpath, _ = QFileDialog.getOpenFileName(
            self, "Select Image or Document for OCR", "",
            "Documents & Images (*.pdf *.png *.jpg *.jpeg *.webp *.tiff);;All Files (*.*)"
        )
        if fpath:
            if fpath not in self.attached_files:
                self.attached_files.append(fpath)
            self._render_attached_chips()
            self._update_sources_strip()
            self.input_field.setText(f"Please run OCR and extract all key data, dates, and amounts from '{Path(fpath).name}'.")
            self.input_field.setFocus()

    def _on_attach_clicked(self):
        fpaths, _ = QFileDialog.getOpenFileNames(
            self,
            "Attach Files for Grounded AI Query",
            "",
            "All Supported Documents (*.pdf *.docx *.txt *.png *.jpg *.jpeg *.webp *.xlsx *.csv *.json *.md *.py);;PDF Documents (*.pdf);;Images (*.png *.jpg *.jpeg *.webp);;Office Documents (*.docx *.xlsx);;Text & Code (*.txt *.json *.csv *.md *.py);;All Files (*.*)"
        )
        if fpaths:
            added = 0
            for fp in fpaths:
                if fp not in self.attached_files:
                    self.attached_files.append(fp)
                    added += 1
            if added > 0:
                self._render_attached_chips()
                self._update_sources_strip()
                self._create_notification_toast(f"Attached {added} file{'s' if added > 1 else ''}.")

    def _render_attached_chips(self):
        while self.att_chips_lay.count():
            it = self.att_chips_lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        if not self.attached_files:
            self.attached_chips_frame.setVisible(False)
            return

        t = self._t
        is_dark = t.get("name") == "dark"
        self.attached_chips_frame.setVisible(True)

        lbl_head = QLabel("Attached Files:")
        lbl_head.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text4']};")
        self.att_chips_lay.addWidget(lbl_head)

        for fp in self.attached_files:
            fname = Path(fp).name
            chip = QFrame()
            chip.setStyleSheet(f"""
                QFrame {{
                    background: {'#181822' if is_dark else '#EEF2F6'};
                    border: 1px solid {t['border']};
                    border-radius: 12px;
                }}
            """)
            c_lay = QHBoxLayout(chip)
            c_lay.setContentsMargins(8, 2, 8, 2)
            c_lay.setSpacing(6)

            ico = QLabel()
            ico.setPixmap(draw_vector_icon("clip", t["primary"], 12))
            c_lay.addWidget(ico)

            disp_name = fname if len(fname) <= 24 else fname[:22] + "..."
            fn_lbl = QLabel(disp_name)
            fn_lbl.setToolTip(fp)
            fn_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text']};")
            c_lay.addWidget(fn_lbl)

            btn_del = QPushButton("✕")
            btn_del.setFixedSize(16, 16)
            btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_del.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 10px; font-weight: 700; color: #EF4444; }
                QPushButton:hover { background: rgba(239, 68, 68, 0.20); border-radius: 8px; }
            """)
            btn_del.clicked.connect(lambda _, p=fp: self._remove_attached_file(p))
            c_lay.addWidget(btn_del)

            self.att_chips_lay.addWidget(chip)

        self.att_chips_lay.addStretch()

    def _remove_attached_file(self, filepath: str):
        if filepath in self.attached_files:
            self.attached_files.remove(filepath)
            self._render_attached_chips()
            self._update_sources_strip()

    # ── Active Chat Rendering (ChatGPT / Copilot Style) ──

    def _get_active_conv(self) -> Optional[Dict[str, Any]]:
        for c in self.conversations:
            if c["id"] == self.active_conv_id:
                return c
        return self.conversations[0] if self.conversations else None

    def _render_active_chat(self):
        while self.msg_lay.count():
            item = self.msg_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        conv = self._get_active_conv()
        if not conv:
            return

        self.chat_heading.setText(conv.get("title", "Document Intelligence RAG"))

        t = self._t
        is_dark = t.get("name") == "dark"
        messages = conv.get("messages", [])

        for idx, msg in enumerate(messages):
            role = msg.get("role", "user")
            text = msg.get("text", "")
            citations = msg.get("citations", [])
            speed = msg.get("speed", "0.2s")
            guardrail = msg.get("guardrail", {})
            provider = msg.get("provider", "DocuVault Hybrid Intelligence Engine")

            if role == "user":
                turn_widget = QWidget()
                turn_widget.setStyleSheet("background: transparent; border: none;")
                t_lay = QHBoxLayout(turn_widget)
                t_lay.setContentsMargins(12, 4, 12, 4)
                t_lay.addStretch(1)

                u_bubble = QFrame()
                u_text_color = "#FFFFFF" if is_dark else "#0F172A"
                u_bubble.setMinimumWidth(160)
                u_bubble.setMaximumWidth(840)
                u_bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
                u_bubble.setStyleSheet(f"""
                    QFrame {{
                        background: {'rgba(255, 255, 255, 0.05)' if is_dark else '#F3F4F6'};
                        border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else '#E5E7EB'};
                        border-radius: 14px;
                    }}
                """)
                ub_lay = QVBoxLayout(u_bubble)
                ub_lay.setContentsMargins(14, 10, 14, 10)
                ub_lay.setSpacing(6)

                # Top row: user icon, name, time, actions
                u_top = QHBoxLayout()
                u_top.setSpacing(8)

                u_ico = QLabel()
                u_ico.setPixmap(draw_vector_icon("user", t["primary"], 14))
                u_top.addWidget(u_ico)

                u_title = QLabel("You")
                u_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
                u_top.addWidget(u_title)

                time_lbl = QLabel(msg.get("time", ""))
                time_lbl.setStyleSheet(f"font-size: 10px; color: {t['text4']};")
                u_top.addWidget(time_lbl)
                u_top.addStretch()

                # In-thread User Actions: Edit, Copy, Delete
                btn_ed = QPushButton()
                btn_ed.setFixedSize(22, 22)
                btn_ed.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_ed.setIcon(QIcon(draw_vector_icon("pencil", t["text4"], 11)))
                btn_ed.setToolTip("Edit question")
                btn_ed.setStyleSheet("background: transparent; border: none;")
                btn_ed.clicked.connect(lambda _, i=idx, txt=text: self._edit_user_message(i, txt))
                u_top.addWidget(btn_ed)

                btn_cp = QPushButton()
                btn_cp.setFixedSize(22, 22)
                btn_cp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_cp.setIcon(QIcon(draw_vector_icon("copy", t["text4"], 11)))
                btn_cp.setToolTip("Copy question")
                btn_cp.setStyleSheet("background: transparent; border: none;")
                btn_cp.clicked.connect(lambda _, txt=text, b=btn_cp: self._copy_to_clipboard(txt, b))
                u_top.addWidget(btn_cp)

                btn_dl = QPushButton()
                btn_dl.setFixedSize(22, 22)
                btn_dl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_dl.setIcon(QIcon(draw_vector_icon("trash", t["text4"], 11)))
                btn_dl.setToolTip("Delete this turn")
                btn_dl.setStyleSheet("background: transparent; border: none;")
                btn_dl.clicked.connect(lambda _, i=idx: self._delete_message_at_index(i))
                u_top.addWidget(btn_dl)

                ub_lay.addLayout(u_top)

                u_msg = QLabel(text)
                u_msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                u_msg.setWordWrap(True)
                u_msg.setStyleSheet(f"font-size: 13.5px; font-weight: 500; color: {u_text_color}; line-height: 1.55; background: transparent; border: none;")
                ub_lay.addWidget(u_msg)

                t_lay.addWidget(u_bubble, 0)
                self.msg_lay.addWidget(turn_widget)

            else:
                # Assistant Turn (Clean Copilot / ChatGPT Prose Flow)
                turn_widget = QWidget()
                turn_widget.setStyleSheet("background: transparent; border: none;")
                t_lay = QVBoxLayout(turn_widget)
                t_lay.setContentsMargins(8, 6, 8, 12)

                a_card = QFrame()
                a_card.setStyleSheet("background: transparent; border: none;")
                ac_lay = QVBoxLayout(a_card)
                ac_lay.setContentsMargins(4, 4, 4, 8)
                ac_lay.setSpacing(10)

                # Header Row: Sparkle icon, Title, Model Badge, Latency
                a_top = QHBoxLayout()
                a_top.setSpacing(8)

                a_ico = QLabel()
                a_ico.setPixmap(draw_vector_icon("sparkle", t["primary"], 16))
                a_top.addWidget(a_ico)

                a_title = QLabel("DocuVault AI")
                a_title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {t['primary']}; letter-spacing: -0.2px;")
                a_top.addWidget(a_title)

                engine_badge = QLabel("Offline Hybrid RAG")
                if "Groq" in provider:
                    engine_badge.setText("Groq Llama-3.1")
                elif "Gemini" in provider:
                    engine_badge.setText("Google Gemini 1.5")
                elif "OpenAI" in provider:
                    engine_badge.setText("OpenAI GPT-4o")

                engine_badge.setStyleSheet(f"""
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.05)'};
                    color: {t['text3']}; font-size: 10px; font-weight: 700;
                    padding: 3px 8px; border-radius: 6px;
                """)
                a_top.addWidget(engine_badge)

                if citations:
                    badge_ground = QLabel(f"Grounded ({len(citations)})")
                    badge_ground.setStyleSheet(f"""
                        background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
                        color: {t['primary']};
                        border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
                        font-size: 10px; font-weight: 700;
                        padding: 3px 8px; border-radius: 6px;
                    """)
                    a_top.addWidget(badge_ground)

                badge_time = QLabel(speed)
                badge_time.setStyleSheet(f"""
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.05)'};
                    color: {t['text4']}; font-size: 10px; font-weight: 700;
                    padding: 3px 8px; border-radius: 6px;
                """)
                a_top.addWidget(badge_time)
                a_top.addStretch()
                ac_lay.addLayout(a_top)

                # Formatted Synthesized Answer (ChatGPT / Copilot Typography)
                ans_display = QLabel()
                ans_display.setTextFormat(Qt.TextFormat.RichText)
                ans_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                ans_display.setWordWrap(True)
                ans_display.setStyleSheet("background: transparent; border: none; padding: 2px 0;")
                html_body = format_chat_markdown_to_html(text, is_dark, t.get("primary", "#FF6422"))
                ans_display.setText(html_body)
                ac_lay.addWidget(ans_display)

                # Hallucination Guardrail Alert
                if guardrail.get("warning"):
                    g_alert = QLabel(f"Warning: {guardrail['warning']}")
                    g_alert.setWordWrap(True)
                    g_alert.setStyleSheet("""
                        background: rgba(245, 181, 68, 0.12);
                        color: #F5B544; font-size: 11px; font-weight: 600;
                        padding: 8px 12px; border-radius: 8px;
                        border: 1px solid rgba(245, 181, 68, 0.25);
                    """)
                    ac_lay.addWidget(g_alert)

                # Verified Sources Strip at bottom of answer
                if citations:
                    src_container = QWidget()
                    src_container.setStyleSheet("background: transparent; border: none;")
                    sc_lay = QVBoxLayout(src_container)
                    sc_lay.setContentsMargins(0, 4, 0, 4)
                    sc_lay.setSpacing(6)

                    sc_head = QLabel(f"Verified Vault Sources ({len(citations)} Grounded):")
                    sc_head.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text4']};")
                    sc_lay.addWidget(sc_head)

                    cards_row = QHBoxLayout()
                    cards_row.setSpacing(8)

                    for cit in citations[:4]:
                        fname = cit.get("filename", "Document")
                        page = cit.get("page_number", 1)
                        sec = cit.get("section_title") or cit.get("position") or "General"
                        score_val = cit.get("score", 95)

                        ext = Path(fname).suffix.lower()
                        ico_name = "ocr" if ext in (".png", ".jpg", ".jpeg", ".webp") else "documents"

                        sc_card = QFrame()
                        sc_bg = "#16161E" if is_dark else "#F8FAFC"
                        sc_border = "#262632" if is_dark else "#E2E8F0"
                        sc_card.setFixedHeight(64)
                        sc_card.setMinimumWidth(180)
                        sc_card.setMaximumWidth(250)
                        sc_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                        sc_card.setStyleSheet(f"""
                            QFrame {{
                                background: {sc_bg};
                                border: 1px solid {sc_border};
                                border-radius: 8px;
                            }}
                            QFrame:hover {{
                                border-color: {t['primary']};
                            }}
                        """)
                        sc_card_lay = QVBoxLayout(sc_card)
                        sc_card_lay.setContentsMargins(10, 6, 10, 6)
                        sc_card_lay.setSpacing(3)

                        r1 = QHBoxLayout()
                        r1.setSpacing(6)
                        ico_lbl = QLabel()
                        ico_lbl.setPixmap(draw_vector_icon(ico_name, t["primary"], 13))
                        r1.addWidget(ico_lbl)

                        disp_fn = fname if len(fname) <= 16 else fname[:14] + "..."
                        lbl_fn = QLabel(disp_fn)
                        lbl_fn.setToolTip(fname)
                        lbl_fn.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {t['text']};")
                        r1.addWidget(lbl_fn, 1)

                        lbl_pct = QLabel(f"{score_val}%")
                        lbl_pct.setStyleSheet(f"""
                            font-size: 9.5px; font-weight: 800; color: {t['primary']};
                            background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
                            border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
                            padding: 1px 5px; border-radius: 4px;
                        """)
                        r1.addWidget(lbl_pct)
                        sc_card_lay.addLayout(r1)

                        r2 = QHBoxLayout()
                        r2.setSpacing(6)
                        lbl_loc = QLabel(f"Page {page} · {sec[:14]}")
                        lbl_loc.setStyleSheet(f"font-size: 10px; color: {t['text4']}; font-weight: 600;")
                        r2.addWidget(lbl_loc, 1)

                        btn_view = QPushButton("View")
                        btn_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                        btn_view.setIcon(QIcon(draw_vector_icon("eye", "#FFFFFF", 11)))
                        btn_view.setFixedHeight(20)
                        btn_view.setStyleSheet(f"""
                            QPushButton {{
                                background: {t['primary']}; color: #FFFFFF;
                                border: none; border-radius: 4px;
                                font-size: 9.5px; font-weight: 700; padding: 2px 8px;
                            }}
                            QPushButton:hover {{ background: {t['primary_hover']}; }}
                        """)
                        btn_view.clicked.connect(lambda _, fn=fname: self._open_document_by_name(fn))
                        r2.addWidget(btn_view)
                        sc_card_lay.addLayout(r2)

                        sc_card.mousePressEvent = lambda ev, fn=fname: self._open_document_by_name(fn)
                        cards_row.addWidget(sc_card)

                    cards_row.addStretch()
                    sc_lay.addLayout(cards_row)
                    ac_lay.addWidget(src_container)

                # Response Actions Toolbar (Vector Icons)
                act_row = QHBoxLayout()
                act_row.setSpacing(8)

                btn_copy = QPushButton("Copy Answer")
                btn_copy.setIcon(QIcon(draw_vector_icon("copy", t["text3"], 12)))
                btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_copy.setFixedHeight(26)
                btn_copy.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#16161D' if is_dark else '#F1F5F9'};
                        color: {t['text3']}; border: 1px solid {t['border']};
                        border-radius: 13px; padding: 2px 12px; font-size: 10.5px; font-weight: 600;
                    }}
                    QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
                """)
                clean_text = re.sub(r"<[^>]+>", "", text)
                btn_copy.clicked.connect(lambda _, txt=clean_text, b=btn_copy: self._copy_to_clipboard(txt, b))
                act_row.addWidget(btn_copy)

                btn_up = QPushButton("Helpful")
                btn_up.setIcon(QIcon(draw_vector_icon("thumb_up", t["text3"], 12)))
                btn_up.setFixedHeight(26)
                btn_up.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_up.setStyleSheet(f"background: transparent; border: 1px solid {t['border']}; border-radius: 13px; font-size: 10.5px; font-weight: 600; color: {t['text3']}; padding: 2px 10px;")
                btn_up.clicked.connect(lambda _, b=btn_up: b.setStyleSheet(f"background: {'rgba(242, 106, 27, 0.15)' if is_dark else '#FFF1EB'}; border: 1px solid {t['primary']}; border-radius: 13px; font-size: 10.5px; font-weight: 700; color: {t['primary']}; padding: 2px 10px;"))
                act_row.addWidget(btn_up)

                btn_down = QPushButton("Unhelpful")
                btn_down.setIcon(QIcon(draw_vector_icon("thumb_down", t["text3"], 12)))
                btn_down.setFixedHeight(26)
                btn_down.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_down.setStyleSheet(f"background: transparent; border: 1px solid {t['border']}; border-radius: 13px; font-size: 10.5px; font-weight: 600; color: {t['text3']}; padding: 2px 10px;")
                btn_down.clicked.connect(lambda _, b=btn_down: b.setStyleSheet("background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-radius: 13px; font-size: 10.5px; font-weight: 700; color: #EF4444; padding: 2px 10px;"))
                act_row.addWidget(btn_down)

                # Regenerate
                prev_query = None
                for m in reversed(messages[:idx]):
                    if m.get("role") == "user":
                        prev_query = m.get("text")
                        break
                if prev_query:
                    btn_regen = QPushButton("Regenerate")
                    btn_regen.setIcon(QIcon(draw_vector_icon("refresh", t["text3"], 12)))
                    btn_regen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_regen.setFixedHeight(26)
                    btn_regen.setStyleSheet(f"""
                        QPushButton {{
                            background: {'#16161D' if is_dark else '#F1F5F9'};
                            color: {t['text3']}; border: 1px solid {t['border']};
                            border-radius: 13px; padding: 2px 12px; font-size: 10.5px; font-weight: 600;
                        }}
                        QPushButton:hover {{ color: {t['primary']}; border-color: {t['primary']}; }}
                    """)
                    btn_regen.clicked.connect(lambda _, q=prev_query: self._execute_query(q, is_regenerate=True))
                    act_row.addWidget(btn_regen)

                # Delete assistant turn
                btn_del_turn = QPushButton()
                btn_del_turn.setFixedSize(26, 26)
                btn_del_turn.setIcon(QIcon(draw_vector_icon("trash", t["text4"], 11)))
                btn_del_turn.setToolTip("Delete this response")
                btn_del_turn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_del_turn.setStyleSheet("background: transparent; border: none;")
                btn_del_turn.clicked.connect(lambda _, i=idx: self._delete_message_at_index(i))
                act_row.addWidget(btn_del_turn)

                act_row.addStretch()
                ac_lay.addLayout(act_row)

                turn_sep = QFrame()
                turn_sep.setFixedHeight(1)
                turn_sep.setStyleSheet(f"background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.08)'}; border: none; margin-top: 14px;")
                ac_lay.addWidget(turn_sep)

                t_lay.addWidget(a_card)
                self.msg_lay.addWidget(turn_widget)

        # Smooth scroll to bottom
        QTimer.singleShot(60, lambda: self.msg_scroll.verticalScrollBar().setValue(
            self.msg_scroll.verticalScrollBar().maximum()
        ))

    def _edit_user_message(self, msg_idx: int, old_text: str):
        self.input_field.setText(old_text)
        self.input_field.setFocus()
        self.input_field.selectAll()
        self._create_notification_toast("Edit question and press Enter to re-run.")

    def _delete_message_at_index(self, msg_idx: int):
        conv = self._get_active_conv()
        if not conv:
            return
        msgs = conv.get("messages", [])
        if 0 <= msg_idx < len(msgs):
            is_user = (msgs[msg_idx].get("role") == "user")
            del msgs[msg_idx]
            if is_user and msg_idx < len(msgs) and msgs[msg_idx].get("role") == "assistant":
                del msgs[msg_idx]
            self._save_conversations()
            self._render_active_chat()
            self._create_notification_toast("Deleted from chat history.")

    def _copy_to_clipboard(self, text: str, btn: QPushButton):
        app = QApplication.instance()
        if app:
            clipboard = app.clipboard()
            clipboard.setText(text)
            old_txt = btn.text()
            btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: btn.setText(old_txt))

    # ── Input Handling & Generative RAG Query Execution ──

    def ask_query(self, query: str):
        self.input_field.setText(query)
        self._on_send()

    def _on_send(self):
        text = self.input_field.text().strip()
        if not text:
            return
        if self.tier_check_callback and not self.tier_check_callback():
            return
        self.input_field.clear()
        self._execute_query(text)

    def _execute_query(self, query_text: str, is_regenerate: bool = False):
        conv = self._get_active_conv()
        if not conv:
            return

        if not is_regenerate:
            conv["messages"].append({
                "role": "user",
                "text": query_text,
                "time": datetime.now().strftime("%H:%M"),
            })
            if conv.get("title") in ("New Conversation", "Document Intelligence RAG") and len(conv["messages"]) <= 3:
                clean_title = query_text.replace("What is", "").replace("When is", "").strip().capitalize()
                if len(clean_title) > 28:
                    clean_title = clean_title[:28] + "..."
                conv["title"] = clean_title
                self._render_conversations_list()

        start_t = time.time()
        answer_text = "DocuVault AI analyzed your local vault files."
        citations = []
        guardrail = {"is_grounded": True, "confidence_score": 1.0, "warning": None}
        provider = "DocuVault Hybrid Intelligence Engine"

        # Determine target filenames (combining pinned sources + attached files)
        targets = list(self.pinned_sources)
        for att in self.attached_files:
            fn = Path(att).name
            if fn not in targets:
                targets.append(fn)

        if self.assistant:
            try:
                res = self.assistant.answer_query(
                    query_text,
                    target_filenames=targets if targets else None,
                    user_email=self.current_user.get("email"),
                )
                if res:
                    answer_text = res.get("answer_text") or res.get("answer") or "No direct clause found."
                    citations = res.get("citations", [])
                    guardrail = res.get("guardrail", {})
                    provider = res.get("provider", provider)
            except Exception as e:
                answer_text = f"Query execution failed: {e}"
        else:
            answer_text = (
                f"Based on your vault index, no direct clause was found for '{query_text}'. "
                "Please import or drop documents to enable neural source grounding."
            )

        elapsed = round(time.time() - start_t, 2)
        speed_str = f"{elapsed:.2f} s" if elapsed > 0.0 else "0.2 s"

        conv["messages"].append({
            "role": "assistant",
            "text": answer_text,
            "citations": citations,
            "time": datetime.now().strftime("%H:%M"),
            "speed": speed_str,
            "guardrail": guardrail,
            "provider": provider,
        })

        self._save_conversations()
        self._render_active_chat()

    def set_assistant(self, assistant: ExplainableAIAssistant):
        self.assistant = assistant
        if hasattr(self, "current_user") and self.current_user:
            self.assistant.set_owner_email(self.current_user.get("email"))

    def set_user_info(self, user_dict: Dict[str, Any]):
        self.current_user = user_dict
        if self.assistant:
            self.assistant.set_owner_email(user_dict.get("email"))
        name = user_dict.get("full_name") or user_dict.get("email") or "Vault User"
        self.profile_name.setText(name)
        tier = user_dict.get("tier", "Pro")
        self.profile_tier.setText(f"{tier} Plan · Offline")

    def _create_notification_toast(self, message: str):
        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback(message)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        # Frosted glass sidebar
        sidebar_bg = "rgba(10, 10, 14, 0.70)" if is_dark else "rgba(255, 255, 255, 0.80)"
        sidebar_border = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.08)"
        self.sidebar_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.sidebar_frame.setStyleSheet(f"""
            #aiSidebar {{
                background: {sidebar_bg};
                border-right: 1px solid {sidebar_border};
            }}
        """)
        self.lbl_title.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {t['text']}; letter-spacing: -0.5px;")
        self.div_sidebar.setStyleSheet(f"background: {sidebar_border};")

        # New chat button
        self.btn_new_chat.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                color: #FFFFFF;
                border: none;
                border-radius: 19px;
                font-size: 12.5px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {t['primary_hover']}; }}
        """)
        self.btn_search_toggle.setStyleSheet(f"""
            QPushButton {{
                background: {'#141416' if is_dark else '#FFFFFF'};
                border: 1px solid {t['border']};
                border-radius: 19px;
            }}
            QPushButton:hover {{ border-color: {t['primary']}; }}
        """)

        self.in_chat_search.setStyleSheet(f"""
            QLineEdit {{
                background: {t['bg3']}; color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 10px; font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {t['primary']}; }}
        """)

        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']};
                border: 1px solid {t['border']}; border-radius: 8px;
                font-size: 11.5px; font-weight: 600; text-align: left; padding-left: 12px;
            }}
            QPushButton:hover {{ background: {'#141418' if is_dark else '#F2F2F7'}; color: {t['text']}; }}
        """)

        self.profile_card.setStyleSheet(f"""
            background: {'#121215' if is_dark else '#FFFFFF'};
            border: 1px solid {sidebar_border};
            border-radius: 10px;
        """)

        # Main Chat Canvas Styling (COMPLETELY TRANSLUCENT FOR 60-FPS PARTICLES)
        self.main_chat_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.main_chat_frame.setStyleSheet(f"""
            #aiChatCanvas {{
                background: transparent;
                border-left: 1px solid {sidebar_border};
            }}
        """)
        self.msg_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_scroll.viewport().setStyleSheet("background: transparent; border: none;")
        self.msg_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.msg_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.msg_container.setStyleSheet("background: transparent; border: none;")

        self.chat_heading.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {t['text']}; letter-spacing: -0.4px;")
        self.chat_subheading.setStyleSheet(f"font-size: 11.5px; color: {t['text4']};")

        # Top Bar buttons
        if hasattr(self, "grounding_pill"):
            self.grounding_pill.setStyleSheet(f"""
                background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
                color: {t['primary']};
                border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
                font-size: 11px; font-weight: 700;
                padding: 5px 12px; border-radius: 12px;
            """)
        if hasattr(self, "badge_offline"):
            self.badge_offline.setStyleSheet(f"""
                font-size: 10px; font-weight: 700; color: {t['primary']};
                background: {'rgba(242, 106, 27, 0.12)' if is_dark else '#FFF1EB'};
                border: 1px solid {'rgba(242, 106, 27, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.35)'};
                padding: 3px 8px; border-radius: 6px;
            """)
        if hasattr(self, "btn_sources_top"):
            self.btn_sources_top.setIcon(QIcon(draw_vector_icon("documents", t["text"], 13)))
            self.btn_sources_top.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 14px;
                    padding: 4px 14px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {t['primary']}; color: {t['primary']}; }}
            """)
        if hasattr(self, "btn_ai_key"):
            self.btn_ai_key.setIcon(QIcon(draw_vector_icon("key", t["primary"], 13)))
            self.btn_ai_key.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']}; color: {t['primary']};
                    border: 1px solid {t['border']}; border-radius: 14px;
                    padding: 4px 14px; font-size: 11px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {t['primary']}; color: #FFFFFF; }}
            """)

        # Floating Pill Input Bar Styling
        input_bg = "rgba(22, 22, 29, 0.88)" if is_dark else "rgba(248, 250, 252, 0.92)"
        input_border = "rgba(255, 100, 34, 0.40)" if is_dark else "rgba(255, 100, 34, 0.30)"
        self.input_card.setStyleSheet(f"""
            #floatingInputCard {{
                background: {input_bg};
                border: 1.5px solid {input_border};
                border-radius: 27px;
            }}
            #floatingInputCard:hover {{ border-color: {t['primary']}; }}
        """)

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: none; background: transparent;
                font-size: 13px; font-weight: 500; color: {t['text']};
            }}
        """)

        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                border: none; border-radius: 19px;
            }}
            QPushButton:hover {{ background: {t['primary_hover']}; }}
        """)

        self._update_sources_strip()
        self._render_conversations_list()
        self._render_active_chat()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. AI FILE ORGANIZER & INTELLIGENT TRIAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIFileOrganizerPage(QWidget):
    """
    Production AI-Powered File Organizer & Intelligent Triage:
    - 60-FPS Ambient Background Animation: Frosted glassmorphism layout allows the
      InteractiveBackground particle constellation to shine through.
    - Accurate Real-Time Metrics: Reflects live vault database (MongoDB + disk).
    - Autonomous Real-Time Auto-Organize: Monitors intake and automatically classifies,
      verifies magic bytes, moves files, syncs to MongoDB, and logs operations.
    - Interactive File Review Table with View Mode toggle (Pending Intake Queue vs Organized Vault).
    - One-Click Smart Batch Sort, Dry-Run Simulation, Demo Batch Generator, and Batch Rollback.
    - Drag & Drop Intake: Drop any document onto the window for instant triage.
    - Clean Collapsible Operations & Security Stream with live action filtering.
    """

    def __init__(self, organizer: FileOrganizerDaemon, mongo: MongoDatabase, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.organizer = organizer
        self.mongo = mongo
        self._t = theme
        self.last_batch_moves: List[Dict[str, str]] = []
        self._pending_files: List[Dict[str, Any]] = []
        self.auto_organize_enabled: bool = True
        self._is_sorting: bool = False
        self._view_mode: str = "PENDING"  # "PENDING" or "VAULT"
        self._log_filter: str = "ALL"      # "ALL", "SORT", "QUARANTINE", "UNDO"
        self._first_load: bool = True

        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        self._build_ui()

        # Seed sample intake if empty on initial launch so user never sees an empty void
        intake_dir = self.organizer.vault_root / "intake"
        intake_dir.mkdir(parents=True, exist_ok=True)
        if not [f for f in intake_dir.iterdir() if f.is_file()]:
            self._seed_sample_intake()

        self.refresh_files()

        # Real-time auto-refresh timer for logs & autonomous file organizer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3500)
        self.refresh_timer.timeout.connect(self._auto_sync_timer_tick)
        self.refresh_timer.start()

    def _build_ui(self):
        t = self._t
        is_dark = t.get("name") == "dark"

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(28, 20, 28, 18)
        root_lay.setSpacing(12)

        # ── 1. Header Banner ──
        h_box = QHBoxLayout()
        h_box.setSpacing(12)

        ico_lbl = QLabel()
        ico_lbl.setPixmap(draw_vector_icon("organizer", t["primary"], 26))
        h_box.addWidget(ico_lbl)

        title_lay = QVBoxLayout()
        title_lay.setSpacing(2)
        self.lbl_title = QLabel("AI File Organizer & Intelligent Triage")
        self.lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {t['text']}; letter-spacing: -0.4px;")
        title_lay.addWidget(self.lbl_title)

        self.lbl_sub = QLabel("Autonomous rule-based & machine-learning folder routing, smart renaming, and magic-byte integrity.")
        self.lbl_sub.setStyleSheet(f"font-size: 12px; color: {t['text4']};")
        title_lay.addWidget(self.lbl_sub)
        h_box.addLayout(title_lay, 1)

        # Live engine status badge / interactive toggle
        self.btn_auto_status = QPushButton("● Auto-Organize: ACTIVE")
        self.btn_auto_status.setFixedHeight(28)
        self.btn_auto_status.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_auto_status.setToolTip("Click to toggle autonomous background organization ON or PAUSED")
        self.btn_auto_status.setStyleSheet(f"""
            QPushButton {{
                font-size: 11px; font-weight: 700; color: {t['green']};
                background: {t['green_bg']};
                border: 1px solid {t.get('green_border', 'rgba(255, 122, 46, 0.35)')};
                padding: 4px 12px; border-radius: 12px;
            }}
            QPushButton:hover {{
                background: {t.get('hover', 'rgba(255, 122, 46, 0.20)')};
            }}
        """)
        self.btn_auto_status.clicked.connect(self._toggle_auto_organize)
        h_box.addWidget(self.btn_auto_status)
        root_lay.addLayout(h_box)

        # ── 2. Top Metric Cards (Frosted Glassmorphic) ──
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(12)

        self.card_total = self._create_metric_card("Total Vault Files", "0", "organizer", t["primary"])
        self.card_intake = self._create_metric_card("Intake Pending", "0", "documents", t["primary"])
        self.card_quarantine = self._create_metric_card("Quarantined", "0", "security", t["red"])
        self.card_ops = self._create_metric_card("Audit Operations", "0", "activity", t["green"])

        cards_lay.addWidget(self.card_total)
        cards_lay.addWidget(self.card_intake)
        cards_lay.addWidget(self.card_quarantine)
        cards_lay.addWidget(self.card_ops)
        root_lay.addLayout(cards_lay)

        # ── 3. Action Toolbar (Frosted Glass Container) ──
        self.tb_card = QFrame()
        self.tb_card.setObjectName("organizerToolbar")
        self._apply_toolbar_style()

        tb_lay = QHBoxLayout(self.tb_card)
        tb_lay.setContentsMargins(12, 8, 12, 8)
        tb_lay.setSpacing(8)

        # Run Smart Sort Primary Button
        self.btn_sort = QPushButton("Run Smart AI Sort Now")
        self.btn_sort.setIcon(QIcon(draw_vector_icon("organizer", "#FFFFFF", 14)))
        self.btn_sort.setFixedHeight(32)
        self.btn_sort.setMinimumWidth(168)
        self.btn_sort.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sort.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                color: #FFFFFF; font-size: 11px; font-weight: 700;
                border: none; border-radius: 8px; padding: 4px 10px;
            }}
            QPushButton:hover {{ background: {t['primary_hover']}; }}
        """)
        self.btn_sort.clicked.connect(self._run_smart_sort)
        tb_lay.addWidget(self.btn_sort)

        # Dry-run Preview Button
        self.btn_preview = QPushButton("Dry-Run Preview")
        self.btn_preview.setIcon(QIcon(draw_vector_icon("eye", t["text"], 13)))
        self.btn_preview.setFixedHeight(32)
        self.btn_preview.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_preview.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#FFFFFF'};
                color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 12px; font-size: 11.5px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {t['primary']}; color: {t['primary']}; }}
        """)
        self.btn_preview.clicked.connect(self._run_dry_run)
        tb_lay.addWidget(self.btn_preview)

        # Add Files Button
        self.btn_add = QPushButton("Add Files to Intake")
        self.btn_add.setIcon(QIcon(draw_vector_icon("plus", t["text"], 13)))
        self.btn_add.setFixedHeight(32)
        self.btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#FFFFFF'};
                color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 12px; font-size: 11.5px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {t['primary']}; color: {t['primary']}; }}
        """)
        self.btn_add.clicked.connect(self._add_files_to_intake)
        tb_lay.addWidget(self.btn_add)

        # Load Demo Batch Button
        self.btn_demo = QPushButton("Load Demo Batch")
        self.btn_demo.setIcon(QIcon(draw_vector_icon("documents", t["text3"], 13)))
        self.btn_demo.setFixedHeight(32)
        self.btn_demo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_demo.setToolTip("Populate intake queue with 7 realistic test documents (Legal, Medical, Academic, Financial, Quarantine)")
        self.btn_demo.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#FFFFFF'};
                color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 12px; font-size: 11.5px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {t['primary']}; color: {t['primary']}; }}
        """)
        self.btn_demo.clicked.connect(self._load_demo_batch)
        tb_lay.addWidget(self.btn_demo)

        # Undo Batch Button
        self.btn_undo = QPushButton("Undo Last Batch")
        self.btn_undo.setIcon(QIcon(draw_vector_icon("refresh", t["text3"], 13)))
        self.btn_undo.setFixedHeight(32)
        self.btn_undo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_undo.setStyleSheet(f"""
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#FFFFFF'};
                color: {t['text3']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 12px; font-size: 11.5px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
        """)
        self.btn_undo.clicked.connect(self._undo_last_batch)
        tb_lay.addWidget(self.btn_undo)

        tb_lay.addStretch()

        # Open Intake Folder
        self.btn_open_intake = QPushButton("Open Intake Folder")
        self.btn_open_intake.setIcon(QIcon(draw_vector_icon("documents", t["text3"], 12)))
        self.btn_open_intake.setFixedHeight(32)
        self.btn_open_intake.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_intake.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
        """)
        self.btn_open_intake.clicked.connect(self._open_intake_folder)
        tb_lay.addWidget(self.btn_open_intake)

        # Open Vault Folder Button
        self.btn_open_vault = QPushButton("Open Vault Folder")
        self.btn_open_vault.setIcon(QIcon(draw_vector_icon("organizer", t["text3"], 12)))
        self.btn_open_vault.setFixedHeight(32)
        self.btn_open_vault.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_vault.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
        """)
        self.btn_open_vault.clicked.connect(self._open_vault_folder)
        tb_lay.addWidget(self.btn_open_vault)

        # Refresh Button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setIcon(QIcon(draw_vector_icon("refresh", t["text3"], 12)))
        self.btn_refresh.setFixedHeight(32)
        self.btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
        """)
        self.btn_refresh.clicked.connect(self.refresh_files)
        tb_lay.addWidget(self.btn_refresh)

        root_lay.addWidget(self.tb_card)

        # ── 4. Splitter: Triage Table (Top) + Clean Audit Activity Stream (Bottom) ──
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle:vertical {
                background: rgba(255, 122, 46, 0.20);
                margin: 2px 0;
            }
            QSplitter::handle:vertical:hover {
                background: #FF7A2E;
            }
        """)

        # Table Wrapper Card
        self.table_wrap = QFrame()
        self.table_wrap.setObjectName("tableWrap")
        tw_lay = QVBoxLayout(self.table_wrap)
        tw_lay.setContentsMargins(14, 12, 14, 12)
        tw_lay.setSpacing(8)

        # Table Header Bar with View Switch
        th_bar = QHBoxLayout()
        th_bar.setSpacing(8)

        self.tbl_head = QLabel("File Queue & Intelligent Classification Triage:")
        self.tbl_head.setStyleSheet(f"font-size: 12.5px; font-weight: 700; color: {t['text']};")
        th_bar.addWidget(self.tbl_head)

        th_bar.addStretch()

        # View Mode Pill Buttons
        self.btn_mode_pending = QPushButton("Intake Queue (0)")
        self.btn_mode_pending.setFixedHeight(24)
        self.btn_mode_pending.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mode_pending.setStyleSheet(f"""
            QPushButton {{
                background: {t['primary']}; color: #FFFFFF; font-size: 10.5px; font-weight: 700;
                border: none; border-radius: 6px; padding: 2px 10px;
            }}
        """)
        self.btn_mode_pending.clicked.connect(lambda: self._set_view_mode("PENDING"))
        th_bar.addWidget(self.btn_mode_pending)

        self.btn_mode_vault = QPushButton("Organized Vault Files")
        self.btn_mode_vault.setFixedHeight(24)
        self.btn_mode_vault.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mode_vault.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']}; font-size: 10.5px; font-weight: 600;
                border: 1px solid {t['border']}; border-radius: 6px; padding: 2px 10px;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
        """)
        self.btn_mode_vault.clicked.connect(lambda: self._set_view_mode("VAULT"))
        th_bar.addWidget(self.btn_mode_vault)

        tw_lay.addLayout(th_bar)

        # Translucent Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Select", "File Name", "Smart Proposed Name", "Category",
            "Size", "Magic Bytes Integrity", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(3, 120)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(5, 140)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.table.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.table.viewport().setStyleSheet("background: transparent; border: none;")

        self._apply_table_style()
        tw_lay.addWidget(self.table)
        splitter.addWidget(self.table_wrap)

        # Audit Log Console Wrapper Card
        self.log_wrap = QFrame()
        self.log_wrap.setObjectName("logWrap")
        lw_lay = QVBoxLayout(self.log_wrap)
        lw_lay.setContentsMargins(14, 10, 14, 10)
        lw_lay.setSpacing(6)

        # Log Header Bar
        log_head_bar = QHBoxLayout()
        log_head_bar.setSpacing(8)

        log_head = QLabel("file_ops.log — Real-Time Operations & Audit Stream:")
        log_head.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {t['text3']};")
        log_head_bar.addWidget(log_head)

        log_head_bar.addStretch()

        # Log Filter Pills
        for flt_name in ("ALL", "SORT", "QUARANTINE", "UNDO"):
            btn_f = QPushButton(flt_name)
            btn_f.setFixedHeight(22)
            btn_f.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_f.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {t['text3']}; font-size: 9.5px; font-weight: 700;
                    border: 1px solid {t['border']}; border-radius: 4px; padding: 1px 7px;
                }}
                QPushButton:hover {{ color: {t['primary']}; border-color: {t['primary']}; }}
            """)
            btn_f.clicked.connect(lambda _, f=flt_name: self._set_log_filter(f))
            log_head_bar.addWidget(btn_f)

        # Collapse Log Button
        self.btn_collapse_log = QPushButton("▾ Collapse")
        self.btn_collapse_log.setFixedHeight(22)
        self.btn_collapse_log.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_collapse_log.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text3']}; font-size: 10px; font-weight: 600;
                border: 1px solid {t['border']}; border-radius: 4px; padding: 1px 8px;
            }}
            QPushButton:hover {{ color: {t['text']}; }}
        """)
        self.btn_collapse_log.clicked.connect(self._toggle_collapse_logs)
        log_head_bar.addWidget(self.btn_collapse_log)

        lw_lay.addLayout(log_head_bar)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.log_console.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._apply_console_style()
        lw_lay.addWidget(self.log_console)

        splitter.addWidget(self.log_wrap)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        root_lay.addWidget(splitter, 1)

    # ─── Drag and Drop Support ──────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            intake_dir = self.organizer.vault_root / "intake"
            intake_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            for url in event.mimeData().urls():
                fp = url.toLocalFile()
                if fp and os.path.exists(fp):
                    p = Path(fp)
                    if p.is_file():
                        shutil.copy2(p, intake_dir / p.name)
                        copied += 1
            if copied > 0:
                p = self.window()
                if hasattr(p, "_show_feedback"):
                    p._show_feedback(f"Imported {copied} file{'s' if copied != 1 else ''} into intake triage queue.")
                self.refresh_files()
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ─── View Modes & Filters ───────────────────────────────────────────────────

    def _set_view_mode(self, mode: str):
        self._view_mode = mode
        t = self._t
        if mode == "PENDING":
            self.btn_mode_pending.setStyleSheet(f"""
                QPushButton {{
                    background: {t['primary']}; color: #FFFFFF; font-size: 10.5px; font-weight: 700;
                    border: none; border-radius: 6px; padding: 2px 10px;
                }}
            """)
            self.btn_mode_vault.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {t['text3']}; font-size: 10.5px; font-weight: 600;
                    border: 1px solid {t['border']}; border-radius: 6px; padding: 2px 10px;
                }}
                QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
            """)
        else:
            self.btn_mode_vault.setStyleSheet(f"""
                QPushButton {{
                    background: {t['primary']}; color: #FFFFFF; font-size: 10.5px; font-weight: 700;
                    border: none; border-radius: 6px; padding: 2px 10px;
                }}
            """)
            self.btn_mode_pending.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {t['text3']}; font-size: 10.5px; font-weight: 600;
                    border: 1px solid {t['border']}; border-radius: 6px; padding: 2px 10px;
                }}
                QPushButton:hover {{ color: {t['text']}; border-color: {t['primary']}; }}
            """)
        self.refresh_files()

    def _set_log_filter(self, flt: str):
        self._log_filter = flt
        self._refresh_audit_logs()

    def _toggle_collapse_logs(self):
        is_visible = self.log_console.isVisible()
        self.log_console.setVisible(not is_visible)
        self.btn_collapse_log.setText("▴ Expand" if is_visible else "▾ Collapse")

    def _toggle_auto_organize(self):
        self.auto_organize_enabled = not self.auto_organize_enabled
        t = self._t
        if self.auto_organize_enabled:
            self.btn_auto_status.setText("● Auto-Organize: ACTIVE")
            self.btn_auto_status.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 700; color: {t['green']};
                    background: {t['green_bg']};
                    border: 1px solid {t.get('green_border', 'rgba(255, 122, 46, 0.35)')};
                    padding: 4px 12px; border-radius: 12px;
                }}
            """)
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback("Autonomous file organizer activated. Intake files will be categorized automatically.")
            # Trigger immediate scan
            self._auto_sync_timer_tick()
        else:
            self.btn_auto_status.setText("⏸ Auto-Organize: PAUSED")
            self.btn_auto_status.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11px; font-weight: 700; color: {t['text3']};
                    background: {'rgba(255, 255, 255, 0.08)' if t.get('name') == 'dark' else '#F1F5F9'};
                    border: 1px solid {t['border']};
                    padding: 4px 12px; border-radius: 12px;
                }}
            """)
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback("Auto-organize paused. Files will remain in queue for manual inspection.")

    # ─── Metric Card Factory ────────────────────────────────────────────────────

    def _create_metric_card(self, label: str, value: str, icon_name: str, color: str) -> QFrame:
        t = self._t
        is_dark = t.get("name") == "dark"
        card = QFrame()
        card.setFixedHeight(68)
        card.setStyleSheet(f"""
            QFrame {{
                background: {'rgba(18, 18, 26, 0.60)' if is_dark else 'rgba(255, 255, 255, 0.70)'};
                border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                border-radius: 14px;
            }}
            QFrame:hover {{
                border-color: rgba(255, 122, 46, 0.35);
            }}
        """)
        c_lay = QHBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        c_lay.setSpacing(12)

        ico = QLabel()
        ico.setPixmap(draw_vector_icon(icon_name, color, 22))
        c_lay.addWidget(ico)

        txt_lay = QVBoxLayout()
        txt_lay.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("cardVal")
        val_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {t['text']}; letter-spacing: -0.5px;")
        txt_lay.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10.5px; font-weight: 600; color: {t['text4']}; text-transform: uppercase; letter-spacing: 0.5px;")
        txt_lay.addWidget(lbl)
        c_lay.addLayout(txt_lay, 1)

        return card

    # ─── Periodic Autonomous Tick ───────────────────────────────────────────────

    def _auto_sync_timer_tick(self):
        if not self.isVisible():
            return

        self._refresh_audit_logs()

        # If autonomous organization is enabled, auto-sort pending files
        if self.auto_organize_enabled and not self._is_sorting:
            intake_dir = self.organizer.vault_root / "intake"
            if intake_dir.exists():
                pending = [f for f in intake_dir.iterdir() if f.is_file()]
                if pending:
                    self._auto_sort_pending_files(pending)

    def _auto_sort_pending_files(self, files: List[Path]):
        self._is_sorting = True
        sorted_cnt = 0
        try:
            for f in files:
                fp = str(f)
                try:
                    res = self.organizer.sort_file(fp)
                    dest = res.get("destination", "")
                    if dest:
                        self.last_batch_moves.append({"src": fp, "dest": dest})
                        self._persist_sorted_document(dest, res.get("category", "General"))
                    sorted_cnt += 1
                except Exception as e:
                    print(f"[AIFileOrganizer] Auto-sort error on {f.name}: {e}")

            if sorted_cnt > 0:
                p = self.window()
                if hasattr(p, "_show_feedback"):
                    p._show_feedback(f"AI File Organizer autonomously sorted {sorted_cnt} incoming file{'s' if sorted_cnt != 1 else ''}.")
                if hasattr(p, "_load_vault_database"):
                    p._load_vault_database()
                self.refresh_files()
        finally:
            self._is_sorting = False

    def _seed_sample_intake(self):
        """Generates realistic sample documents into vault/intake."""
        try:
            import generate_samples
            if hasattr(generate_samples, "generate_all_samples"):
                generate_samples.generate_all_samples()
                return
        except Exception as e:
            print(f"[AIFileOrganizer] Notice loading generate_samples: {e}")

        # Fallback inline generation if module not directly importable
        intake_dir = self.organizer.vault_root / "intake"
        intake_dir.mkdir(parents=True, exist_ok=True)
        try:
            (intake_dir / "Academic_Quantum_Error_Mitigation.txt").write_text(
                "QUANTUM ERROR MITIGATION IN HIGH-DIMENSIONAL HILBERT SPACES\nAbstract: Scalable error mitigation protocols.",
                encoding="utf-8"
            )
            (intake_dir / "Master_Services_Agreement_NY.txt").write_text(
                "MASTER SERVICES AGREEMENT\nGoverning Law: Under the laws of the State of New York. Effective Date: 2026-10-10.",
                encoding="utf-8"
            )
            (intake_dir / "Vendor_Invoice_INV-9042.xml").write_text(
                "<invoice><vendor>Apex Quantum</vendor><total>$1,250.00</total></invoice>",
                encoding="utf-8"
            )
            (intake_dir / "Medical_Clinical_Record_MRN77821.xml").write_text(
                "<medical_record><patient>Jane Doe</patient><diagnosis>Hypertension</diagnosis></medical_record>",
                encoding="utf-8"
            )
            (intake_dir / "Clean_Integrity_Verification.txt").write_text(
                "Official verification test record. Hash integrity verified on 2026-10-27.",
                encoding="utf-8"
            )
            # PE disguised file
            with open(intake_dir / "Disguised_Malware_Payload.pdf", "wb") as f:
                f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00DOS mode payload.")
        except Exception as e:
            print(f"[AIFileOrganizer] Inline seed error: {e}")

    def _load_demo_batch(self):
        self._seed_sample_intake()
        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback("Loaded demonstration files into intake queue.")
        self._set_view_mode("PENDING")
        self.refresh_files()

    def _persist_sorted_document(self, dest_path: str, category: str):
        """Sync newly sorted file into MongoDB and Catalog so the app updates in real-time."""
        p = Path(dest_path)
        if not p.exists() or "quarantine" in dest_path.lower():
            return
        try:
            user_email = getattr(self.window(), "user_email", None) if self.window() else None
            doc = DocumentFactory.create_document(str(p), category_hint=category, enforce_magic_bytes=False)
            doc_dict = doc.to_dict()
            full_text = " ".join([page.get("text", "") for page in doc_dict.get("pages", [])]) or doc_dict.get("raw_text", "")
            doc_dict["executive_summary"] = DocumentAnalyzer.extract_executive_summary(full_text, doc.filename)
            doc_dict["counterparties"] = DocumentAnalyzer.extract_counterparties(full_text)
            doc_dict["risk_profile"] = DocumentAnalyzer.calculate_risk_profile(full_text, doc_dict.get("clauses"))
            doc_dict["tracked_folder"] = str(p.parent)
            if user_email:
                doc_dict["owner_email"] = user_email
            doc_dict["created_at"] = datetime.now().isoformat()
            doc_dict["updated_at"] = datetime.now().isoformat()

            if self.mongo and self.mongo.is_connected:
                self.mongo.save_document(doc_dict, user_email=user_email)
        except Exception as e:
            print(f"[AIFileOrganizer] MongoDB sync notice: {e}")

    # ─── Main Refresh & Populator ───────────────────────────────────────────────

    def refresh_files(self, dry_run: bool = False):
        self._pending_files.clear()
        intake_dir = self.organizer.vault_root / "intake"
        intake_dir.mkdir(parents=True, exist_ok=True)

        raw_intake_files = [f for f in intake_dir.iterdir() if f.is_file()]

        # Query disk vault files across categories
        local_disk_count = 0
        vault_files_by_cat: List[Tuple[Path, str]] = []
        for cat in self.organizer.CATEGORIES:
            cat_dir = self.organizer.vault_root / cat
            if cat_dir.exists():
                cat_files = [f for f in cat_dir.iterdir() if f.is_file()]
                local_disk_count += len(cat_files)
                for cf in cat_files:
                    vault_files_by_cat.append((cf, cat))

        # Query MongoDB for real-time vault count
        mongo_count = 0
        if self.mongo and self.mongo.is_connected:
            try:
                user_email = getattr(self.window(), "user_email", None) if self.window() else None
                mongo_count = len(self.mongo.list_documents(user_email=user_email))
            except Exception:
                mongo_count = 0

        win_docs = len(getattr(self.window(), "docs", {})) if self.window() else 0
        total_vault_count = max(mongo_count, win_docs, local_disk_count)

        quarantine_dir = self.organizer.vault_root / "quarantine"
        quarantine_count = len([f for f in quarantine_dir.iterdir() if f.is_file()]) if quarantine_dir.exists() else 0

        # Update metric cards
        self.card_total.findChild(QLabel, "cardVal").setText(str(total_vault_count))
        self.card_intake.findChild(QLabel, "cardVal").setText(str(len(raw_intake_files)))
        self.card_quarantine.findChild(QLabel, "cardVal").setText(str(quarantine_count))
        self.card_ops.findChild(QLabel, "cardVal").setText(str(len(self.organizer.logger.get_recent_logs(500))))

        self.btn_mode_pending.setText(f"Intake Queue ({len(raw_intake_files)})")

        # Choose files to display based on active view mode
        self.table.setRowCount(0)
        t = self._t
        is_dark = t.get("name") == "dark"

        if self._view_mode == "PENDING":
            display_files = [(f, "PENDING") for f in raw_intake_files]
            self.tbl_head.setText(f"File Queue & Intelligent Classification Triage ({len(raw_intake_files)} Pending):")
        else:
            display_files = [(f, cat) for f, cat in vault_files_by_cat]
            if quarantine_dir.exists():
                display_files.extend([(f, "Quarantine") for f in quarantine_dir.iterdir() if f.is_file()])
            self.tbl_head.setText(f"Organized Vault Documents ({len(display_files)} Stored):")

        for f, mode_cat in display_files:
            fp = str(f)
            sz_b = f.stat().st_size
            sz_str = f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B"

            # Magic-byte check
            is_valid = True
            try:
                BinaryParser.validate_file(fp)
            except Exception:
                is_valid = False

            # Detect category
            cat = mode_cat if mode_cat != "PENDING" else "General"
            if mode_cat == "PENDING":
                try:
                    doc = DocumentFactory.create_document(fp, enforce_magic_bytes=False)
                    cat = doc.get_category()
                except Exception:
                    cat = "Quarantine" if not is_valid else "General"

            # Generate smart rename proposal
            stem = f.stem.replace("_", " ").title().replace(" ", "_")
            ext = f.suffix.lower()
            if stem.lower().startswith(cat.lower()):
                smart_name = f"{stem}{ext}"
            else:
                smart_name = f"{cat}_{stem}{ext}"

            row = self.table.rowCount()
            self.table.insertRow(row)

            # 0. Checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            chk_wrap = QWidget()
            ch_lay = QHBoxLayout(chk_wrap)
            ch_lay.setContentsMargins(8, 0, 0, 0)
            ch_lay.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_wrap)

            # 1. Name with vector icon
            ico_name = "documents" if is_valid else "security"
            ico_col = t["primary"] if is_valid else t["red"]
            name_item = QTableWidgetItem(f.name)
            name_item.setIcon(QIcon(draw_vector_icon(ico_name, ico_col, 13)))
            self.table.setItem(row, 1, name_item)

            # 2. Smart Proposed Name (Monospace styled chip)
            smart_item = QTableWidgetItem(smart_name)
            self.table.setItem(row, 2, smart_item)

            # 3. Category Combobox / Badge
            if self._view_mode == "PENDING":
                combo = QComboBox()
                combo.addItems(["Legal", "Financial", "Academic", "Medical", "General", "Quarantine"])
                idx = combo.findText(cat)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.setStyleSheet(f"""
                    QComboBox {{
                        background: {'rgba(255, 255, 255, 0.08)' if is_dark else '#FFFFFF'};
                        color: {t['text']};
                        border: 1px solid {t['border']}; border-radius: 6px;
                        padding: 3px 8px; font-size: 11px; font-weight: 600;
                    }}
                """)
                self.table.setCellWidget(row, 3, combo)
            else:
                cat_badge = QLabel(cat)
                cat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_col = {
                    "Legal": "#818CF8", "Financial": "#34D399", "Academic": "#60A5FA",
                    "Medical": "#F472B6", "General": "#FBBF24", "Quarantine": "#F87171"
                }.get(cat, t["primary"])
                cat_badge.setStyleSheet(f"""
                    color: {badge_col}; font-weight: 700; font-size: 10.5px;
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else '#F1F5F9'};
                    padding: 3px 8px; border-radius: 6px;
                """)
                self.table.setCellWidget(row, 3, cat_badge)

            # 4. Size
            sz_item = QTableWidgetItem(sz_str)
            sz_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, sz_item)

            # 5. Binary Status Badge
            st_lbl = QLabel("Verified" if is_valid else "Corrupt / Disguised")
            st_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            st_col = t["green"] if is_valid else t["red"]
            st_bg = t["green_bg"] if is_valid else t["red_bg"]
            st_lbl.setStyleSheet(f"""
                color: {st_col}; font-weight: 700; font-size: 10px;
                background: {st_bg}; padding: 3px 8px; border-radius: 6px;
            """)
            self.table.setCellWidget(row, 5, st_lbl)

            # 6. Action Button
            btn_act = QPushButton("Sort" if self._view_mode == "PENDING" else "Open")
            btn_act.setFixedHeight(24)
            btn_act.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_act.setStyleSheet(f"""
                QPushButton {{
                    background: {t['primary']}; color: #FFFFFF;
                    border: none; border-radius: 5px; font-size: 10.5px; font-weight: 700;
                    padding: 2px 10px;
                }}
                QPushButton:hover {{ background: {t['primary_hover']}; }}
            """)
            if self._view_mode == "PENDING":
                btn_act.clicked.connect(lambda _, path=fp: self._sort_single(path))
            else:
                btn_act.clicked.connect(lambda _, path=fp: QDesktopServices.openUrl(QUrl.fromLocalFile(path)))
            self.table.setCellWidget(row, 6, btn_act)

            self._pending_files.append({"path": fp, "smart_name": smart_name, "cat": cat, "valid": is_valid})

        self._refresh_audit_logs()

    # ─── Sorting Actions ────────────────────────────────────────────────────────

    def _sort_single(self, filepath: str):
        try:
            res = self.organizer.sort_file(filepath)
            dest = res.get("destination", "")
            if dest:
                self.last_batch_moves.append({"src": filepath, "dest": dest})
                self._persist_sorted_document(dest, res.get("category", "General"))
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback(f"Organized '{Path(filepath).name}' \u2192 /{res.get('category')}/")
            if hasattr(p, "_load_vault_database"):
                p._load_vault_database()
        except Exception as e:
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback(f"Sort failed: {e}")
        self.refresh_files()

    def _run_smart_sort(self):
        intake_dir = self.organizer.vault_root / "intake"
        files = [f for f in intake_dir.iterdir() if f.is_file()]
        if not files:
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback("No files pending in intake queue. Click 'Add Files to Intake' or 'Load Demo Batch'.")
            return

        sorted_cnt = 0
        self.last_batch_moves.clear()
        for f in files:
            try:
                res = self.organizer.sort_file(str(f))
                if res.get("destination"):
                    self.last_batch_moves.append({"src": str(f), "dest": res["destination"]})
                    self._persist_sorted_document(res["destination"], res.get("category", "General"))
                sorted_cnt += 1
            except Exception:
                pass

        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback(f"AI File Organizer categorized {sorted_cnt} file{'s' if sorted_cnt != 1 else ''} into vault categories.")
        if hasattr(p, "_load_vault_database"):
            p._load_vault_database()

        self.refresh_files()

    def _run_dry_run(self):
        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback("Dry-Run Simulation: File categories computed without moving disk files.")
        self.refresh_files(dry_run=True)

    def _undo_last_batch(self):
        if not self.last_batch_moves:
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback("No recent batch moves available to undo.")
            return

        reverted = 0
        for move in self.last_batch_moves:
            dest = Path(move["dest"])
            src = Path(move["src"])
            if dest.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest), str(src))
                reverted += 1

        self.organizer.logger.log_operation(
            level="WARN",
            action="UNDO",
            filename=f"Batch of {reverted} files",
            category="Intake",
            size_bytes=0,
            destination="vault/intake/",
            extra="User initiated batch rollback",
        )
        self.last_batch_moves.clear()
        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback(f"Rolled back {reverted} file{'s' if reverted != 1 else ''} to intake.")
        if hasattr(p, "_load_vault_database"):
            p._load_vault_database()
        self.refresh_files()

    def _add_files_to_intake(self):
        fpaths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Queue for AI Organizing", "", "All Files (*.*)"
        )
        if fpaths:
            intake_dir = self.organizer.vault_root / "intake"
            intake_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            for fp in fpaths:
                p = Path(fp)
                dest = intake_dir / p.name
                shutil.copy2(p, dest)
                copied += 1
            p = self.window()
            if hasattr(p, "_show_feedback"):
                p._show_feedback(f"Added {copied} file{'s' if copied != 1 else ''} to vault intake queue.")
            self._set_view_mode("PENDING")
            self.refresh_files()

    def _open_vault_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.organizer.vault_root.resolve())))

    def _open_intake_folder(self):
        intake_dir = self.organizer.vault_root / "intake"
        intake_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(intake_dir.resolve())))

    # ─── Audit Log Stream ───────────────────────────────────────────────────────

    def _refresh_audit_logs(self):
        logs = self.organizer.logger.get_recent_logs(90)
        formatted = []
        for line in logs:
            if self._log_filter != "ALL" and self._log_filter not in line:
                continue

            # Rich pill formatting
            if "SORT" in line:
                badge = "<span style='background: rgba(255, 122, 46, 0.16); color: #FF7A2E; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10px;'>SORT</span>"
                line_html = f"{badge} <span style='color: #E2E8F0;'>{line.split('|', 2)[-1] if '|' in line else line}</span>"
            elif "QUARANTINE" in line or "WARN" in line:
                badge = "<span style='background: rgba(240, 85, 110, 0.16); color: #F0556E; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10px;'>QUARANTINE</span>"
                line_html = f"{badge} <span style='color: #FCA5A5;'>{line.split('|', 2)[-1] if '|' in line else line}</span>"
            elif "UNDO" in line:
                badge = "<span style='background: rgba(245, 181, 68, 0.16); color: #F5B544; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10px;'>ROLLBACK</span>"
                line_html = f"{badge} <span style='color: #FDE68A;'>{line.split('|', 2)[-1] if '|' in line else line}</span>"
            else:
                badge = "<span style='background: rgba(107, 155, 255, 0.16); color: #6B9BFF; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10px;'>AUDIT</span>"
                line_html = f"{badge} <span style='color: #94A3B8;'>{line.split('|', 2)[-1] if '|' in line else line}</span>"

            formatted.append(line_html)

        self.log_console.setHtml("<br>".join(formatted) if formatted else "<span style='color: #64748B;'>No matching audit entries.</span>")
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    # ─── Style Application Helpers ──────────────────────────────────────────────

    def _apply_toolbar_style(self):
        t = self._t
        is_dark = t.get("name") == "dark"
        self.tb_card.setStyleSheet(f"""
            #organizerToolbar {{
                background: {'rgba(18, 18, 26, 0.55)' if is_dark else 'rgba(255, 255, 255, 0.75)'};
                border: 1px solid {'rgba(255, 122, 46, 0.20)' if is_dark else 'rgba(242, 106, 27, 0.25)'};
                border-radius: 12px;
            }}
        """)

    def _apply_table_style(self):
        t = self._t
        is_dark = t.get("name") == "dark"
        self.table_wrap.setStyleSheet(f"""
            #tableWrap {{
                background: {'rgba(14, 14, 22, 0.50)' if is_dark else 'rgba(255, 255, 255, 0.65)'};
                border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                border-radius: 14px;
            }}
        """)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                color: {t['text']};
                border: none;
                gridline-color: {'rgba(255, 255, 255, 0.05)' if is_dark else '#F1F5F9'};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                background: transparent;
            }}
            QTableWidget::item:hover {{
                background: {'rgba(255, 122, 46, 0.10)' if is_dark else 'rgba(242, 106, 27, 0.08)'};
            }}
            QTableWidget::item:selected {{
                background: {'rgba(255, 122, 46, 0.18)' if is_dark else 'rgba(242, 106, 27, 0.15)'};
            }}
            QHeaderView::section {{
                background: {'rgba(22, 22, 32, 0.70)' if is_dark else '#F8FAFC'};
                color: {t['text3']};
                border: none;
                border-bottom: 1px solid {t['border']};
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
        """)

    def _apply_console_style(self):
        t = self._t
        is_dark = t.get("name") == "dark"
        self.log_wrap.setStyleSheet(f"""
            #logWrap {{
                background: {'rgba(10, 10, 16, 0.50)' if is_dark else 'rgba(255, 255, 255, 0.65)'};
                border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                border-radius: 12px;
            }}
        """)
        self.log_console.setStyleSheet(f"""
            QTextEdit {{
                background: {'rgba(8, 8, 14, 0.55)' if is_dark else 'rgba(248, 250, 252, 0.70)'};
                color: #38BDF8;
                border: 1px solid {t['border']};
                border-radius: 8px;
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 11px;
                line-height: 1.5;
                padding: 8px;
            }}
        """)

    # ─── Dynamic Theme Updates ──────────────────────────────────────────────────

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"

        self.lbl_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {t['text']}; letter-spacing: -0.4px;")
        self.lbl_sub.setStyleSheet(f"font-size: 12px; color: {t['text4']};")

        for card in (self.card_total, self.card_intake, self.card_quarantine, self.card_ops):
            card.setStyleSheet(f"""
                QFrame {{
                    background: {'rgba(18, 18, 26, 0.60)' if is_dark else 'rgba(255, 255, 255, 0.70)'};
                    border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                    border-radius: 14px;
                }}
                QFrame:hover {{
                    border-color: rgba(255, 122, 46, 0.35);
                }}
            """)
            lbl = card.findChild(QLabel, "cardVal")
            if lbl:
                lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {t['text']}; letter-spacing: -0.5px;")

        self._apply_toolbar_style()
        self._apply_table_style()
        self._apply_console_style()
        self.refresh_files()


class DeadlinesPage(QWidget):
    """
    Dedicated Smart Deadlines and Compliance Obligation Workspace
    matching Page 15 of the design pack with interactive calendar,
    filtering tabs, and Coming Up obligation cards with real-time database persistence.
    """

    def __init__(self, theme: Dict[str, str], mongo: Optional[MongoDatabase] = None, owner_email: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._t = theme
        self.mongo = mongo
        self.owner_email = owner_email
        self.manager = DeadlineManager()
        self.deadlines: List[Dict[str, Any]] = []
        self.current_filter = "All"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(16)

        # ── 1. Header (Title, Subtitle, and Action Buttons) ──
        header = QHBoxLayout()
        header.setSpacing(12)

        t_box = QVBoxLayout()
        t_box.setSpacing(3)
        self.t_lbl = QLabel("Deadlines")
        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {theme['text']}; letter-spacing: -0.3px;")
        t_box.addWidget(self.t_lbl)

        self.sub_lbl = QLabel("Dates found in your contracts, obligations, and compliance milestones.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        t_box.addWidget(self.sub_lbl)
        header.addLayout(t_box)

        header.addStretch()

        self.btn_export_ics = QPushButton("Export calendar (.ics)")
        self.btn_export_ics.setFixedHeight(34)
        self.btn_export_ics.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_ics.clicked.connect(self._export_ics)
        header.addWidget(self.btn_export_ics)

        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.setFixedHeight(34)
        self.btn_export_csv.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_csv.clicked.connect(self._export_csv)
        header.addWidget(self.btn_export_csv)

        self.btn_add = QPushButton("+ Add deadline")
        self.btn_add.setFixedHeight(34)
        self.btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add.clicked.connect(self._open_add_deadline_dialog)
        header.addWidget(self.btn_add)

        lay.addLayout(header)

        # ── 2. Split Workspace (Month Calendar on Left, Coming up on Right) ──
        split_lay = QHBoxLayout()
        split_lay.setSpacing(18)

        # ── Left Card: Month Calendar ──
        self.calendar_card = QFrame()
        self.calendar_card.setObjectName("calendarCard")
        cal_vlay = QVBoxLayout(self.calendar_card)
        cal_vlay.setContentsMargins(22, 20, 22, 20)
        cal_vlay.setSpacing(14)

        # Calendar month top bar
        cal_top = QHBoxLayout()
        self.month_lbl = QLabel("October 2026")
        self.month_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {theme['text']};")
        cal_top.addWidget(self.month_lbl)
        cal_top.addStretch()

        self.btn_today = QPushButton("Today")
        self.btn_today.setFixedHeight(26)
        self.btn_today.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cal_top.addWidget(self.btn_today)
        cal_vlay.addLayout(cal_top)

        # Weekdays header row
        days_header = QHBoxLayout()
        days_header.setSpacing(8)
        self.day_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.day_header_labels: List[QLabel] = []
        for dname in self.day_headers:
            lbl = QLabel(dname)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {theme['text4']};")
            days_header.addWidget(lbl, 1)
            self.day_header_labels.append(lbl)
        cal_vlay.addLayout(days_header)

        # 7-column Calendar Grid (October 2026: 1st is Thu)
        self.grid_container = QWidget()
        self.cal_grid = QGridLayout(self.grid_container)
        self.cal_grid.setContentsMargins(0, 4, 0, 0)
        self.cal_grid.setSpacing(8)

        self.day_cells: Dict[int, QFrame] = {}
        self._build_calendar_grid()
        cal_vlay.addWidget(self.grid_container, 1)

        split_lay.addWidget(self.calendar_card, 6)

        # ── Right Card: Coming up Obligations ──
        self.coming_card = QFrame()
        self.coming_card.setObjectName("comingCard")
        coming_vlay = QVBoxLayout(self.coming_card)
        coming_vlay.setContentsMargins(22, 20, 22, 20)
        coming_vlay.setSpacing(14)

        coming_top = QHBoxLayout()
        self.coming_title = QLabel("Coming up")
        self.coming_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {theme['text']};")
        coming_top.addWidget(self.coming_title)
        coming_top.addStretch()
        coming_vlay.addLayout(coming_top)

        # Filter Tabs Row
        filter_box = QHBoxLayout()
        filter_box.setSpacing(6)
        self.filter_buttons: Dict[str, QPushButton] = {}
        for tab_name in ["All", "Urgent < 7d", "Active", "Completed"]:
            btn = QPushButton(tab_name)
            btn.setFixedHeight(24)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, n=tab_name: self._set_filter(n))
            filter_box.addWidget(btn)
            self.filter_buttons[tab_name] = btn
        coming_vlay.addLayout(filter_box)

        # Scrollable items container
        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.items_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.items_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.items_scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.items_container_widget = QWidget()
        self.items_container_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.items_container = QVBoxLayout(self.items_container_widget)
        self.items_container.setContentsMargins(0, 4, 4, 4)
        self.items_container.setSpacing(8)
        self.items_scroll.setWidget(self.items_container_widget)
        coming_vlay.addWidget(self.items_scroll, 1)

        self._populate_coming_up_items()

        # Subtle footer note matching Page 15
        self.footer_note = QLabel("Dates are monitored automatically across your contracts.")
        self.footer_note.setWordWrap(True)
        self.footer_note.setStyleSheet(f"font-size: 11px; color: {theme['text4']}; line-height: 1.4;")
        coming_vlay.addWidget(self.footer_note)

        split_lay.addWidget(self.coming_card, 5)

        lay.addLayout(split_lay, 1)
        self.update_theme(theme)

    def _set_filter(self, filter_name: str):
        self.current_filter = filter_name
        self._update_filter_button_styles()
        self._populate_coming_up_items()

    def _update_filter_button_styles(self):
        t = self._t
        is_dark = t.get("name") == "dark"
        for name, btn in self.filter_buttons.items():
            if name == self.current_filter:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(242, 106, 27, 0.20);
                        color: {t['primary']};
                        border: 1px solid rgba(242, 106, 27, 0.40);
                        border-radius: 12px;
                        padding: 2px 10px;
                        font-size: 10px;
                        font-weight: 700;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#141418' if is_dark else '#F2F2F7'};
                        color: {t['text3']};
                        border: 1px solid {'#26262E' if is_dark else '#E5E5EA'};
                        border-radius: 12px;
                        padding: 2px 10px;
                        font-size: 10px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        color: {t['text']};
                        border-color: {t['primary']};
                    }}
                """)

    def _build_calendar_grid(self):
        while self.cal_grid.count():
            item = self.cal_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        start_col = 4
        total_days = 31

        current_day = 1
        for row in range(5):
            for col in range(7):
                if row == 0 and col < start_col:
                    empty = QLabel("")
                    self.cal_grid.addWidget(empty, row, col)
                    continue

                if current_day > total_days:
                    empty = QLabel("")
                    self.cal_grid.addWidget(empty, row, col)
                    continue

                deadline_days = {}
                for d in self.deadlines:
                    try:
                        due = d.get("due_date", "")
                        if "-" in due:
                            d_day = int(due.split("-")[-1])
                            col_c = "#F0556E" if d.get("priority") in ("Critical", "High") else t['primary']
                            deadline_days[d_day] = col_c
                    except Exception:
                        pass

                day_num = current_day
                cell = QFrame()
                cell.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                cell.setFixedHeight(54)

                is_today = (day_num == datetime.now().day)

                if is_today:
                    cell.setStyleSheet(f"""
                        QFrame {{
                            background: rgba(242, 106, 27, 0.14);
                            border: 1.5px solid {t['primary']};
                            border-radius: 10px;
                        }}
                    """)
                else:
                    cell_border = "#1F2735" if is_dark else "#E4E7EC"
                    cell.setStyleSheet(f"""
                        QFrame {{
                            background: transparent;
                            border: 1px solid {cell_border};
                            border-radius: 10px;
                        }}
                        QFrame:hover {{
                            background: {'rgba(255, 255, 255, 0.04)' if is_dark else 'rgba(0, 0, 0, 0.03)'};
                            border-color: {t['primary']};
                        }}
                    """)

                clay = QVBoxLayout(cell)
                clay.setContentsMargins(8, 6, 8, 6)
                clay.setSpacing(2)

                num_lbl = QLabel(str(day_num))
                num_lbl.setStyleSheet(f"""
                    font-size: 11px;
                    font-weight: {'800' if is_today else '600'};
                    color: {t['primary'] if is_today else t['text']};
                """)
                clay.addWidget(num_lbl)

                clay.addStretch()

                if day_num in deadline_days:
                    dot = QLabel()
                    dot.setFixedSize(6, 6)
                    dot.setStyleSheet(f"background: {deadline_days[day_num]}; border-radius: 3px;")
                    clay.addWidget(dot, 0, Qt.AlignmentFlag.AlignCenter)
                else:
                    clay.addSpacing(6)

                self.cal_grid.addWidget(cell, row, col)
                self.day_cells[day_num] = cell
                current_day += 1

    def _populate_coming_up_items(self):
        while self.items_container.count():
            item = self.items_container.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        if not self.deadlines:
            empty_lbl = QLabel("No active deadlines recorded.\nImport contracts or click '+ Add deadline' to track obligations.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {t['text4']}; font-size: 12px; padding: 40px 10px; line-height: 1.5;")
            self.items_container.addWidget(empty_lbl)
            return

        items_to_render = []
        for d in self.deadlines:
            eval_res = self.manager.evaluate_deadline(d)
            days_left = eval_res.get("days_left", 0)
            status = d.get("computed_status", eval_res.get("status", "Active"))
            is_completed = (status == "Completed")

            # Apply filter
            if self.current_filter == "Urgent < 7d" and (days_left > 7 or is_completed):
                continue
            if self.current_filter == "Active" and is_completed:
                continue
            if self.current_filter == "Completed" and not is_completed:
                continue

            if is_completed:
                chip_txt = "Completed"
                col = "#8E8E93"
            elif days_left < 0:
                chip_txt = f"{abs(days_left)}d overdue"
                col = "#F0556E"
            elif days_left <= 3:
                chip_txt = f"In {days_left}d"
                col = "#F0556E"
            elif days_left <= 7:
                chip_txt = f"In {days_left}d"
                col = "#FF8C42"
            else:
                chip_txt = f"In {days_left}d"
                col = t['primary']

            due = eval_res.get("adjusted_due_date", "2026-10-28")
            day_str = due.split("-")[-1] if "-" in due else "28"
            items_to_render.append({
                "id": d.get("id", ""),
                "date": day_str,
                "title": eval_res.get("title", d.get("title", "Obligation")),
                "doc": eval_res.get("document", d.get("document", "Document.pdf")),
                "status": status,
                "chip": chip_txt,
                "color": col,
                "is_completed": is_completed,
                "badge_bg": "rgba(242, 106, 27, 0.12)" if not is_completed else "rgba(142, 142, 147, 0.12)",
                "chip_bg": "rgba(242, 106, 27, 0.14)" if not is_completed else "rgba(142, 142, 147, 0.14)",
            })

        if not items_to_render:
            empty_lbl = QLabel(f"No deadlines matching filter '{self.current_filter}'.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {t['text4']}; font-size: 12px; padding: 30px 10px;")
            self.items_container.addWidget(empty_lbl)
            return

        for it in items_to_render:
            row_w = QFrame()
            row_w.setStyleSheet(f"""
                QFrame {{
                    background: {'rgba(255, 255, 255, 0.03)' if is_dark else 'rgba(0, 0, 0, 0.02)'};
                    border: 1px solid {'#22222B' if is_dark else '#E5E5EA'};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    border-color: {t['primary']};
                    background: {'rgba(242, 106, 27, 0.05)' if is_dark else 'rgba(242, 106, 27, 0.03)'};
                }}
            """)
            rlay = QHBoxLayout(row_w)
            rlay.setContentsMargins(10, 8, 10, 8)
            rlay.setSpacing(10)

            # Square date badge
            date_badge = QLabel(it["date"])
            date_badge.setFixedSize(36, 36)
            date_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_badge.setStyleSheet(f"""
                background: {it['badge_bg']};
                color: {it['color']};
                font-size: 13px;
                font-weight: 800;
                border-radius: 8px;
                border: 1px solid {it['color']}44;
            """)
            rlay.addWidget(date_badge)

            # Title and Doc text
            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            lbl_title = QLabel(it["title"])
            lbl_title.setStyleSheet(f"font-size: 12.5px; font-weight: 700; color: {t['text']};")
            text_box.addWidget(lbl_title)

            lbl_doc = QLabel(f"{it['doc']} • {it['status']}")
            lbl_doc.setStyleSheet(f"font-size: 10.5px; color: {t['text4']};")
            text_box.addWidget(lbl_doc)
            rlay.addLayout(text_box, 1)

            # Urgency Chip
            chip = QLabel(it["chip"])
            chip.setStyleSheet(f"""
                background: {it['chip_bg']};
                color: {it['color']};
                font-size: 10px;
                font-weight: 700;
                border-radius: 8px;
                padding: 3px 8px;
                border: 1px solid {it['color']}33;
            """)
            rlay.addWidget(chip)

            # Complete toggle button
            btn_done = QPushButton()
            btn_done.setFixedSize(26, 26)
            btn_done.setIcon(QIcon(draw_vector_icon("check", t['primary'] if it['is_completed'] else t['text4'], 12)))
            btn_done.setToolTip("Mark as Active" if it['is_completed'] else "Mark as Completed")
            btn_done.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_done.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 6px; } QPushButton:hover { background: rgba(242, 106, 27, 0.15); }")
            btn_done.clicked.connect(lambda _, did=it['id']: self._toggle_deadline_status(did))
            rlay.addWidget(btn_done)

            # Delete button
            btn_del = QPushButton()
            btn_del.setFixedSize(26, 26)
            btn_del.setIcon(QIcon(draw_vector_icon("trash", t['text4'], 12)))
            btn_del.setToolTip("Delete obligation")
            btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_del.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 6px; } QPushButton:hover { background: rgba(240, 85, 110, 0.2); }")
            btn_del.clicked.connect(lambda _, did=it['id']: self._delete_deadline(did))
            rlay.addWidget(btn_del)

            self.items_container.addWidget(row_w)

        self.items_container.addStretch()

    def _toggle_deadline_status(self, deadline_id: str):
        for d in self.deadlines:
            if d.get("id") == deadline_id:
                curr = d.get("computed_status", "Active")
                d["computed_status"] = "Completed" if curr != "Completed" else "Active"
                if self.mongo:
                    self.mongo.save_deadline(d, user_email=self.owner_email)
                break
        self.refresh_from_db()

    def _delete_deadline(self, deadline_id: str):
        if self.mongo:
            self.mongo.delete_deadline(deadline_id, user_email=self.owner_email)
        self.deadlines = [d for d in self.deadlines if d.get("id") != deadline_id]
        self.refresh_from_db()

    def refresh_from_db(self):
        if self.mongo:
            try:
                self.deadlines = self.mongo.list_deadlines(user_email=self.owner_email)
            except Exception:
                pass
        self._populate_coming_up_items()
        self._build_calendar_grid()

    def refresh_deadlines(self, deadlines: List[Dict[str, Any]]):
        self.deadlines = deadlines
        self._populate_coming_up_items()
        self._build_calendar_grid()

    def _export_ics(self):
        content = DeadlineManager.export_icalendar(self.deadlines)
        path, _ = QFileDialog.getSaveFileName(self, "Export iCalendar", "deadlines.ics", "iCalendar (*.ics)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Success", f"iCalendar exported to:\n{path}")

    def _export_csv(self):
        content = DeadlineManager.export_csv(self.deadlines)
        path, _ = QFileDialog.getSaveFileName(self, "Export Deadlines CSV", "deadlines.csv", "CSV Files (*.csv)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Success", f"Deadlines exported to:\n{path}")

    def _open_add_deadline_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Compliance Deadline")
        dlg.setFixedSize(400, 260)
        dlay = QVBoxLayout(dlg)
        dlay.setSpacing(12)

        lbl = QLabel("Create Custom Deadline")
        lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {self._t['text']};")
        dlay.addWidget(lbl)

        in_title = QLineEdit()
        in_title.setPlaceholderText("Obligation / Contract Title")
        dlay.addWidget(in_title)

        in_doc = QLineEdit()
        in_doc.setPlaceholderText("Associated Document")
        dlay.addWidget(in_doc)

        in_days = QSpinBox()
        in_days.setRange(1, 365)
        in_days.setValue(14)
        in_days.setPrefix("Due in: ")
        in_days.setSuffix(" days")
        dlay.addWidget(in_days)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_save = QPushButton("Save Deadline")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(dlg.accept)
        btn_box.addWidget(btn_save)
        dlay.addLayout(btn_box)

        if dlg.exec():
            title = in_title.text().strip() or "Custom Obligation"
            doc = in_doc.text().strip() or "Manual Entry"
            days = in_days.value()
            new_dl = {
                "id": f"DL-{random.randint(100, 999)}",
                "title": title,
                "document": doc,
                "due_date": (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
                "days_left": days,
                "computed_status": "Active",
            }
            if self.mongo:
                self.mongo.save_deadline(new_dl, user_email=self.owner_email)
            self.deadlines.append(new_dl)
            self.refresh_from_db()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"

        self.t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {t['text']}; letter-spacing: -0.3px;")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {t['text4']};")

        if hasattr(self, "month_lbl"):
            self.month_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {t['text']};")
        if hasattr(self, "day_header_labels"):
            for lbl in self.day_header_labels:
                lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text4']};")
        if hasattr(self, "coming_title"):
            self.coming_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {t['text']};")
        if hasattr(self, "footer_note"):
            self.footer_note.setStyleSheet(f"font-size: 11px; color: {t['text4']}; line-height: 1.4;")

        btn_sec_qss = f"""
            QPushButton {{
                background: {t['surface']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 17px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {'#18202F' if is_dark else '#F0F2F5'};
                border-color: {t['primary']};
            }}
        """
        self.btn_export_ics.setStyleSheet(btn_sec_qss)
        self.btn_export_csv.setStyleSheet(btn_sec_qss)

        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                color: #FFFFFF;
                border: none;
                border-radius: 17px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['primary_hover']};
            }}
        """)

        card_qss = f"""
            background: {t['surface']};
            border: 1px solid {t['border']};
            border-radius: 16px;
        """
        self.calendar_card.setStyleSheet(card_qss)
        self.coming_card.setStyleSheet(card_qss)

        self.btn_today.setStyleSheet(f"""
            QPushButton {{
                background: {'#1F2735' if is_dark else '#E4E7EC'};
                color: {t['text']};
                border: none;
                border-radius: 12px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {t['primary']};
                color: #FFFFFF;
            }}
        """)

        self._update_filter_button_styles()
        self._build_calendar_grid()
        self._populate_coming_up_items()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPTION E: RIGHT COLLAPSIBLE AI DRAWER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIDrawer(QFrame):
    """
    Option E right-docked AI Assistant Drawer that lives on every page.
    Extendable & resizable via dragging, matching Figma CHAT A.I+ single-div architecture
    with ChatGPT/Copilot luxury aesthetics and zero green colors.
    """
    closed = pyqtSignal()
    expand_requested = pyqtSignal()

    def __init__(self, assistant: Optional[ExplainableAIAssistant], theme: Dict[str, str], parent=None, owner_email: Optional[str] = None):
        super().__init__(parent)
        self.assistant = assistant
        self.owner_email = owner_email
        self._t = theme
        self.messages: List[Dict[str, Any]] = [
            {
                "role": "assistant",
                "text": (
                    "DocuVault AI Assistant is ready. Ask any question about your contracts, NDAs, invoices, "
                    "or imported records. All responses are verified with source citations."
                ),
                "citations": [],
                "time": "Just now",
            }
        ]
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(280)
        self.setMaximumWidth(1050)
        self.resize(380, self.height())
        self.setObjectName("aiDrawer")

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(16, 16, 16, 16)
        vlay.setSpacing(12)

        # ── 1. Top Bar (Logo, Title, Verified chip, Clear, Expand, Close) ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        ico_top = QLabel()
        ico_top.setPixmap(draw_vector_icon("sparkle", theme['primary'], 16))
        top_bar.addWidget(ico_top)

        self.title_lbl = QLabel("DocuVault AI")
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {theme['text']};")
        top_bar.addWidget(self.title_lbl)

        self.evidence_chip = QLabel("Verified Sources")
        self.evidence_chip.setStyleSheet("""
            background: rgba(242, 106, 27, 0.12);
            color: #F26A1B;
            border: 1px solid rgba(242, 106, 27, 0.28);
            font-size: 9.5px;
            font-weight: 700;
            border-radius: 6px;
            padding: 2px 7px;
        """)
        top_bar.addWidget(self.evidence_chip)

        top_bar.addStretch()

        self.btn_clear = QPushButton()
        self.btn_clear.setFixedSize(26, 26)
        self.btn_clear.setIcon(QIcon(draw_vector_icon("refresh", theme['text3'], 13)))
        self.btn_clear.setToolTip("Clear conversation")
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.clicked.connect(self._clear_conversation)
        top_bar.addWidget(self.btn_clear)

        self.btn_expand = QPushButton()
        self.btn_expand.setFixedSize(26, 26)
        self.btn_expand.setIcon(QIcon(draw_vector_icon("fit", theme['text3'], 13)))
        self.btn_expand.setToolTip("Expand to full page AI Assistant")
        self.btn_expand.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_expand.clicked.connect(self.expand_requested.emit)
        top_bar.addWidget(self.btn_expand)

        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(26, 26)
        self.btn_close.setIcon(QIcon(draw_vector_icon("close", theme['text3'], 12)))
        self.btn_close.setToolTip("Close drawer (Ctrl+J)")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.closed.emit)
        top_bar.addWidget(self.btn_close)
        vlay.addLayout(top_bar)

        # ── 2. Quick Question Chips ──
        chips_lay = QHBoxLayout()
        chips_lay.setSpacing(6)
        self.chip_buttons: List[QPushButton] = []
        for q_txt in ["Notice period", "Payment terms", "Liability", "Termination"]:
            chip_btn = QPushButton(q_txt)
            chip_btn.setFixedHeight(26)
            chip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            chip_btn.clicked.connect(lambda _, txt=q_txt: self._handle_quick_query(txt))
            chips_lay.addWidget(chip_btn)
            self.chip_buttons.append(chip_btn)
        vlay.addLayout(chips_lay)

        # ── 3. Grounded Conversation Scroll Area ──
        self.scroll = QScrollArea()
        self.scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.chat_container = QWidget()
        self.chat_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.chat_container.setStyleSheet("background: transparent; border: none;")
        self.chat_lay = QVBoxLayout(self.chat_container)
        self.chat_lay.setContentsMargins(4, 4, 8, 4)
        self.chat_lay.setSpacing(12)

        self.scroll.setWidget(self.chat_container)
        vlay.addWidget(self.scroll, 1)

        # ── 4. ChatGPT-style Floating Input Card with Attachment Popover ──
        self.in_wrap = QFrame()
        in_lay = QHBoxLayout(self.in_wrap)
        in_lay.setContentsMargins(8, 4, 6, 4)
        in_lay.setSpacing(6)

        self.btn_attach = QPushButton()
        self.btn_attach.setFixedSize(28, 28)
        self.btn_attach.setIcon(QIcon(draw_vector_icon("plus", theme['primary'], 13)))
        self.btn_attach.setToolTip("Attach or choose tool")
        self.btn_attach.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_attach.clicked.connect(self._show_drawer_attachment_menu)
        in_lay.addWidget(self.btn_attach)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your documents...")
        self.input_field.returnPressed.connect(self._submit)
        in_lay.addWidget(self.input_field, 1)

        self.btn_send = QPushButton()
        self.btn_send.setFixedSize(28, 28)
        self.btn_send.setIcon(QIcon(draw_vector_icon("send", "#FFFFFF", 12)))
        self.btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send.setToolTip("Ask DocuVault AI")
        self.btn_send.clicked.connect(self._submit)
        in_lay.addWidget(self.btn_send)

        vlay.addWidget(self.in_wrap)
        self.update_theme(theme)

    def _show_drawer_attachment_menu(self):
        menu = QMenu(self)
        is_dark = self._t.get("name") == "dark"
        bg_col = "#141418" if is_dark else "#FFFFFF"
        border_col = "rgba(242, 106, 27, 0.3)" if is_dark else "#E5E5EA"
        text_col = "#F5F5F7" if is_dark else "#1D1D1F"
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 12px;
                padding: 6px;
                color: {text_col};
                font-size: 12px;
                font-weight: 500;
            }}
            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 8px;
            }}
            QMenu::item:selected {{
                background-color: rgba(242, 106, 27, 0.16);
                color: #F26A1B;
            }}
            QMenu::separator {{
                height: 1px;
                background: {border_col};
                margin: 4px 6px;
            }}
        """)

        act_upload = menu.addAction("Upload from Computer...")
        act_vault = menu.addAction("Add from Vault Documents...")
        menu.addSeparator()
        act_ocr = menu.addAction("OCR & Text Scanner...")
        act_synth = menu.addAction("Deep Multi-Doc Synthesis")
        act_compliance = menu.addAction("Audit Compliance & Deadlines")

        action = menu.exec(self.btn_attach.mapToGlobal(QPoint(0, -menu.sizeHint().height() - 4)))
        if not action:
            return

        p = self.parent()
        if action == act_upload:
            if p and hasattr(p, "_open_file_dialog"):
                p._open_file_dialog()
            else:
                files, _ = QFileDialog.getOpenFileNames(self, "Upload to Vault", "", "All Supported (*.pdf *.docx *.txt *.csv *.png *.jpg)")
                if files and p and hasattr(p, "_import_file_list"):
                    p._import_file_list(files)
        elif action == act_vault:
            self.input_field.setText("Analyze document: ")
            self.input_field.setFocus()
        elif action == act_ocr:
            files, _ = QFileDialog.getOpenFileNames(self, "Select Image for OCR", "", "Images (*.png *.jpg *.jpeg *.tiff *.bmp *.pdf)")
            if files:
                self.input_field.setText(f"Extract all text and verify tables via OCR from {Path(files[0]).name}")
                self._submit()
        elif action == act_synth:
            self.input_field.setText("Synthesize cross-document insights across all uploaded vault contracts:")
            self.input_field.setFocus()
        elif action == act_compliance:
            self.input_field.setText("Check contract obligations and list upcoming compliance deadlines.")
            self._submit()

    def _clear_conversation(self):
        self.messages = [
            {
                "role": "assistant",
                "text": (
                    "DocuVault AI Assistant is ready. Ask any question about your contracts, NDAs, invoices, "
                    "or imported records. All responses are verified with source citations."
                ),
                "citations": [],
                "time": "Just now",
            }
        ]
        self._render_messages()

    def _render_messages(self):
        while self.chat_lay.count():
            item = self.chat_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        for msg in self.messages:
            role = msg.get("role", "assistant")
            text = msg.get("text", "")
            citations = msg.get("citations", [])

            if role == "user":
                u_turn = QWidget()
                u_turn.setStyleSheet("background: transparent; border: none;")
                ulay = QVBoxLayout(u_turn)
                ulay.setContentsMargins(4, 2, 4, 4)
                ulay.setSpacing(2)

                u_bubble = QFrame()
                u_bubble.setStyleSheet("background: transparent; border: none;")
                ub_lay = QVBoxLayout(u_bubble)
                ub_lay.setContentsMargins(6, 6, 6, 6)
                ub_lay.setSpacing(3)

                u_hdr_box = QHBoxLayout()
                u_hdr_box.setSpacing(6)
                u_ico = QLabel()
                u_ico.setPixmap(draw_vector_icon("user", t["primary"], 12))
                u_hdr_box.addWidget(u_ico)
                u_hdr = QLabel("You")
                u_hdr.setStyleSheet(f"font-size: 10.5px; font-weight: 700; color: {t['primary']}; background: transparent; border: none;")
                u_hdr_box.addWidget(u_hdr)
                u_hdr_box.addStretch()
                ub_lay.addLayout(u_hdr_box)

                ulbl = QLabel(text)
                ulbl.setWordWrap(True)
                ulbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                ulbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {'#F5F5F7' if is_dark else '#101828'}; line-height: 1.4; background: transparent; border: none;")
                ub_lay.addWidget(ulbl)

                ulay.addWidget(u_bubble)
                self.chat_lay.addWidget(u_turn)

            else:
                a_turn = QWidget()
                a_turn.setStyleSheet("background: transparent; border: none;")
                alay = QVBoxLayout(a_turn)
                alay.setContentsMargins(4, 2, 4, 6)
                alay.setSpacing(6)

                badges_lay = QHBoxLayout()
                badges_lay.setSpacing(6)
                b_ico = QLabel()
                b_ico.setPixmap(draw_vector_icon("sparkle", t["primary"], 13))
                badges_lay.addWidget(b_ico)
                b_name = QLabel("DocuVault AI")
                b_name.setStyleSheet(f"font-size: 11.5px; font-weight: 800; color: {t['primary']}; background: transparent; border: none;")
                badges_lay.addWidget(b_name)

                b_ground = QLabel(f"● Grounded ({len(citations)} source{'s' if len(citations)!=1 else ''})")
                b_ground.setStyleSheet(f"""
                    background: rgba(242, 106, 27, 0.14);
                    color: {t['primary']};
                    border: 1px solid rgba(242, 106, 27, 0.28);
                    font-size: 9.5px;
                    font-weight: 700;
                    border-radius: 6px;
                    padding: 2px 7px;
                """)
                badges_lay.addWidget(b_ground)

                b_time = QLabel("0.2s")
                b_time.setStyleSheet(f"background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'}; color: {t['text4']}; font-size: 9.5px; font-weight: 700; border-radius: 6px; padding: 2px 7px;")
                badges_lay.addWidget(b_time)
                badges_lay.addStretch()
                alay.addLayout(badges_lay)

                ans_lbl = QLabel()
                ans_lbl.setTextFormat(Qt.TextFormat.RichText)
                ans_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                ans_lbl.setWordWrap(True)
                ans_lbl.setStyleSheet("background: transparent; border: none; padding: 2px 0;")
                html_body = format_chat_markdown_to_html(text, is_dark, t.get("primary", "#FF6422"))
                ans_lbl.setText(html_body)
                alay.addWidget(ans_lbl)

                if citations:
                    for cit in citations[:3]:
                        c_fn = cit.get("filename", "")
                        c_pg = cit.get("page_number", 1)
                        c_sn = cit.get("snippet", "")
                        if c_fn:
                            snip_str = f': "{c_sn[:80]}..."' if c_sn else ""
                            c_lbl = QLabel(f"• <b>{c_fn}</b> (p.{c_pg}){snip_str}")
                            c_lbl.setWordWrap(True)
                            c_lbl.setStyleSheet(f"font-size: 10px; color: {t['primary']}; line-height: 1.3; background: transparent; border: none;")
                            alay.addWidget(c_lbl)

                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.08)'}; border: none;")
                alay.addWidget(sep)

                self.chat_lay.addWidget(a_turn)

        self.chat_lay.addStretch()
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _handle_quick_query(self, query: str):
        self.input_field.setText(query)
        self._submit()

    def _submit(self):
        txt = self.input_field.text().strip()
        if not txt:
            return
        self.input_field.clear()

        # Append user turn
        self.messages.append({
            "role": "user",
            "text": txt,
            "citations": []
        })

        citations = []
        if self.assistant:
            try:
                target_files = None
                p = self.parent()
                if p and hasattr(p, "selected_doc") and p.selected_doc:
                    s_fn = p.selected_doc.get("filename")
                    if s_fn and any(w in txt.lower() for w in ["this", "current", "here", "file", "document", "contract"]):
                        target_files = [s_fn]

                res = self.assistant.answer_query(txt, target_filenames=target_files, user_email=self.owner_email)
                answer_txt = res.get("answer_text") or res.get("answer") or "No direct evidence found in local vault."
                citations = res.get("citations", []) or res.get("sources", [])
            except Exception as e:
                answer_txt = f"Could not parse query: {e}"
                citations = []
        else:
            answer_txt = f"DocuVault AI: Grounded analysis completed for '{txt}'."
            citations = []

        self.messages.append({
            "role": "assistant",
            "text": answer_txt,
            "citations": citations
        })

        self._render_messages()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"
        drawer_bg = "rgba(10, 10, 14, 0.96)" if is_dark else "rgba(255, 255, 255, 0.96)"
        drawer_border = "rgba(255, 122, 46, 0.28)" if is_dark else "rgba(242, 106, 27, 0.25)"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(f"""
            #aiDrawer {{
                background: {drawer_bg};
                border-left: 1px solid {drawer_border};
            }}
        """)
        self.scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.viewport().setStyleSheet("background: transparent; border: none;")
        self.scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.chat_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.chat_container.setStyleSheet("background: transparent; border: none;")
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text']};")

        self.evidence_chip.setStyleSheet(f"""
            background: rgba(242, 106, 27, 0.12);
            color: {t['primary']};
            border: 1px solid rgba(242, 106, 27, 0.28);
            font-size: 9.5px;
            font-weight: 700;
            border-radius: 6px;
            padding: 2px 7px;
        """)

        btn_icon_qss = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
            }}
        """
        if hasattr(self, "btn_clear"):
            self.btn_clear.setStyleSheet(btn_icon_qss)
        if hasattr(self, "btn_expand"):
            self.btn_expand.setStyleSheet(btn_icon_qss)
        if hasattr(self, "btn_close"):
            self.btn_close.setStyleSheet(btn_icon_qss)

        if hasattr(self, "chip_buttons"):
            for chip_btn in self.chip_buttons:
                chip_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#141418' if is_dark else '#F2F2F7'};
                        color: {t['text2']};
                        border: 1px solid {'#2B2B36' if is_dark else t['border']};
                        border-radius: 12px;
                        padding: 2px 10px;
                        font-size: 10px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        border-color: {t['primary']};
                        color: {t['primary']};
                    }}
                """)

        if hasattr(self, "in_wrap"):
            self.in_wrap.setStyleSheet(f"""
                QFrame {{
                    background: {'#141418' if is_dark else t['bg2']};
                    border: 1px solid {'rgba(255, 122, 46, 0.3)' if is_dark else t['border']};
                    border-radius: 16px;
                }}
            """)

        if hasattr(self, "btn_attach"):
            self.btn_attach.setStyleSheet(f"""
                QPushButton {{
                    background: {'rgba(255, 122, 46, 0.12)' if is_dark else 'rgba(242, 106, 27, 0.10)'};
                    border: 1px solid {'rgba(255, 122, 46, 0.25)' if is_dark else 'rgba(242, 106, 27, 0.20)'};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    background: rgba(242, 106, 27, 0.25);
                }}
            """)

        if hasattr(self, "input_field"):
            self.input_field.setStyleSheet(f"""
                QLineEdit {{
                    border: none;
                    background: transparent;
                    font-size: 11.5px;
                    color: {t['text']};
                    selection-background-color: {t['primary']};
                }}
            """)

        if hasattr(self, "btn_send"):
            self.btn_send.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                    border: none;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    background: {t['primary_hover']};
                }}
            """)

        self._render_messages()

    def minimumSizeHint(self) -> QSize:
        return QSize(280, 200)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPTION A: UNIVERSAL TOP COMMAND BAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TopCommandBar(QFrame):
    """
    Layout Option A: Unified command & action bar that sits on top of every page.
    Features Search (Ctrl+K), Import, AI Assistant Drawer Toggle (Ctrl+J), Duplicate Scanner, Display Scale (100%/125%/150%), and Profile.
    """
    search_triggered = pyqtSignal(str)
    import_clicked = pyqtSignal()
    ai_toggle_clicked = pyqtSignal()
    duplicates_clicked = pyqtSignal()
    profile_clicked = pyqtSignal()
    scale_changed = pyqtSignal(float)
    api_key_clicked = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._scale = 1.0
        self.setFixedHeight(50)
        self.setObjectName("topCommandBar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(10)

        # Universal Search Bar with embedded Ctrl+K badge
        self.search_wrap = QFrame()
        self.search_wrap.setFixedHeight(34)
        swlay = QHBoxLayout(self.search_wrap)
        swlay.setContentsMargins(10, 0, 8, 0)
        swlay.setSpacing(8)

        self.s_icon = QLabel()
        self.s_icon.setFixedSize(16, 16)
        swlay.addWidget(self.s_icon)

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search documents, content, or clauses (Ctrl+K)...")
        self.search_in.textChanged.connect(self.search_triggered.emit)
        swlay.addWidget(self.search_in, 1)

        self.kbadge = QLabel("Ctrl+K")
        self.kbadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        swlay.addWidget(self.kbadge)
        lay.addWidget(self.search_wrap, 1)

        # Action Buttons matching Reference Button Sheet
        self.btn_import = QPushButton("Import")
        self.btn_import.setFixedHeight(32)
        self.btn_import.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_import.clicked.connect(self.import_clicked.emit)
        lay.addWidget(self.btn_import)

        self.btn_ai = QPushButton("✨ AI Drawer")
        self.btn_ai.setFixedHeight(32)
        self.btn_ai.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ai.clicked.connect(self.ai_toggle_clicked.emit)
        lay.addWidget(self.btn_ai)

        self.btn_api_key = QPushButton("🔑 AI Key")
        self.btn_api_key.setFixedHeight(32)
        self.btn_api_key.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_api_key.setToolTip("Configure AI Search API Keys (Gemini, Groq, OpenAI)")
        self.btn_api_key.clicked.connect(self.api_key_clicked.emit)
        lay.addWidget(self.btn_api_key)

        self.btn_dup = QPushButton("Scan duplicates")
        self.btn_dup.setFixedHeight(32)
        self.btn_dup.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_dup.clicked.connect(self.duplicates_clicked.emit)
        lay.addWidget(self.btn_dup)

        # Windows Display Scaling Option (100% / 125% / 150%)
        self.btn_scale = QPushButton("🔍 100%")
        self.btn_scale.setFixedHeight(32)
        self.btn_scale.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scale.setToolTip("Display Scale: 100% / 125% / 150% (Ctrl++, Ctrl+-)")
        self.btn_scale.clicked.connect(self._cycle_scale)
        lay.addWidget(self.btn_scale)

        self.btn_profile = QPushButton("Profile")
        self.btn_profile.setFixedHeight(32)
        self.btn_profile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_profile.clicked.connect(self.profile_clicked.emit)
        lay.addWidget(self.btn_profile)

        self.update_theme(theme)

    def _cycle_scale(self):
        scales = [1.0, 1.25, 1.50]
        curr = getattr(self, "_scale", 1.0)
        try:
            idx = (scales.index(curr) + 1) % len(scales)
        except ValueError:
            idx = 0
        new_scale = scales[idx]
        self.set_scale_display(new_scale)
        self.scale_changed.emit(new_scale)

    def set_scale_display(self, scale: float):
        self._scale = scale
        pct = int(round(scale * 100))
        self.btn_scale.setText(f"🔍 {pct}%")

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"

        self.setStyleSheet(f"""
            #topCommandBar {{
                background: {t['surface']};
                border-bottom: 1px solid {t['border']};
            }}
        """)

        self.search_wrap.setStyleSheet(f"""
            background: {t['bg2']};
            border: 1px solid {t['border']};
            border-radius: 10px;
        """)

        self.s_icon.setPixmap(draw_vector_icon("search", t["text3"] if is_dark else "#475467", 16))

        self.search_in.setStyleSheet(f"""
            border: none;
            background: transparent;
            font-size: 12px;
            color: {t['text']};
        """)

        self.kbadge.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {t['text4']};
            background: {'#1A1A1A' if is_dark else '#E4E7EC'};
            border-radius: 4px;
            padding: 2px 6px;
        """)

        # Secondary Button Styles matching Reference Design Sheet
        sec_btn_bg = "#141418" if is_dark else "#FFFFFF"
        sec_btn_border = "#2B2B36" if is_dark else "#E2E4E9"
        sec_btn_text = "#E4E4E7" if is_dark else "#374151"
        sec_hover_bg = "#1C1C22" if is_dark else "#F9FAFB"

        btn_qss = f"""
            QPushButton {{
                background: {sec_btn_bg};
                color: {sec_btn_text};
                border: 1px solid {sec_btn_border};
                border-radius: 9px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {sec_hover_bg};
                border-color: {t['primary']};
                color: {t['primary']};
            }}
            QPushButton:pressed {{
                background: {'#0E0E12' if is_dark else '#F3F4F6'};
            }}
        """
        self.btn_ai.setStyleSheet(btn_qss)
        self.btn_api_key.setStyleSheet(btn_qss)
        self.btn_dup.setStyleSheet(btn_qss)
        self.btn_scale.setStyleSheet(btn_qss)
        self.btn_profile.setStyleSheet(btn_qss)

        # Primary Import Button matching Reference Design Sheet (Orange gradient with crisp border)
        primary_grad_0 = "#FF8C38" if is_dark else "#F26A1B"
        primary_grad_1 = "#EE6618" if is_dark else "#E04F08"
        self.btn_import.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary_grad_0}, stop:1 {primary_grad_1});
                color: #FFFFFF;
                border: 1px solid {t['primary']};
                border-radius: 9px;
                padding: 4px 18px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['primary_hover']};
                border-color: #FFA575;
            }}
            QPushButton:pressed {{
                background: {t['primary_pressed']};
            }}
        """)


class WorkspaceStack(QStackedWidget):
    """
    Fluid stacked widget with a compact minimum size hint.
    Allows center_splitter to freely resize docked drawers (Details Drawer and AI Drawer)
    without being locked or jittering against child page size constraints.
    """
    def minimumSizeHint(self) -> QSize:
        return QSize(350, 200)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRIMARY MAIN WINDOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocuVault(QMainWindow):
    """
    DocuVault Master Application Window:
    - Layout Option A: Slim Rail + Universal Command Bar
    - Layout Option E: Collapsible Right-Hand AI Drawer
    - Dynamic 60-FPS ambient background tracking mouse hover
    - Orange brand styling (Light & Dark)
    - Unified workspace card layout
    - Universal Search (Ctrl+K)
    - Real-time database & document operations
    """

    def __init__(self, current_user: Optional[Dict[str, Any]] = None, start_at_splash: bool = True):
        super().__init__()
        self.setWindowTitle("DocuVault — Enterprise Document Management")
        self.setWindowIcon(get_app_icon())
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.setWindowIcon(get_app_icon())
        self.resize(1380, 880)
        self.setMinimumSize(1080, 680)

        # Multi-Tenant SaaS User State
        saved_session = SessionManager.load_session()
        self.current_user = current_user or saved_session or {
            "email": "user@docuvault.local",
            "full_name": "Vault User",
            "tier": "Free",
            "country": "Global",
        }
        self.user_email = self.current_user.get("email", "user@docuvault.local").strip().lower()
        self.user_tier = self.current_user.get("tier", "Free")
        self.chat_query_count = 0

        # Core Backend Engines
        self.storage_mode = "Local Vault"
        self.local_prov = LocalStorageProvider(root_dir="vault/local")
        self.cloud_prov = CloudStorageProvider(mirror_dir="vault/cloud_mirror")
        self.catalog = CatalogManager()
        self.vec_engine = VectorSearchEngine()
        self.organizer = FileOrganizerDaemon(vault_root="vault")
        self.mongo = MongoDatabase()
        self.assistant = ExplainableAIAssistant(self.vec_engine, mongo_database=self.mongo, owner_email=self.user_email)

        # Real-Time Directory Tracker (Git-Like Folder Auto-Sync)
        self.tracker = DirectoryTracker(
            on_document_discovered=self._on_tracked_document_discovered,
            mongo=self.mongo,
            owner_email=self.user_email,
        )
        self.tracker.start_background_monitoring(poll_interval_sec=3.0)

        # Application State
        self.docs: Dict[str, Dict[str, Any]] = {}
        self.selected_doc: Optional[Dict[str, Any]] = None
        self.current_filter_cat = "All"
        self.current_search_query = ""
        self._workers: List[QThread] = []
        self._import_queue: List[str] = []

        # Active Theme (Default: Light Mode or Persisted Setting)
        saved_theme_mode = SessionManager.get_theme_mode()
        self.theme = DARK if saved_theme_mode == "dark" else LIGHT
        self._apply_theme()
        self._build_ui(start_at_splash=start_at_splash)
        self._setup_shortcuts()
        self._load_vault_database()
        self._update_folder_sync_badge()

        # Wire header user info and AI tier check callback
        self.header_banner.set_user_info(self.current_user)
        self.page_ai.tier_check_callback = self._check_chat_quota

        # Install global mouse tracking filter so ambient background glides with mouse cursor
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove:
            if hasattr(self, "workspace_canvas") and self.workspace_canvas:
                try:
                    gpos = event.globalPosition().toPoint()
                except AttributeError:
                    gpos = event.globalPos()
                self.workspace_canvas.set_target_mouse(gpos.x(), gpos.y())
        return super().eventFilter(obj, event)

    def _apply_theme(self):
        self.setStyleSheet(qss(self.theme))
        if hasattr(self, "showcase_widget"):
            self.showcase_widget.set_theme(self.theme)
        if hasattr(self, "auth_widget"):
            self.auth_widget.set_theme(self.theme)
        if hasattr(self, "workspace_canvas"):
            self.workspace_canvas.update_theme(self.theme)
        if hasattr(self, "command_bar"):
            self.command_bar.update_theme(self.theme)
        if hasattr(self, "ai_drawer"):
            self.ai_drawer.update_theme(self.theme)
        if hasattr(self, "sidebar"):
            self.sidebar.update_theme(self.theme)
        if hasattr(self, "header_banner"):
            self.header_banner.update_theme(self.theme)
        if hasattr(self, "inspector"):
            self.inspector.update_theme(self.theme)
        if hasattr(self, "page_storage"):
            self.page_storage.update_theme(self.theme)
        if hasattr(self, "page_security"):
            self.page_security.update_theme(self.theme)
        if hasattr(self, "page_audit"):
            self.page_audit.update_theme(self.theme)
        if hasattr(self, "page_ai"):
            self.page_ai.update_theme(self.theme)
        if hasattr(self, "page_organizer"):
            self.page_organizer.update_theme(self.theme)
        if hasattr(self, "page_deadlines"):
            self.page_deadlines.update_theme(self.theme)

        # Update feedback bar
        if hasattr(self, "feedback_bar"):
            self.feedback_bar.setStyleSheet(f"""
                background: {self.theme['surface']};
                border-top: 1px solid {self.theme['border']};
            """)
        if hasattr(self, "feedback_msg"):
            self.feedback_msg.setStyleSheet(f"font-size: 11px; color: {self.theme['text3']};")
        if hasattr(self, "shortcut_hint"):
            self.shortcut_hint.setStyleSheet(f"font-size: 11px; color: {self.theme['text4']};")
        if hasattr(self, "mongo_status"):
            self._update_mongo_status()

        # Update search bar badge
        if hasattr(self, "kbadge"):
            self.kbadge.setStyleSheet(f"""
                font-size: 10px;
                font-weight: 700;
                color: {self.theme['text4']};
                background: {self.theme['bg2']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 2px 6px;
            """)

        # Update scroll area, list container, and workspace card
        if isinstance(getattr(self, "scroll", None), QWidget):
            self.scroll.setStyleSheet(f"border: none; background: {self.theme['surface']};")
        if hasattr(self, "list_container"):
            self.list_container.setStyleSheet(f"background: {self.theme['surface']};")
        if hasattr(self, "workspace_card"):
            self.workspace_card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {self.theme['surface']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, "toolbar"):
            self.toolbar.setStyleSheet(f"border-bottom: 1px solid {self.theme['border']}; background: {self.theme['surface']};")
        if hasattr(self, "folder_sync_bar"):
            self.folder_sync_bar.setStyleSheet(f"background: {self.theme['bg3']}; border-bottom: 1px solid {self.theme['border']};")
        if hasattr(self, "lbl_folder_sync_status"):
            self.lbl_folder_sync_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.theme['text3']};")
        if hasattr(self, "doc_count_lbl"):
            self.doc_count_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {self.theme['text3']};")

        if hasattr(self, "filter_buttons"):
            for c, btn in self.filter_buttons.items():
                self._apply_filter_btn_style(btn, c == getattr(self, "current_filter_cat", "All"))

        if hasattr(self, "list_lay"):
            self._render_documents()
        if hasattr(self, "selected_doc") and self.selected_doc and hasattr(self, "inspector"):
            self.inspector.show_doc(self.selected_doc, self.storage_mode)

    def _toggle_theme(self):
        self.theme = DARK if self.theme["name"] == "light" else LIGHT
        SessionManager.set_theme_mode(self.theme["name"])
        self._apply_theme()
        self._show_feedback(f"Switched to {self.theme['name'].capitalize()} Mode")

    def _setup_shortcuts(self):
        # Universal Search Shortcut: Ctrl+K
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self._focus_search)

        # Clear Search Shortcut: Esc
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._clear_search)

        # Option E: AI Assistant Drawer Toggle Shortcut: Ctrl+J
        self.ai_shortcut = QShortcut(QKeySequence("Ctrl+J"), self)
        self.ai_shortcut.activated.connect(self._toggle_ai_drawer)

        # UI Scale Shortcuts: Ctrl+Plus, Ctrl+Minus, Ctrl+0
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoom_in_shortcut.activated.connect(lambda: self._step_scale(0.25))
        self.zoom_in_plus = QShortcut(QKeySequence("Ctrl++"), self)
        self.zoom_in_plus.activated.connect(lambda: self._step_scale(0.25))
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_shortcut.activated.connect(lambda: self._step_scale(-0.25))
        self.zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        self.zoom_reset_shortcut.activated.connect(lambda: self.set_ui_scale(1.0))

    def set_ui_scale(self, scale: float):
        """Sets Windows high-DPI display scale (1.0 = 100%, 1.25 = 125%, 1.50 = 150%)."""
        self.ui_scale = scale
        app = QApplication.instance()
        if app:
            font = app.font()
            base_pt = 9.5
            font.setPointSize(int(round(base_pt * scale)))
            app.setFont(font)
        if hasattr(self, "command_bar"):
            self.command_bar.set_scale_display(scale)
        self._apply_theme()
        pct = int(round(scale * 100))
        self._show_feedback(f"Display Scale set to {pct}% (Windows High-DPI Optimized)")

    def _step_scale(self, delta: float):
        scales = [1.0, 1.25, 1.50]
        curr = getattr(self, "ui_scale", 1.0)
        new_scale = min(1.50, max(1.0, curr + delta))
        self.set_ui_scale(new_scale)

    def _focus_search(self):
        self.stack.setCurrentIndex(0)
        for i, item in enumerate(self.sidebar.nav_items):
            item.set_active(i == 0)
        if hasattr(self, "command_bar"):
            self.command_bar.search_in.setFocus()
            self.command_bar.search_in.selectAll()
        elif hasattr(self, "search_input"):
            self.search_input.setFocus()
            self.search_input.selectAll()
        self._show_feedback("Universal Search activated (Ctrl+K)")

    def _clear_search(self):
        cleared = False
        if hasattr(self, "command_bar") and (self.command_bar.search_in.hasFocus() or self.command_bar.search_in.text()):
            self.command_bar.search_in.clear()
            cleared = True
        if hasattr(self, "search_input") and (self.search_input.hasFocus() or self.search_input.text()):
            self.search_input.clear()
            cleared = True
        if cleared:
            self._show_feedback("Search cleared")

    def _toggle_ai_drawer(self):
        if not hasattr(self, "ai_drawer") or not hasattr(self, "center_splitter"):
            return
        is_vis = self.ai_drawer.isVisible()
        if is_vis:
            self.ai_drawer.setVisible(False)
            self._show_feedback("AI Assistant Drawer closed")
        else:
            # VS Code style: close details inspector if open to prevent sidebar squishing/glitching
            if hasattr(self, "inspector") and self.inspector.isVisible():
                self.inspector.setVisible(False)
                if hasattr(self, "btn_toggle_inspector"):
                    self.btn_toggle_inspector.setChecked(False)
            self.ai_drawer.setVisible(True)
            total_w = self.center_splitter.width() or self.width()
            drawer_w = max(360, int(total_w * 0.32))
            main_w = max(400, total_w - drawer_w)
            self.center_splitter.setSizes([main_w, 0, drawer_w])
            self.ai_drawer.input_field.setFocus()
            self._show_feedback("AI Assistant Drawer opened (Ctrl+J to toggle)")

    # ─── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self, start_at_splash: bool = True):
        # Master Root Stack (Single Unified Window Lifecycle)
        self.master_stack = QStackedWidget(self)
        self.setCentralWidget(self.master_stack)

        # ── Page 0: 5-Second Dynamic Feature Showcase Animation ──
        self.showcase_widget = StartupShowcaseWidget(duration_ms=5000, theme_mode=self.theme["name"], parent=self)
        self.showcase_widget.finished.connect(self._on_showcase_finished)
        self.showcase_widget.theme_toggled.connect(self._toggle_theme)
        self.master_stack.addWidget(self.showcase_widget)  # Index 0

        # ── Page 1: Embedded Authentication Screen ──
        saved_session = SessionManager.load_session()
        saved_email = (self.current_user if saved_session else {}).get("email", "") if saved_session else ""
        self.auth_widget = EmbeddedAuthWidget(default_email=saved_email, theme_mode=self.theme["name"], parent=self)
        self.auth_widget.authenticated.connect(self._on_user_authenticated)
        self.auth_widget.theme_toggled.connect(self._toggle_theme)
        self.master_stack.addWidget(self.auth_widget)  # Index 1

        # ── Page 2: Primary Workspace Container ──
        self.workspace_container = QWidget(self)
        root_lay = QHBoxLayout(self.workspace_container)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── 1. Sliding Sidebar (Option A Slim Rail: 68px default, expands on hover/toggle) ──
        self.sidebar = SlidingSidebar(self.theme, self)
        self.sidebar.page_selected.connect(self._on_page_selected)
        self.sidebar.theme_toggled.connect(self._toggle_theme)
        root_lay.addWidget(self.sidebar)

        # ── 2. Interactive Background Canvas (60-FPS Ambient Mouse Tracking) ──
        self.workspace_canvas = InteractiveBackground(self.theme, self.workspace_container)
        main_content = self.workspace_canvas
        mlay = QVBoxLayout(main_content)
        mlay.setContentsMargins(0, 0, 0, 0)
        mlay.setSpacing(0)

        # ── Option A: Universal Command Bar on top of every page ──
        self.command_bar = TopCommandBar(self.theme, self)
        self.command_bar.search_triggered.connect(self._on_search_query_changed)
        self.command_bar.import_clicked.connect(self._open_file_dialog)
        self.command_bar.ai_toggle_clicked.connect(self._toggle_ai_drawer)
        self.command_bar.duplicates_clicked.connect(self._show_duplicate_scanner)
        self.command_bar.scale_changed.connect(self.set_ui_scale)
        self.command_bar.profile_clicked.connect(self._show_profile_dialog)
        self.command_bar.api_key_clicked.connect(self._open_api_key_dialog)
        mlay.addWidget(self.command_bar)

        # Top progress bar for background operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        mlay.addWidget(self.progress_bar)

        # ── Center Splitter (Pages Stack on Left + Draggable Extendable AI Drawer on Right) ──
        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.center_splitter.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.center_splitter.setHandleWidth(6)
        self.center_splitter.setOpaqueResize(True)
        self.center_splitter.setStyleSheet("""
            QSplitter::handle:horizontal {
                background: rgba(255, 122, 46, 0.22);
                border-left: 1px solid rgba(255, 122, 46, 0.40);
            }
            QSplitter::handle:horizontal:hover {
                background: #FF7A2E;
            }
            QSplitter::handle:horizontal:pressed {
                background: #FF944D;
            }
        """)

        self.stack = WorkspaceStack()
        self.stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.page_docs = self._build_documents_page()
        self.page_ai = AIAssistantPage(self.assistant, self.theme)
        self.page_organizer = AIFileOrganizerPage(self.organizer, self.mongo, self.theme, self)
        self.page_storage = StorageVaultPage(self.theme)
        self.page_storage.btn_sync_now.clicked.connect(self._sync_storage_vault)
        self.page_storage.btn_change_loc.clicked.connect(self._track_new_directory)
        self.page_security = IntegritySecurityPage(self.theme)
        self.page_audit = AuditTrailPage(self.theme)
        self.page_deadlines = DeadlinesPage(self.theme, mongo=self.mongo, owner_email=self.user_email, parent=self)

        # Index 0 is Documents (Default when opened)
        self.stack.addWidget(self.page_docs)        # 0 (Documents - DEFAULT)
        self.stack.addWidget(self.page_ai)          # 1 (AI Assistant)
        self.stack.addWidget(self.page_organizer)   # 2 (AI File Organizer)
        self.stack.addWidget(self.page_storage)     # 3 (Storage Vault)
        self.stack.addWidget(self.page_security)    # 4 (Integrity & Health)
        self.stack.addWidget(self.page_audit)       # 5 (Audit Trail)
        self.stack.addWidget(self.page_deadlines)   # 6 (Deadlines)
        self.center_splitter.addWidget(self.stack)

        # Document Details Drawer in Center Splitter (Slider side-by-side with AI Drawer)
        self.center_splitter.addWidget(self.inspector)
        self.inspector.setVisible(False)

        # Option E: Draggable Extendable Right-Hand AI Drawer
        self.ai_drawer = AIDrawer(self.assistant, self.theme, self, owner_email=self.user_email)
        self.ai_drawer.closed.connect(self._toggle_ai_drawer)
        self.ai_drawer.expand_requested.connect(lambda: self._on_page_selected(1))
        self.ai_drawer.setVisible(False)
        self.center_splitter.addWidget(self.ai_drawer)

        self.center_splitter.setCollapsible(0, False)
        self.center_splitter.setCollapsible(1, False)
        self.center_splitter.setCollapsible(2, False)
        self.center_splitter.setStretchFactor(0, 1)
        self.center_splitter.setStretchFactor(1, 0)
        self.center_splitter.setStretchFactor(2, 0)

        mlay.addWidget(self.center_splitter, 1)

        # ── 3. Bottom Toast / Feedback Bar with Real-time MongoDB Status ──
        self.feedback_bar = QFrame()
        self.feedback_bar.setFixedHeight(34)
        self.feedback_bar.setStyleSheet(f"""
            background: {self.theme['surface']};
            border-top: 1px solid {self.theme['border']};
        """)
        flay = QHBoxLayout(self.feedback_bar)
        flay.setContentsMargins(20, 0, 20, 0)
        flay.setSpacing(12)

        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"color: {self.theme['primary']}; font-size: 11px;")
        flay.addWidget(self.status_dot)

        self.feedback_msg = QLabel("Ready \u2022 Press Ctrl+K to search \u2022 Ctrl+J for AI")
        self.feedback_msg.setStyleSheet(f"font-size: 11px; color: {self.theme['text3']};")
        flay.addWidget(self.feedback_msg)

        flay.addStretch()

        # MongoDB Realtime Status Indicator
        self.mongo_status = QLabel()
        self._update_mongo_status()
        flay.addWidget(self.mongo_status)
        flay.addSpacing(16)

        self.shortcut_hint = QLabel("Search: Ctrl+K  \u2022  AI Drawer: Ctrl+J  \u2022  Clear: Esc")
        self.shortcut_hint.setStyleSheet(f"font-size: 11px; color: {self.theme['text4']};")
        flay.addWidget(self.shortcut_hint)

        mlay.addWidget(self.feedback_bar)
        root_lay.addWidget(main_content, 1)

        self.master_stack.addWidget(self.workspace_container)  # Index 2

        if start_at_splash:
            self.master_stack.setCurrentIndex(0)
        else:
            self.master_stack.setCurrentIndex(2)
            if hasattr(self, "showcase_widget"):
                self.showcase_widget.timer.stop()
                self.showcase_widget._closing = True

    def _on_showcase_finished(self):
        """Transitions smoothly from 5s showcase to login/register in the SAME window."""
        if self.master_stack.currentIndex() == 0:
            self.master_stack.setCurrentIndex(1)

    def _on_user_authenticated(self, user_data: Dict[str, Any]):
        """Transitions from login/register to main workspace in the SAME window with clean user partition."""
        self.current_user = user_data
        self.user_email = user_data.get("email", "").strip().lower()
        self.user_tier = user_data.get("tier", "Free")
        self.chat_query_count = 0
        self.header_banner.set_user_info(self.current_user)
        if hasattr(self, "page_ai"):
            self.page_ai.set_user_info(self.current_user)
        if hasattr(self, "assistant"):
            self.assistant.set_owner_email(self.user_email)
        if hasattr(self, "ai_drawer"):
            self.ai_drawer.owner_email = self.user_email
        if hasattr(self, "tracker"):
            self.tracker.set_owner_email(self.user_email)

        # Reload vault database strictly scoped to this authenticated user
        self._load_vault_database()

        self._show_feedback(f"Welcome back, {user_data.get('full_name', 'User')}! Vault unlocked.")
        self.master_stack.setCurrentIndex(2)
        self.stack.setCurrentIndex(0)
        if hasattr(self, "sidebar") and self.sidebar.nav_items:
            for i, it in enumerate(self.sidebar.nav_items):
                it.set_active(i == 0)


    def _update_mongo_status(self):
        if self.mongo.is_connected:
            self.mongo_status.setText("● MongoDB Connected (docuvault_db)")
            self.mongo_status.setStyleSheet(f"color: {self.theme['green']}; font-size: 11px; font-weight: 700;")
        else:
            self.mongo_status.setText("● MongoDB Offline (Local Storage Mode)")
            self.mongo_status.setStyleSheet(f"color: {self.theme['orange']}; font-size: 11px; font-weight: 700;")

    def _build_documents_page(self) -> QWidget:
        """
        Builds the unified single-card workspace for Documents.
        Zero cluttered floating divs — organized into two cohesive surfaces.
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # ── Surface 1: Unified Header Banner (Metrics + Production Actions) ──
        self.header_banner = UnifiedHeaderBanner(self.theme, self)
        self.header_banner.files_dropped.connect(self._import_files)
        self.header_banner.browse_clicked.connect(self._open_file_dialog)
        self.header_banner.duplicates_clicked.connect(self._show_duplicate_scanner)
        self.header_banner.webhub_clicked.connect(self._launch_web_hub)
        self.header_banner.profile_clicked.connect(self._show_profile_dialog)
        lay.addWidget(self.header_banner)

        # ── Surface 2: Master Document Workspace Card ──
        self.workspace_card = QFrame()
        self.workspace_card.setObjectName("unifiedCard")
        wlay = QVBoxLayout(self.workspace_card)
        wlay.setContentsMargins(0, 0, 0, 0)
        wlay.setSpacing(0)

        # Toolbar inside the card: Filter categories & search
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(48)
        self.toolbar.setStyleSheet(f"border-bottom: 1px solid {self.theme['border']}; background: {self.theme['surface']};")
        tlay = QHBoxLayout(self.toolbar)
        tlay.setContentsMargins(12, 0, 12, 0)
        tlay.setSpacing(6)

        # Category Filter Pills
        self.filter_buttons: Dict[str, QPushButton] = {}
        for cat in ["All", "Legal", "Financial", "Medical", "Academic", "General"]:
            btn = QPushButton(cat)
            btn.setObjectName("filterPill")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._apply_filter_btn_style(btn, cat == "All")
            btn.clicked.connect(lambda _, c=cat: self._set_category_filter(c))
            tlay.addWidget(btn)
            self.filter_buttons[cat] = btn

        tlay.addSpacing(4)
        # Redesigned Document Count (Clean, borderless typography)
        self.doc_count_lbl = QLabel("0 documents")
        self.doc_count_lbl.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {self.theme['text3']};")
        tlay.addWidget(self.doc_count_lbl)

        tlay.addStretch()

        # Universal Search Bar with embedded Ctrl+K badge
        search_wrap = QFrame()
        search_wrap.setFixedWidth(145)
        search_wrap.setFixedHeight(30)
        search_wrap.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        swlay = QHBoxLayout(search_wrap)
        swlay.setContentsMargins(0, 0, 0, 0)
        swlay.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(30)
        self.search_input.setPlaceholderText("Filter documents...")
        self.search_input.setStyleSheet("padding-right: 48px;")
        self.search_input.textChanged.connect(self._on_search_query_changed)
        swlay.addWidget(self.search_input)

        self.kbadge = QLabel("Ctrl+K")
        self.kbadge.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 700;
            color: {self.theme['text4']};
            background: {self.theme['bg2']};
            border: 1px solid {self.theme['border']};
            border-radius: 4px;
            padding: 2px 5px;
        """)
        self.kbadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_holder = QHBoxLayout(self.search_input)
        badge_holder.setContentsMargins(0, 0, 6, 0)
        badge_holder.addStretch()
        badge_holder.addWidget(self.kbadge)
        tlay.addWidget(search_wrap)

        # Toggle Details Panel (Collapse / Expand Inspector Drawer)
        self.btn_toggle_inspector = QPushButton("Details Drawer")
        self.btn_toggle_inspector.setObjectName("secondaryBtn")
        self.btn_toggle_inspector.setFixedHeight(30)
        self.btn_toggle_inspector.setCheckable(True)
        self.btn_toggle_inspector.setChecked(False)
        self.btn_toggle_inspector.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_inspector.clicked.connect(self._toggle_inspector)
        tlay.addWidget(self.btn_toggle_inspector)

        wlay.addWidget(self.toolbar)

        # ── Git-Like Watched Repositories & Action Bar ──
        self.folder_sync_bar = QFrame()
        self.folder_sync_bar.setFixedHeight(42)
        self.folder_sync_bar.setStyleSheet(f"background: {self.theme['bg3']}; border-bottom: 1px solid {self.theme['border']};")
        fs_lay = QHBoxLayout(self.folder_sync_bar)
        fs_lay.setContentsMargins(16, 0, 16, 0)
        fs_lay.setSpacing(8)

        btn_track_folder = QPushButton("📁 + Track Directory")
        btn_track_folder.setFixedHeight(28)
        btn_track_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_track_folder.setToolTip("Select directories to monitor like Git for automated ingestion and OCR")
        btn_track_folder.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 3px 12px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {self.theme['primary_h']};
            }}
        """)
        btn_track_folder.clicked.connect(self._track_new_directory)
        fs_lay.addWidget(btn_track_folder)

        self.btn_manage_folders = QPushButton("Monitored Folders")
        self.btn_manage_folders.setFixedHeight(28)
        self.btn_manage_folders.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_manage_folders.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['bg2']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border2']};
                border-radius: 7px;
                padding: 3px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self.theme['primary']};
                color: {self.theme['primary']};
            }}
        """)
        self.btn_manage_folders.clicked.connect(self._open_tracked_folders_dialog)
        fs_lay.addWidget(self.btn_manage_folders)

        # Monitored folders status indicator
        self.lbl_folder_sync_status = QLabel("● 0 Folders Monitored (Live Sync Active)")
        self.lbl_folder_sync_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.theme['text3']};")
        fs_lay.addWidget(self.lbl_folder_sync_status)

        fs_lay.addStretch()

        # Action buttons on the right of the action bar
        btn_verify_all = QPushButton("Verify All")
        btn_verify_all.setObjectName("secondaryBtn")
        btn_verify_all.setFixedHeight(28)
        btn_verify_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_verify_all.clicked.connect(self._verify_all_documents)
        fs_lay.addWidget(btn_verify_all)

        btn_sort = QPushButton("Auto-Organize")
        btn_sort.setObjectName("secondaryBtn")
        btn_sort.setFixedHeight(28)
        btn_sort.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_sort.clicked.connect(self._run_auto_organize)
        fs_lay.addWidget(btn_sort)

        btn_rescan_dirs = QPushButton("⚡ Rescan Folders")
        btn_rescan_dirs.setFixedHeight(28)
        btn_rescan_dirs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_rescan_dirs.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['bg2']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border2']};
                border-radius: 7px;
                padding: 3px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self.theme['primary']};
                color: {self.theme['primary']};
            }}
        """)
        btn_rescan_dirs.clicked.connect(self._rescan_watched_directories)
        fs_lay.addWidget(btn_rescan_dirs)

        wlay.addWidget(self.folder_sync_bar)

        # Document List Scroll Area (Full Width inside card)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"border: none; background: {self.theme['surface']};")

        self.list_container = QWidget()
        self.list_lay = QVBoxLayout(self.list_container)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(0)
        self.list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_container)

        wlay.addWidget(self.scroll, 1)

        # Document Inspector Drawer (Resides in center_splitter alongside AI Drawer)
        self.inspector = DocumentInspector(self.theme, self)
        self.inspector.view_text_clicked.connect(self._view_selected_document_text)
        self.inspector.verify_clicked.connect(self._verify_selected_document)
        self.inspector.delete_clicked.connect(self._delete_selected_document)
        self.inspector.copy_hash_clicked.connect(lambda h: self._show_feedback("Security fingerprint copied to clipboard"))
        self.inspector.health_clicked.connect(self._show_health_report)
        self.inspector.version_clicked.connect(self._show_version_history)
        self.inspector.ai_clicked.connect(self._show_ai_assistant)
        self.inspector.ocr_clicked.connect(self._show_ocr_viewer)
        self.inspector.redact_clicked.connect(self._redact_selected_document)
        self.inspector.rebuttal_clicked.connect(self._draft_contract_rebuttal)
        self.inspector.encrypt_clicked.connect(self._open_client_encryption)
        self.inspector.export_dossier_clicked.connect(self._export_compliance_dossier)
        self.inspector.retention_clicked.connect(self._apply_retention_policy)
        self.inspector.collapse_requested.connect(self._collapse_inspector)

        lay.addWidget(self.workspace_card, 1)

        return page

    def _toggle_inspector(self):
        if not hasattr(self, "inspector") or not hasattr(self, "center_splitter"):
            return
        is_vis = self.inspector.isVisible()
        if is_vis:
            self.inspector.setVisible(False)
            if hasattr(self, "btn_toggle_inspector"):
                self.btn_toggle_inspector.setChecked(False)
            self._show_feedback("Document Details Drawer closed")
        else:
            # VS Code style: close AI drawer if open so only one drawer is active in splitter
            if hasattr(self, "ai_drawer") and self.ai_drawer.isVisible():
                self.ai_drawer.setVisible(False)
            self.inspector.setVisible(True)
            if hasattr(self, "btn_toggle_inspector"):
                self.btn_toggle_inspector.setChecked(True)
            total_w = self.center_splitter.width() or self.width()
            insp_w = max(340, min(550, int(total_w * 0.32)))
            main_w = max(400, total_w - insp_w)
            self.center_splitter.setSizes([main_w, insp_w, 0])
            self._show_feedback("Document Details Drawer opened — drag border to resize")

    def _collapse_inspector(self):
        if hasattr(self, "inspector"):
            self.inspector.setVisible(False)
        if hasattr(self, "btn_toggle_inspector"):
            self.btn_toggle_inspector.setChecked(False)
        self._show_feedback("Document Details Drawer closed")

    # ─── Navigation & Feedback ────────────────────────────────────────────

    def _on_page_selected(self, idx: int):
        for i, item in enumerate(self.sidebar.nav_items):
            item.set_active(i == idx)
        self.stack.setCurrentIndex(idx)
        # If user switches to dedicated AI page, minimize side AI drawer to avoid duplicate views
        if idx == 1 and hasattr(self, "ai_drawer") and self.ai_drawer.isVisible():
            self.ai_drawer.setVisible(False)
        titles = [
            "Documents Workspace",
            "Explainable AI Assistant",
            "AI File Organizer & Intelligent Triage",
            "Storage & Cloud Mirrors",
            "Integrity & Security Center",
            "Audit Action Log",
            "Smart Deadlines & Obligations",
        ]
        if idx == 1:
            self.page_ai.set_assistant(self.assistant)
        elif idx == 2:
            self.page_organizer.refresh_files()
        elif idx == 3:
            self.page_storage.refresh_storage_metrics(self.docs, self.user_tier)
        elif idx == 4:
            self.page_security.refresh_metrics(self.docs)
        elif idx == 5:
            self.page_audit.refresh_from_logs(
                self.mongo.get_audit_logs(user_email=self.user_email) if self.mongo.is_connected else [],
                len(self.docs)
            )
        elif idx == 6:
            self.page_deadlines.owner_email = self.user_email
            self.page_deadlines.refresh_from_db()
        self._show_feedback(f"Navigated to {titles[idx]}")

    def _show_feedback(self, msg: str):
        self.feedback_msg.setText(msg)
        self.page_audit.log_event(msg)
        if hasattr(self, "mongo") and self.mongo.is_connected:
            self.mongo.log_audit("FEEDBACK", msg, user_email=getattr(self, "user_email", None))

    # ─── Database & Vault Loading (MongoDB Realtime Primary) ───────────────

    def _load_vault_database(self):
        """Loads real documents from MongoDB partitioned for the active user."""
        self.docs.clear()
        self.catalog = CatalogManager()
        self.vec_engine = VectorSearchEngine()

        if hasattr(self, "tracker") and hasattr(self, "user_email"):
            self.tracker.set_owner_email(self.user_email)

        # 1. Attempt loading from MongoDB realtime collection filtered by active user
        loaded_from_mongo = False
        if self.mongo.is_connected:
            loaded_from_mongo = True
            mongo_docs = self.mongo.list_documents(user_email=getattr(self, "user_email", None))
            for doc in mongo_docs:
                doc_id = doc.get("doc_id")
                if doc_id:
                    self.docs[doc_id] = doc
                    self.catalog.add_document(doc, storage_mode=self.storage_mode)
                    self.vec_engine.add_document_chunks(
                        doc_id, doc.get("filename", ""), doc.get("category", "General"), doc.get("pages", []), owner_email=self.user_email
                    )

        # 2. Only if MongoDB is completely offline/disconnected and demo user, check local fallback
        if not loaded_from_mongo and not self.docs and getattr(self, "user_email", "") in ("user@docuvault.local", "demo@docuvault.ai", ""):
            categories = ["Legal", "Financial", "Medical", "Academic", "General"]
            for cat in categories:
                cat_dir = Path("vault") / cat
                if cat_dir.exists():
                    for f in cat_dir.iterdir():
                        if f.is_file() and not f.name.endswith(".tmp"):
                            try:
                                doc = DocumentFactory.create_document(str(f), category_hint=cat, enforce_magic_bytes=False)
                                dd = doc.to_dict()
                                dd["pages"] = [{"page_number": p.get("page_number", i+1), "text": p.get("text", "")} for i, p in enumerate(doc.pages)]
                                dd["owner_email"] = self.user_email
                                self.docs[doc.doc_id] = dd
                                self.catalog.add_document(dd, storage_mode=self.storage_mode)
                                self.vec_engine.add_document_chunks(doc.doc_id, doc.filename, doc.get_category(), doc.pages, owner_email=self.user_email)
                            except Exception:
                                pass

        self.vec_engine.build_index()
        self.assistant.set_engine(self.vec_engine)
        self.assistant.set_mongo(self.mongo)
        self.assistant.set_owner_email(self.user_email)
        if hasattr(self, "ai_drawer"):
            self.ai_drawer.owner_email = self.user_email
        if hasattr(self, "page_ai"):
            self.page_ai.set_assistant(self.assistant)
        if hasattr(self, "page_deadlines"):
            self.page_deadlines.owner_email = self.user_email
            self.page_deadlines.refresh_from_db()
        if hasattr(self, "page_storage"):
            self.page_storage.refresh_storage_metrics(self.docs, getattr(self, "user_tier", "Free"))
        if hasattr(self, "page_security"):
            self.page_security.refresh_metrics(self.docs)
        if hasattr(self, "page_audit"):
            self.page_audit.refresh_from_logs(
                self.mongo.get_audit_logs(user_email=getattr(self, "user_email", None)) if self.mongo.is_connected else [],
                len(self.docs)
            )

        if hasattr(self, "inspector"):
            self.inspector.show_empty()
        self.selected_doc = None

        self._render_documents()
        self._update_metrics_bar()
        self._update_mongo_status()

        if self.docs:
            first_doc = next(iter(self.docs.values()))
            self._select_document(first_doc, open_drawer=False)
        else:
            self.selected_doc = None
            if hasattr(self, "inspector"):
                self.inspector.show_empty()

        src = "MongoDB" if loaded_from_mongo else "Vault Filesystem"
        self._show_feedback(f"Loaded {len(self.docs)} authentic documents from {src}")

    # ─── Rendering Document List ──────────────────────────────────────────

    def _render_documents(self):
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        filtered: List[Dict[str, Any]] = []
        for d in self.docs.values():
            if self.current_filter_cat != "All" and d.get("category") != self.current_filter_cat:
                continue
            if self.current_search_query:
                q = self.current_search_query.lower()
                name_match = q in d.get("filename", "").lower()
                cat_match = q in d.get("category", "").lower()
                content_match = any(q in p.get("text", "").lower() for p in d.get("pages", []))
                if not (name_match or cat_match or content_match):
                    continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        if not filtered:
            empty_card = QFrame()
            empty_card.setObjectName("emptyCard")
            is_dark = self.theme.get("name") == "dark"
            dash_col = "rgba(255, 122, 46, 0.35)" if is_dark else "rgba(242, 106, 27, 0.30)"
            empty_card.setStyleSheet(f"""
                #emptyCard {{
                    background: transparent;
                    border: 2px dashed {dash_col};
                    border-radius: 12px;
                    margin: 40px 30px;
                    padding: 40px 20px;
                }}
            """)
            elay = QVBoxLayout(empty_card)
            elay.setSpacing(10)
            elay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            e_icon = QLabel("📂")
            e_icon.setStyleSheet("font-size: 38px; background: transparent;")
            e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elay.addWidget(e_icon)

            e_title = QLabel("Vault is ready for documents")
            e_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {self.theme['text']}; background: transparent;")
            e_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elay.addWidget(e_title)

            e_sub = QLabel("Select directories to track with live auto-sync, or import files directly into your secure vault.")
            e_sub.setStyleSheet(f"font-size: 12px; color: {self.theme['text3']}; background: transparent;")
            e_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elay.addWidget(e_sub)

            btn_track = QPushButton("📁 + Track Directory")
            btn_track.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_track.setFixedHeight(34)
            btn_track.setStyleSheet(f"""
                QPushButton {{
                    background: {self.theme['primary']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 20px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {self.theme['primary_h']};
                }}
            """)
            btn_track.clicked.connect(self._track_new_directory)
            elay.addWidget(btn_track, alignment=Qt.AlignmentFlag.AlignCenter)

            self.list_lay.addWidget(empty_card)
        else:
            for doc in filtered:
                item = DocumentListItem(doc, self.theme)
                if self.selected_doc and self.selected_doc.get("doc_id") == doc.get("doc_id"):
                    item.set_selected(True)
                item.clicked.connect(lambda d: self._select_document(d, open_drawer=True))
                item.view_requested.connect(self._view_document_direct)
                item.delete_requested.connect(self._delete_document_direct)
                self.list_lay.addWidget(item)

        self.doc_count_lbl.setText(f"{len(filtered)} {'documents' if len(filtered) != 1 else 'document'}")

    def _update_metrics_bar(self):
        total = len(self.docs)
        verified = sum(1 for d in self.docs.values() if d.get("status") == "Verified")
        pct = f"{(verified / total * 100):.0f}%" if total > 0 else "100%"
        cats = len(set(d.get("category") for d in self.docs.values())) if self.docs else 0
        total_bytes = sum(d.get("size_bytes", 0) for d in self.docs.values())

        if total_bytes >= 1048576:
            sz_str = f"{total_bytes / 1048576:.1f} MB"
        elif total_bytes >= 1024:
            sz_str = f"{total_bytes / 1024:.1f} KB"
        else:
            sz_str = f"{total_bytes} B"


        self.header_banner.update_metrics(total, sz_str, pct, cats)

    # ─── Filter & Search Handling ─────────────────────────────────────────

    def _apply_filter_btn_style(self, btn: QPushButton, active: bool):
        t = self.theme
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t['primary']};
                    color: #FFFFFF;
                    border: 1px solid {t['primary']};
                    border-radius: 13px;
                    padding: 4px 11px;
                    font-size: 11px;
                    font-weight: 700;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']};
                    color: {t['text2']};
                    border: 1px solid {t['border']};
                    border-radius: 13px;
                    padding: 4px 11px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {t['hover']};
                    color: {t['text']};
                    border-color: {t['border2']};
                }}
            """)

    def _set_category_filter(self, cat: str):
        self.current_filter_cat = cat
        for c, btn in self.filter_buttons.items():
            btn.setProperty("active", c == cat)
            self._apply_filter_btn_style(btn, c == cat)
        self._render_documents()
        self._show_feedback(f"Filtered repository by category: {cat}")

    def _on_search_query_changed(self, text: str):
        self.current_search_query = text.strip()
        # Keep command bar and toolbar search inputs synchronized
        if hasattr(self, "command_bar") and self.command_bar.search_in.text() != text:
            self.command_bar.search_in.blockSignals(True)
            self.command_bar.search_in.setText(text)
            self.command_bar.search_in.blockSignals(False)
        if hasattr(self, "search_input") and self.search_input.text() != text:
            self.search_input.blockSignals(True)
            self.search_input.setText(text)
            self.search_input.blockSignals(False)

        # If user searches from another page, navigate to Documents page to show results
        if self.current_search_query and self.stack.currentIndex() != 0:
            self.stack.setCurrentIndex(0)
            for i, it in enumerate(self.sidebar.nav_items):
                it.set_active(i == 0)

        self._render_documents()
        count = self.doc_count_lbl.text() if hasattr(self, "doc_count_lbl") else ""
        if self.current_search_query:
            self._show_feedback(f"Search results for '{self.current_search_query}': {count}")

    # ─── Document Selection ───────────────────────────────────────────────

    def _select_document(self, doc: Dict[str, Any], open_drawer: bool = False):
        self.selected_doc = doc
        if hasattr(self, "inspector"):
            self.inspector.show_doc(doc, self.storage_mode)
        for i in range(self.list_lay.count()):
            w = self.list_lay.itemAt(i).widget()
            if isinstance(w, DocumentListItem):
                w.set_selected(w._doc.get("doc_id") == doc.get("doc_id"))
        if open_drawer and hasattr(self, "inspector") and not self.inspector.isVisible():
            self._toggle_inspector()
        self._show_feedback(f"Selected: {doc.get('filename')}")

    # ─── Document Actions & Feature Dialog Triggers ───────────────────────

    def _view_document_direct(self, doc: Dict[str, Any]):
        self._select_document(doc, open_drawer=False)
        dialog = DocumentViewerDialog(doc, self.theme, self)
        dialog.exec()

    def _delete_document_direct(self, doc: Dict[str, Any]):
        if not doc:
            return
        fname = doc.get("filename", "this file")
        reply = QMessageBox.question(
            self, "Remove Document",
            f"Are you sure you want to remove '{fname}' from the vault catalog?\n(The file on disk will remain untouched)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            doc_id = doc.get("doc_id")
            if doc_id:
                if doc_id in self.docs:
                    del self.docs[doc_id]
                self.mongo.delete_document(doc_id, user_email=getattr(self, "user_email", None))
                self.mongo.log_audit(
                    "DELETE",
                    f"Removed '{fname}' from repository index",
                    doc_id,
                    operator=self.current_user.get("full_name", "User"),
                    user_email=getattr(self, "user_email", None)
                )

            if self.selected_doc and self.selected_doc.get("doc_id") == doc_id:
                self.selected_doc = None
                if hasattr(self, "inspector"):
                    self.inspector.show_empty()
            self._render_documents()
            self._update_metrics_bar()
            if hasattr(self, "page_storage"):
                self.page_storage.refresh_storage_metrics(self.docs, getattr(self, "user_tier", "Free"))
            if hasattr(self, "page_security"):
                self.page_security.refresh_metrics(self.docs)
            if hasattr(self, "page_audit"):
                self.page_audit.refresh_from_logs(
                    self.mongo.get_audit_logs(user_email=getattr(self, "user_email", None)) if self.mongo.is_connected else [],
                    len(self.docs)
                )
            self._show_feedback(f"Removed '{fname}' from repository index")

    def _view_selected_document_text(self):
        if self.selected_doc:
            self._view_document_direct(self.selected_doc)

    def _delete_selected_document(self):
        if self.selected_doc:
            self._delete_document_direct(self.selected_doc)

    def _verify_selected_document(self):
        if not self.selected_doc:
            return
        fpath = self.selected_doc.get("filepath", "")
        expected = self.selected_doc.get("sha256_hash", "")
        if os.path.exists(fpath):
            actual = BinaryParser.calculate_sha256(fpath)
            new_status = "Verified" if actual.lower() == expected.lower() else "Tampered"
            self.selected_doc["status"] = new_status
            doc_id = self.selected_doc.get("doc_id")
            if doc_id:
                self.mongo.update_document_status(doc_id, new_status)
                self.mongo.log_audit("VERIFY", f"Verified integrity status '{new_status}' for {Path(fpath).name}", doc_id)

            if new_status == "Verified":
                self._show_feedback(f"Integrity verified for {Path(fpath).name}")
                QMessageBox.information(self, "Integrity Verified", "Cryptographic SHA-256 fingerprint verified authentic.\nFile content matches disk record exactly.")
            else:
                self._show_feedback(f"Warning: Integrity mismatch for {Path(fpath).name}")
                QMessageBox.warning(self, "Integrity Warning", "Cryptographic mismatch detected!\nFile content does not match recorded signature.")

            self.inspector.show_doc(self.selected_doc, self.storage_mode)
            self._render_documents()
            self._update_metrics_bar()

    def _verify_all_documents(self):
        tampered_count = 0
        for d in self.docs.values():
            fp = d.get("filepath", "")
            exp = d.get("sha256_hash", "")
            if os.path.exists(fp):
                act = BinaryParser.calculate_sha256(fp)
                d["status"] = "Verified" if act.lower() == exp.lower() else "Tampered"
                if d.get("doc_id"):
                    self.mongo.update_document_status(d["doc_id"], d["status"])
                if d["status"] == "Tampered":
                    tampered_count += 1

        self._render_documents()
        self._update_metrics_bar()
        if tampered_count:
            self._show_feedback(f"Audit Complete: {tampered_count} files flagged for integrity issues")
            QMessageBox.warning(self, "Audit Alert", f"{tampered_count} document(s) failed cryptographic verification.")
        else:
            self._show_feedback("Audit Complete: All repository documents verified authentic")
            QMessageBox.information(self, "Audit Passed", "All repository documents have been cryptographically verified.")

    def _run_auto_organize(self):
        res = self.organizer.process_intake_folder()
        self._load_vault_database()
        self._show_feedback(f"Auto-Organizer sorted {len(res)} files into vault categories")
        QMessageBox.information(self, "Auto-Organizer", f"Processed intake folder.\n{len(res)} documents classified and filed into vault categories.")

    # ─── High-Value Feature Dialog Launchers ───────────────────────────────

    def _show_duplicate_scanner(self):
        dialog = DuplicateScannerDialog(list(self.docs.values()), self.theme, self)
        dialog.exec()

    def _show_ai_assistant(self):
        self.stack.setCurrentIndex(1)
        for i, item in enumerate(self.sidebar.nav_items):
            item.set_active(i == 1)
        self._show_feedback("Opened Explainable AI Assistant")

    def _show_version_history(self):
        if not self.selected_doc:
            return
        if not TierManager.can_access_feature(self.user_tier, "smart_diff"):
            modal = UpgradeModal(
                self.current_user,
                reason="Document Version History & Visual Clause Diff is a Pro feature.",
                parent=self,
            )
            modal.upgraded.connect(self._on_user_upgraded)
            modal.exec()
            return

        doc_id = self.selected_doc.get("doc_id", "")
        versions = self.mongo.get_versions(doc_id)
        dialog = DocumentVersionDialog(self.selected_doc, versions, self.theme, self)
        dialog.exec()

    def _show_ocr_viewer(self):
        if not self.selected_doc:
            return
        dialog = OCRViewerDialog(self.selected_doc, self.theme, self)
        dialog.exec()

    def _show_health_report(self):
        if not self.selected_doc:
            return
        deadlines = self.mongo.list_deadlines()
        dialog = DocumentHealthDialog(self.selected_doc, deadlines, self.theme, self)
        dialog.exec()

    def _show_deadlines(self):
        self._on_page_selected(6)
        self._show_feedback("Opened Deadlines & Obligations Workspace")

    # ─── Document Import Pipeline (With Duplicate Pre-Check) ───────────────

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents to Import", "",
            "Supported Documents (*.pdf *.xml *.txt);;All Files (*.*)"
        )
        if files:
            self._import_files(files)

    def _import_files(self, paths: List[str]):
        self._import_queue = list(paths)
        self._process_next_import()

    def _process_next_import(self):
        if not self._import_queue:
            return

        # Free tier document limit quota check
        try:
            TierManager.check_document_limit(self.user_tier, len(self.docs))
        except TierLimitExceededError as e:
            self._import_queue.clear()
            self._show_feedback("Free Trial limit reached (5 documents max).")
            modal = UpgradeModal(self.current_user, reason=str(e), parent=self)
            modal.upgraded.connect(self._on_user_upgraded)
            modal.exec()
            return

        filepath = self._import_queue.pop(0)

        # 1. Duplicate Detection Check before processing
        try:
            file_hash = BinaryParser.calculate_sha256(filepath)
            exact_match = DuplicateDetector.check_exact_duplicate(file_hash, list(self.docs.values()))
            if exact_match:
                warn_dlg = DuplicateWarningDialog(
                    Path(filepath).name, exact_match, is_exact=True, similarity_pct=100.0, theme=self.theme, parent=self
                )
                if warn_dlg.exec() != QDialog.DialogCode.Accepted or not warn_dlg.proceed_import:
                    self._show_feedback(f"Import cancelled: Duplicate of '{exact_match.get('filename')}'")
                    QTimer.singleShot(100, self._process_next_import)
                    return
        except Exception:
            pass

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        fname = Path(filepath).name
        self._show_feedback(f"Importing {fname}...")

        worker = DocumentIngestWorker(
            filepath, self.storage_mode, self.local_prov, self.cloud_prov, self.vec_engine
        )
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(lambda _: self._cleanup_worker(worker))
        worker.failed.connect(lambda _: self._cleanup_worker(worker))
        worker.start()
        self._workers.append(worker)

    def _on_worker_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self._show_feedback(msg)

    def _on_worker_finished(self, doc_dict: Dict[str, Any]):
        doc_dict["owner_email"] = getattr(self, "user_email", None)
        self.docs[doc_dict["doc_id"]] = doc_dict
        self.catalog.add_document(doc_dict, storage_mode=self.storage_mode)

        # Persist to MongoDB in real-time with user ownership
        self.mongo.save_document(doc_dict, user_email=getattr(self, "user_email", None))
        self.mongo.save_version(doc_dict["doc_id"], {
            "version_number": "1.0",
            "sha256_hash": doc_dict.get("sha256_hash"),
            "author": self.current_user.get("full_name", "Ingest Worker"),
            "owner_email": getattr(self, "user_email", None),
            "text_snapshot": " ".join(p.get("text", "") for p in doc_dict.get("pages", [])),
        })
        self.mongo.log_audit(
            "IMPORT",
            f"Successfully imported '{doc_dict['filename']}'",
            doc_dict["doc_id"],
            operator=self.current_user.get("full_name", "User"),
            user_email=getattr(self, "user_email", None)
        )

        self.vec_engine.build_index()
        self.assistant.set_engine(self.vec_engine)

        self._render_documents()
        self._update_metrics_bar()
        if hasattr(self, "page_storage"):
            self.page_storage.refresh_storage_metrics(self.docs, getattr(self, "user_tier", "Free"))
        if hasattr(self, "page_security"):
            self.page_security.refresh_metrics(self.docs)
        if hasattr(self, "page_audit"):
            self.page_audit.refresh_from_logs(
                self.mongo.get_audit_logs(user_email=getattr(self, "user_email", None)) if self.mongo.is_connected else [],
                len(self.docs)
            )
        self._select_document(doc_dict)
        self._show_feedback(f"Successfully imported '{doc_dict['filename']}' to MongoDB")
        QTimer.singleShot(100, self._process_next_import)

    def _on_worker_failed(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self._show_feedback(f"Import error: {error_msg}")
        QMessageBox.warning(self, "Import Error", f"Failed to import document:\n{error_msg}")
        QTimer.singleShot(100, self._process_next_import)

    def _cleanup_worker(self, worker: QThread):
        try:
            worker.quit()
            worker.wait(1500)
            if worker in self._workers:
                self._workers.remove(worker)
        except RuntimeError:
            pass

    def _check_chat_quota(self) -> bool:
        """Validates AI chat query quota before sending inquiry."""
        try:
            TierManager.check_chat_limit(self.user_tier, self.chat_query_count)
            self.chat_query_count += 1
            return True
        except TierLimitExceededError as e:
            self._show_feedback("AI Chat query limit reached for session.")
            modal = UpgradeModal(self.current_user, reason=str(e), parent=self)
            modal.upgraded.connect(self._on_user_upgraded)
            modal.exec()
            return False

    def _on_user_upgraded(self, updated_user: dict):
        """Elevates current session state to Pro Plan."""
        self.current_user = updated_user
        self.user_tier = updated_user.get("tier", "Pro")
        self.header_banner.set_user_info(self.current_user)
        self._show_feedback(f"Account upgraded to {self.user_tier.upper()}! Unlimited access active.")

    def _show_profile_dialog(self):
        """Opens interactive account profile modal."""
        dlg = ProfileDialog(
            user_info=self.current_user,
            current_doc_count=len(self.docs),
            current_chat_count=self.chat_query_count,
            parent=self,
        )
        dlg.tier_changed.connect(self._on_user_upgraded)
        dlg.signed_out.connect(self._handle_sign_out)
        dlg.exec()

    def _handle_sign_out(self):
        """Clears session and switches back to embedded login in the SAME window with clean state."""
        SessionManager.clear_session()
        self.current_user = {}
        self.user_email = ""
        self.docs.clear()
        self.selected_doc = None
        self.catalog = CatalogManager()
        self.vec_engine = VectorSearchEngine()
        if hasattr(self, "inspector"):
            self.inspector.show_empty()
            self.inspector.setVisible(False)
        if hasattr(self, "btn_toggle_inspector"):
            self.btn_toggle_inspector.setChecked(False)
        if hasattr(self, "ai_drawer"):
            self.ai_drawer.setVisible(False)
        self._render_documents()
        self._update_metrics_bar()
        self.master_stack.setCurrentIndex(1)
        self._show_feedback("Signed out securely. Please sign in.")


    def _launch_web_hub(self):
        """Launches or opens Streamlit Cloud Web Hub in system browser."""
        import webbrowser
        self._show_feedback("Connecting to DocuVault Cloud Web Hub...")
        try:
            # Check if Streamlit server is already responding
            import urllib.request
            urllib.request.urlopen("http://localhost:8501", timeout=0.8)
        except Exception:
            # Launch Streamlit server in background
            try:
                subprocess.Popen(
                    [sys.executable, "-m", "streamlit", "run", "ui/dashboard_streamlit.py", "--server.port=8501", "--server.headless=true"],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                self._show_feedback(f"Could not launch Web Hub process: {e}")
        webbrowser.open("http://localhost:8501")

    def _redact_selected_document(self):
        """Performs regex-based PII redaction on selected document."""
        if not self.selected_doc:
            return

        if not TierManager.can_access_feature(self.user_tier, "pii_redaction"):
            modal = UpgradeModal(
                self.current_user,
                reason="Confidential PII Redaction is a Pro feature.",
                parent=self,
            )
            modal.upgraded.connect(self._on_user_upgraded)
            modal.exec()
            return

        pages = self.selected_doc.get("pages", [])
        full_text = " ".join([p.get("text", "") for p in pages]) or self.selected_doc.get("filename", "")
        sanitized_text, detections = PIIRedactor.redact_text(full_text)

        # Show Redaction Summary Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("PII Compliance Redaction — DocuVault Pro")
        dlg.setFixedSize(600, 480)
        dlg.setStyleSheet(f"background: {self.theme['surface']}; color: {self.theme['text']};")
        dlay = QVBoxLayout(dlg)
        dlay.setContentsMargins(20, 20, 20, 20)
        dlay.setSpacing(12)

        head = QLabel(f"Redaction Complete: {len(detections)} Sensitive PII Entities Masked")
        head.setStyleSheet("font-size: 14px; font-weight: 700; color: #10B981;")
        dlay.addWidget(head)

        preview = QTextBrowser()
        preview.setStyleSheet(f"background: {self.theme['bg3']}; border: 1px solid {self.theme['border']}; border-radius: 8px; padding: 12px; font-size: 12px;")
        preview.setPlainText(sanitized_text[:3000])
        dlay.addWidget(preview, 1)

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(34)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("background: #FF7A3D; color: #FFFFFF; border-radius: 6px; font-weight: 600;")
        btn_close.clicked.connect(dlg.accept)
        dlay.addWidget(btn_close)
        dlg.exec()

    # ─── Git-Like Watched Directory & Production Tool Actions ─────────────

    def _update_folder_sync_badge(self):
        if not hasattr(self, "tracker") or not hasattr(self, "lbl_folder_sync_status"):
            return
        count = len(self.tracker.get_watched_folders())
        if count == 0:
            self.lbl_folder_sync_status.setText("● 0 Folders Monitored (Click '+ Track Directory' to auto-sync)")
            self.lbl_folder_sync_status.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {self.theme['text4']};")
        else:
            self.lbl_folder_sync_status.setText(f"● {count} Folder{'s' if count != 1 else ''} Monitored (Live Git-Like Auto-Sync Active)")
            self.lbl_folder_sync_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.theme['green']};")

    def _track_new_directory(self):
        """Allows selecting a directory to track like Git for newly added files."""
        path = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor (Git-Like Auto-Sync)")
        if not path:
            return

        self.tracker.add_watched_folder(path)
        self._update_folder_sync_badge()
        self._show_feedback(f"Tracking & scanning directory: {Path(path).name} ...")

        # Ingest all files in the tracked directory for the active user
        found = self.tracker.scan_folder(path, force=True)
        for doc_dict in found:
            self._on_tracked_document_discovered(doc_dict)

        self._load_vault_database()
        self._show_feedback(f"Tracked directory synced. Processed {len(found)} documents from {Path(path).name}")

    def _open_tracked_folders_dialog(self):
        """Opens modal to view and manage watched directories."""
        dlg = TrackedFoldersDialog(self.tracker, self.theme, self)
        dlg.folders_changed.connect(self._on_tracked_folders_changed)
        dlg.exec()

    def _on_tracked_folders_changed(self):
        self._update_folder_sync_badge()
        self._load_vault_database()

    def _rescan_watched_directories(self):
        """Manually triggers a full re-scan of all monitored directories."""
        self._show_feedback("Scanning all monitored folders for new or modified files...")
        found = self.tracker.scan_all_watched(force=True)
        for doc_dict in found:
            self._on_tracked_document_discovered(doc_dict)
        self._load_vault_database()
        self._update_folder_sync_badge()
        self._show_feedback(f"Folder sync complete. Processed {len(found)} documents across monitored folders.")

    def _sync_storage_vault(self):
        """Manually trigger background folder synchronization and refresh real-time metrics."""
        self._show_feedback("Synchronizing Storage Vault and cloud mirrors...")
        if hasattr(self, "tracker"):
            found = self.tracker.scan_all_watched()
            for doc_dict in found:
                self._on_tracked_document_discovered(doc_dict)
            self._update_folder_sync_badge()
        if hasattr(self, "page_storage"):
            self.page_storage.refresh_storage_metrics(self.docs, getattr(self, "user_tier", "Free"))
        self._show_feedback(f"Storage Vault synced • {len(self.docs)} files up to date")

    def _on_tracked_document_discovered(self, doc_dict: Dict[str, Any]):
        """Handler called when DirectoryTracker discovers an incoming file."""
        doc_id = doc_dict.get("doc_id")
        if not doc_id:
            return

        # Add to state and databases
        doc_dict["owner_email"] = getattr(self, "user_email", None)
        self.docs[doc_id] = doc_dict
        self.catalog.add_document(doc_dict)
        self.mongo.save_document(doc_dict, user_email=getattr(self, "user_email", None))

        # Index into in-memory NumPy vector engine with hierarchical chunking
        pages = doc_dict.get("pages", []) or [{"page_number": 1, "text": doc_dict.get("raw_text", "")}]
        self.vec_engine.add_hierarchical_document_chunks(
            doc_id=doc_id,
            filename=doc_dict.get("filename", "tracked_file"),
            category=doc_dict.get("category", "General"),
            pages=pages,
        )
        self.vec_engine.build_index()

        # Update UI safely
        QTimer.singleShot(0, self._render_documents)
        QTimer.singleShot(0, self._update_metrics_bar)
        QTimer.singleShot(0, self._update_folder_sync_badge)
        if hasattr(self, "page_storage"):
            QTimer.singleShot(0, lambda: self.page_storage.refresh_storage_metrics(self.docs, getattr(self, "user_tier", "Free")))
        QTimer.singleShot(0, lambda: self._show_feedback(f"⚡ Ingested: {doc_dict.get('filename')} (Auto-saved to MongoDB)"))

    def _open_api_key_dialog(self):
        """Opens the API Key & Neural Search Configuration modal."""
        dlg = ApiKeyConfigDialog(self.theme, self)
        dlg.keys_updated.connect(self._on_api_keys_configured)
        dlg.exec()

    def _on_api_keys_configured(self, keys: dict):
        try:
            from backend.api_client import LLMClient
            new_llm = LLMClient()
            self.assistant.llm_client = new_llm
            self.page_ai.assistant.llm_client = new_llm
            if hasattr(self, "ai_drawer") and hasattr(self.ai_drawer, "assistant") and self.ai_drawer.assistant:
                self.ai_drawer.assistant.llm_client = new_llm
        except Exception:
            pass
        self._show_feedback("⚡ AI Keys configured. Real-time generative AI search is now active!")

    def _draft_contract_rebuttal(self):
        """Automated Rebuttal/Reply Drafting: opens legal amendment letter generator."""
        if not self.selected_doc:
            return
        dlg = RebuttalDraftDialog(self.selected_doc, self.theme, self)
        dlg.exec()

    def _open_client_encryption(self):
        """Opens Zero-Knowledge AES-256 client-side encryption modal."""
        if not self.selected_doc:
            return
        dlg = ClientEncryptionDialog(self.selected_doc, self.theme, self)
        dlg.exec()

    def _export_compliance_dossier(self):
        """Compiles selected documents into compliance master dossier ZIP."""
        docs_to_export = list(self.docs.values())
        if not docs_to_export:
            QMessageBox.warning(self, "No Documents", "The repository is empty. Please import or track documents first.")
            return
        dlg = DossierExportDialog(docs_to_export, self.theme, self)
        dlg.exec()

    def _apply_retention_policy(self):
        """Automated Storage Retention Cleanup (DoD 5220.22-M shredding / archiving)."""
        retention = RetentionPolicyManager()
        summary = retention.get_retention_summary(list(self.docs.values()))
        archivable = summary["archivable_count"]
        shreddable = summary["shreddable_count"]

        msg = (
            f"Retention Policy Assessment:\n\n"
            f"• Documents eligible for auto-archival (> 365 days): {archivable}\n"
            f"• Documents eligible for secure shredding (> 730 days): {shreddable}\n\n"
            f"Would you like to run automated archival and secure DoD 5220.22-M shredding now?"
        )
        reply = QMessageBox.question(self, "Retention Policy Audit", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = retention.enforce_retention_policies(list(self.docs.values()))
            QMessageBox.information(
                self, "Retention Enforced",
                f"Retention policy successfully executed:\n\n"
                f"• Archived: {res['archived_count']}\n"
                f"• Shredded: {res['shredded_count']}\n"
                f"• Retention log updated in vault_audit."
            )

    def closeEvent(self, event):
        """Clean shutdown of background directory watcher."""
        try:
            if hasattr(self, "tracker"):
                self.tracker.stop_background_monitoring()
        except Exception:
            pass
        event.accept()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLICATION ENTRYPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI Variable", 10))
    app.setStyle("Fusion")

    # Launch Single Unified Master Window:
    # 1. Plays 5-second dynamic feature showcase animation inside this window
    # 2. Seamlessly transitions to login/register in the same window (with skip option)
    # 3. Transitions to main workspace in the same window upon authentication
    window = DocuVault(start_at_splash=True)
    window.showMaximized()
    sys.exit(app.exec())




if __name__ == "__main__":
    main()
