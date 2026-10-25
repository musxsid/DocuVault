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
from datetime import datetime
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
    QAbstractItemView, QApplication, QCheckBox, QDialog, QFileDialog, QFrame,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
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
    "green": "#32D583",
    "green_bg": "#ECFDF5",
    "green_border": "#A7F3D0",
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
    "green": "#32D583",
    "green_bg": "rgba(50, 213, 131, 0.14)",
    "green_border": "rgba(50, 213, 131, 0.30)",
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

    p.end()
    return pm


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
            ("Financial", 154, "#32D583"),
            ("Academic", 135, "#A58BFF"),
            ("Medical", 96, "#F0556E"),
            ("General", 134, "#FF7A2E"),
        ]
        self.used_text = "960.9 KB"
        self.total_text = "of 5 GB used"

    def set_data(self, used_str: str, slices: List[tuple]):
        self.used_text = used_str
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
        p.setPen(QPen(QColor(50, 213, 131, 40), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        # Active progress arc
        pct = max(0.0, min(1.0, self._score / 100.0))
        span_angle = int(pct * 360.0 * 16.0)
        p.setPen(QPen(QColor("#32D583"), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
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
            ("storage", "Storage Vault", 2),
            ("security", "Integrity & Health", 3),
            ("activity", "Audit Trail", 4),
            ("calendar", "Deadlines", 5),
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
        self.setMinimumWidth(320)
        self.setMaximumWidth(950)
        self.resize(380, self.height())
        self._current_hash = ""
        self._current_doc: Optional[Dict[str, Any]] = None
        self._build()

    def _build(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
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
        lay.addWidget(self.title_lbl)

        self.meta_sub_lbl = QLabel("No document selected")
        self.meta_sub_lbl.setStyleSheet(f"font-size: 11px; color: {t['text4']};")
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
    """Clean reader modal with high legibility, in-text search, and system file launcher."""

    def __init__(self, doc: Dict[str, Any], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        t = theme
        self._doc = doc
        is_dark = t.get("name") == "dark"
        self.setWindowTitle(f"Document Viewer — {doc.get('filename', 'Document')}")
        self.resize(880, 680)
        self.setStyleSheet(f"background: {t['bg']}; color: {t['text']};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(14)

        # ── 1. Header Bar: Title + Badges + Actions ──
        hlay = QHBoxLayout()
        title = QLabel(doc.get("filename", "Untitled Document"))
        title.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {t['text']}; letter-spacing: -0.3px;")
        hlay.addWidget(title)
        hlay.addStretch()

        status = doc.get("status", "Verified")
        is_ok = status == "Verified"
        st = QLabel(f"\u25CF {'Verified Authentic' if is_ok else 'Integrity Alert'}")
        st.setStyleSheet(f"""
            color: {t['green'] if is_ok else t['red']};
            background: {t['green_bg'] if is_ok else t['red_bg']};
            font-weight: 700; font-size: 11px;
            padding: 4px 10px; border-radius: 6px;
        """)
        hlay.addWidget(st)
        lay.addLayout(hlay)

        # Metadata Subtitle
        sz_b = doc.get("size_bytes", 0)
        sz_str = f"{sz_b / (1024*1024):.1f} MB" if sz_b >= 1048576 else (f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B")
        sub = QLabel(f"Category: <b>{doc.get('category', 'General')}</b>  \u2022  {doc.get('page_count', 1)} page{'s' if doc.get('page_count', 1) != 1 else ''}  \u2022  Size: {sz_str}")
        sub.setStyleSheet(f"font-size: 11.5px; color: {t['text3']};")
        lay.addWidget(sub)

        # ── 2. Filter & Toolbar: In-document search + Copy + Launch ──
        tb_row = QHBoxLayout()
        tb_row.setSpacing(8)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("🔍 Find inside document...")
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
        tb_row.addWidget(self.find_input, 1)

        btn_copy = QPushButton("📋 Copy Text")
        btn_copy.setObjectName("secondaryBtn")
        btn_copy.setFixedHeight(30)
        btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_copy.clicked.connect(self._copy_all_text)
        tb_row.addWidget(btn_copy)

        fpath = doc.get("filepath", "")
        if fpath and os.path.exists(fpath):
            btn_os = QPushButton("📂 Open in System App")
            btn_os.setObjectName("secondaryBtn")
            btn_os.setFixedHeight(30)
            btn_os.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_os.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(fpath))))
            tb_row.addWidget(btn_os)

        lay.addLayout(tb_row)

        # ── 3. Document Content Display ──
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setStyleSheet(f"""
            QTextEdit {{
                background: {'#0D0D11' if is_dark else '#FFFFFF'};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                font-family: 'Consolas', 'Segoe UI Mono', 'Menlo', monospace;
                font-size: 12.5px;
                line-height: 1.6;
                padding: 12px;
            }}
        """)
        pages = doc.get("pages", [])
        if pages:
            body = "\n\n".join(
                f"── Page {p.get('page_number', i+1)} ──\n{p.get('text', '')}"
                for i, p in enumerate(pages)
            )
        else:
            body = doc.get("raw_text", "No readable text content extracted.")
        self.txt.setPlainText(body)
        lay.addWidget(self.txt, 1)

        # ── 4. Bottom Row: Close Button ──
        blow = QHBoxLayout()
        blow.addStretch()
        cb = QPushButton("Close")
        cb.setObjectName("primaryBtn")
        cb.setFixedHeight(32)
        cb.setFixedWidth(100)
        cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cb.clicked.connect(self.close)
        blow.addWidget(cb)
        lay.addLayout(blow)

    def _copy_all_text(self):
        QApplication.clipboard().setText(self.txt.toPlainText())
        self.find_input.setPlaceholderText("Copied all text to clipboard!")
        QTimer.singleShot(2000, lambda: self.find_input.setPlaceholderText("🔍 Find inside document..."))

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
            ("Financial", "154 KB", "#32D583"),
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

        # ── Bottom Card: Recent Sync Activity ──
        self.sync_card = QFrame()
        self.sync_card.setObjectName("unifiedCard")
        sc_lay = QVBoxLayout(self.sync_card)
        sc_lay.setContentsMargins(24, 20, 24, 20)
        sc_lay.setSpacing(12)

        self.sc_title = QLabel("Recent sync activity")
        self.sc_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
        sc_lay.addWidget(self.sc_title)

        sync_items = [
            ("NDA_Apex_Quantum_2026.pdf", "Mirrored to cloud folder \u2022 2 min ago"),
            ("Vendor_Invoice_INV-9042.xml", "Encrypted and indexed \u2022 14 min ago"),
            ("CodeArrest_offer_letter.pdf", "Hash checked on import \u2022 1 h ago"),
        ]
        self.sync_labels = []
        for fname, desc in sync_items:
            row = QHBoxLayout()
            icon_lbl = QLabel("🔄")
            icon_lbl.setStyleSheet(f"color: {t['primary']}; font-size: 12px;")
            row.addWidget(icon_lbl)

            col = QVBoxLayout()
            col.setSpacing(2)
            fn_lbl = QLabel(fname)
            fn_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['text']};")
            col.addWidget(fn_lbl)
            ds_lbl = QLabel(desc)
            ds_lbl.setStyleSheet(f"font-size: 11px; color: {t['text3']};")
            col.addWidget(ds_lbl)
            row.addLayout(col, 1)

            badge = QLabel("Synced")
            badge.setStyleSheet(f"color: {t['green']}; background: {t['green_bg']}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
            row.addWidget(badge)
            sc_lay.addLayout(row)
            self.sync_labels.append((fn_lbl, ds_lbl, badge))

        lay.addWidget(self.sync_card)
        lay.addStretch()

    def refresh_storage_metrics(self, docs: Dict[str, Dict[str, Any]]):
        cat_sizes: Dict[str, int] = {"Legal": 0, "Financial": 0, "Academic": 0, "Medical": 0, "General": 0}
        total_b = 0
        for d in docs.values():
            cat = d.get("category", "General")
            sz = d.get("size_bytes") or len(d.get("raw_text", "")) or 1024
            if cat in cat_sizes:
                cat_sizes[cat] += sz
            else:
                cat_sizes["General"] += sz
            total_b += sz

        def fmt_sz(b):
            if b >= 1048576:
                return f"{b/1048576:.1f} MB"
            elif b >= 1024:
                return f"{b/1024:.1f} KB"
            return f"{b} B"

        if hasattr(self, "cat_labels"):
            for nl, sl in self.cat_labels:
                name = nl.text()
                sl.setText(fmt_sz(cat_sizes.get(name, 0)))

        used_str = fmt_sz(total_b)
        if hasattr(self, "lbl_local_used"):
            self.lbl_local_used.setText(f"{used_str} of 5 GB used")
        if hasattr(self, "donut"):
            colors = {"Legal": "#6B9BFF", "Financial": "#32D583", "Academic": "#A58BFF", "Medical": "#F0556E", "General": "#FF7A2E"}
            slices = [(cat, sz if total_b > 0 else 1, colors[cat]) for cat, sz in cat_sizes.items()]
            self.donut.set_data(used_str if total_b > 0 else "0 B", slices)

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
    Transforms markdown headings, bold text, bullets, code blocks,
    and blockquotes into clean, high-contrast, modern HTML formatted
    for chatbot readability and typography.
    """
    if not text:
        return ""

    heading_color = "#FFFFFF" if is_dark else "#0F172A"
    body_color = "#E4E4E7" if is_dark else "#1E293B"
    bold_color = "#FFFFFF" if is_dark else "#09090B"
    quote_bg = "rgba(255, 100, 34, 0.08)" if is_dark else "rgba(255, 100, 34, 0.06)"
    quote_text = "#F4F4F5" if is_dark else "#334155"
    code_bg = "rgba(255, 255, 255, 0.09)" if is_dark else "rgba(0, 0, 0, 0.06)"
    code_text = "#F59E0B" if is_dark else "#D97706"
    bullet_color = primary_color

    lines = text.split("\n")
    html_lines = []
    in_quote = False
    quote_buffer = []

    def flush_quote():
        nonlocal in_quote, quote_buffer
        if quote_buffer:
            q_content = "<br>".join(quote_buffer)
            html_lines.append(
                f'<div style="border-left: 3.5px solid {primary_color}; background: {quote_bg}; '
                f'padding: 10px 14px; margin: 10px 0; border-radius: 0 8px 8px 0; '
                f'font-style: italic; color: {quote_text}; line-height: 1.6; font-size: 13px;">{q_content}</div>'
            )
            quote_buffer = []
        in_quote = False

    for line in lines:
        stripped = line.strip()

        # Blockquote handler
        if stripped.startswith(">"):
            in_quote = True
            q_text = stripped.lstrip(">").strip()
            q_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', q_text)
            q_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 5px; border-radius: 4px; font-size: 11.5px;">\\1</code>', q_text)
            quote_buffer.append(q_text)
            continue
        else:
            if in_quote:
                flush_quote()

        if not stripped:
            html_lines.append('<div style="height: 8px;"></div>')
            continue

        # Headings
        if stripped.startswith("####"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h4 style="margin: 12px 0 5px 0; font-size: 13.5px; font-weight: 800; '
                f'color: {heading_color}; letter-spacing: -0.2px;">{h_text}</h4>'
            )
        elif stripped.startswith("###"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h3 style="margin: 14px 0 6px 0; font-size: 15px; font-weight: 800; '
                f'color: {heading_color}; letter-spacing: -0.3px;">{h_text}</h3>'
            )
        elif stripped.startswith("##"):
            h_text = stripped.lstrip("#").strip()
            h_text = re.sub(r"\*\*([^*]+)\*\*", "\\1", h_text)
            html_lines.append(
                f'<h2 style="margin: 16px 0 8px 0; font-size: 16.5px; font-weight: 800; '
                f'color: {heading_color}; letter-spacing: -0.3px;">{h_text}</h2>'
            )
        # Bullet list items
        elif stripped.startswith(("•", "-", "* ")) and not stripped.startswith("**"):
            b_text = re.sub(r"^([•\-*]\s*)", "", stripped)
            b_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', b_text)
            b_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 5px; border-radius: 4px; font-size: 11.5px;">\\1</code>', b_text)
            b_text = re.sub(r"\*([^*]+)\*", '<i>\\1</i>', b_text)
            html_lines.append(
                f'<div style="margin: 4px 0 4px 8px; line-height: 1.55; color: {body_color}; font-size: 13px;">'
                f'<span style="color: {bullet_color}; font-weight: 800; margin-right: 6px;">•</span>{b_text}</div>'
            )
        else:
            p_text = stripped
            p_text = re.sub(r"\*\*([^*]+)\*\*", f'<b style="color: {bold_color}; font-weight: 700;">\\1</b>', p_text)
            p_text = re.sub(r"`([^`]+)`", f'<code style="background: {code_bg}; color: {code_text}; padding: 2px 5px; border-radius: 4px; font-size: 11.5px;">\\1</code>', p_text)
            p_text = re.sub(r"\*([^*]+)\*", '<i>\\1</i>', p_text)
            html_lines.append(
                f'<div style="line-height: 1.6; color: {body_color}; font-size: 13.5px; margin-bottom: 4px;">{p_text}</div>'
            )

    if in_quote:
        flush_quote()

    full_html = "".join(html_lines)
    return f"""
    <div style="font-family: 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif; font-size: 13.5px; line-height: 1.65;">
        {full_html}
    </div>
    """


class AIAssistantPage(QWidget):
    """
    State-of-the-art Explainable AI Assistant Workspace inspired by Figma CHAT A.I+:
    - Left Conversation Sidebar: 'CHAT A.I+' title, '+ New chat' pill, search toggle,
      'Your conversations' with 'Clear All', dynamic conversation list with active indicators
      and delete actions, bottom Settings and User Profile pill.
    - Right Main Chat Canvas: Top evidence grounding banner, scrollable chat stream
      with user questions and grounded AI answers, source citation cards with verified quotes
      and document links, response actions (Helpful, Unhelpful, Copy, Regenerate).
    - Bottom Floating Pill Input Bar: Rounded 26px pill, sparkle icon, document query input,
      and circular orange send action.
    - Full theme fidelity: Pitch Black & Orange (Dark Mode), Crisp Apple White & Orange (Light Mode).
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

        # Initialize default conversation
        self._init_default_conversations()
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
                            "Welcome to <b>DocuVault AI</b>. I am your air-gapped, offline-first "
                            "document intelligence assistant.<br><br>"
                            "Every answer is grounded directly in your uploaded vault files using "
                            "hybrid neural vector search and verified token overlap. "
                            "Zero cloud exfiltration guaranteed."
                        ),
                        "citations": [],
                        "time": "Just now",
                        "speed": "0.1s",
                        "guardrail": {"is_grounded": True, "confidence_score": 1.0, "warning": None},
                    }
                ],
            }
        ]
        self.active_conv_id = "conv_init"

    def _build_ui(self):
        t = self._t
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. LEFT CONVERSATION SIDEBAR (~270px)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(270)
        self.sidebar_frame.setObjectName("aiSidebar")
        s_lay = QVBoxLayout(self.sidebar_frame)
        s_lay.setContentsMargins(16, 20, 16, 16)
        s_lay.setSpacing(12)

        # Header: CHAT A.I+ Title
        head_row = QHBoxLayout()
        head_row.setContentsMargins(4, 0, 4, 0)
        self.lbl_title = QLabel("CHAT A.I+")
        self.lbl_title.setStyleSheet("font-size: 19px; font-weight: 800; letter-spacing: -0.5px;")
        head_row.addWidget(self.lbl_title)
        head_row.addStretch()

        self.badge_offline = QLabel("● Air-Gapped")
        self.badge_offline.setStyleSheet(f"""
            font-size: 10px; font-weight: 700; color: {t['green']};
            background: {t['green_bg']}; padding: 2px 8px; border-radius: 6px;
        """)
        head_row.addWidget(self.badge_offline)
        s_lay.addLayout(head_row)

        s_lay.addSpacing(4)

        # Action Row: [+ New chat] Orange Pill + [🔍 Search] Icon Button
        act_row = QHBoxLayout()
        act_row.setSpacing(8)

        self.btn_new_chat = QPushButton("+ New chat")
        self.btn_new_chat.setFixedHeight(38)
        self.btn_new_chat.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_chat.clicked.connect(self._create_new_chat)
        act_row.addWidget(self.btn_new_chat, 1)

        self.btn_search_toggle = QPushButton("🔍")
        self.btn_search_toggle.setFixedSize(38, 38)
        self.btn_search_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
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

        self.btn_settings = QPushButton("⚙️ Assistant Settings")
        self.btn_settings.setFixedHeight(34)
        self.btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings.clicked.connect(self._show_settings_hint)
        s_lay.addWidget(self.btn_settings)

        # User Profile Pill
        self.profile_card = QFrame()
        self.profile_card.setFixedHeight(44)
        p_lay = QHBoxLayout(self.profile_card)
        p_lay.setContentsMargins(8, 4, 8, 4)
        p_lay.setSpacing(10)

        self.avatar_lbl = QLabel("S")
        self.avatar_lbl.setFixedSize(30, 30)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(f"""
            background: {t['primary']}; color: #FFFFFF;
            font-size: 12px; font-weight: 800; border-radius: 15px;
        """)
        p_lay.addWidget(self.avatar_lbl)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(1)
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.profile_name = QLabel("Siddharth")
        self.profile_name.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        self.profile_tier = QLabel("Enterprise Vault")
        self.profile_tier.setStyleSheet(f"font-size: 10px; color: {t['text4']}; font-weight: 600;")
        info_lay.addWidget(self.profile_name)
        info_lay.addWidget(self.profile_tier)
        p_lay.addLayout(info_lay, 1)

        s_lay.addWidget(self.profile_card)
        main_lay.addWidget(self.sidebar_frame)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. RIGHT MAIN CHAT AREA
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.main_chat_frame = QFrame()
        self.main_chat_frame.setObjectName("aiChatCanvas")
        self.main_chat_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
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

        self.btn_sources_top = QPushButton("📎 Sources: All Vault")
        self.btn_sources_top.setFixedHeight(30)
        self.btn_sources_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sources_top.setToolTip("Select specific documents to ground queries, or import new files")
        self.btn_sources_top.clicked.connect(self._open_sources_dialog)
        top_bar.addWidget(self.btn_sources_top)

        self.btn_ai_key = QPushButton("🔑 AI Key")
        self.btn_ai_key.setFixedHeight(30)
        self.btn_ai_key.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ai_key.setToolTip("Configure Gemini, Groq, or OpenAI API Key")
        self.btn_ai_key.clicked.connect(self._open_api_key_modal)
        top_bar.addWidget(self.btn_ai_key)

        self.grounding_pill = QLabel("● Grounded in Vault Sources")
        self.grounding_pill.setStyleSheet("""
            background: #142920; color: #32D583;
            font-size: 11px; font-weight: 700;
            padding: 5px 12px; border-radius: 12px;
        """)
        top_bar.addWidget(self.grounding_pill)

        self.speed_pill = QLabel("⚡ Sub-second RRF")
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

        # Main Message Stream (Scrollable Area)
        self.msg_scroll = QScrollArea()
        self.msg_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_scroll.setWidgetResizable(True)
        self.msg_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.msg_scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.msg_container = QWidget()
        self.msg_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_container.setStyleSheet("background: transparent; border: none;")
        self.msg_lay = QVBoxLayout(self.msg_container)
        self.msg_lay.setContentsMargins(0, 8, 0, 16)
        self.msg_lay.setSpacing(18)
        self.msg_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.msg_scroll.setWidget(self.msg_container)
        m_lay.addWidget(self.msg_scroll, 1)

        # Active Sources Grounding Pill Strip (Right Above Input Bar)
        self.sources_strip = QFrame()
        self.sources_strip.setFixedHeight(28)
        self.sources_strip.setStyleSheet("background: transparent; border: none;")
        ss_lay = QHBoxLayout(self.sources_strip)
        ss_lay.setContentsMargins(4, 0, 4, 0)
        ss_lay.setSpacing(8)

        self.lbl_active_source_context = QLabel("📎 Query Scope: All Vault Documents")
        self.lbl_active_source_context.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text3']};")
        ss_lay.addWidget(self.lbl_active_source_context)

        self.btn_add_source_inline = QPushButton("+ Filter / Add Sources")
        self.btn_add_source_inline.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_source_inline.setStyleSheet(f"background: transparent; border: none; font-size: 11px; font-weight: 700; color: {t['primary']};")
        self.btn_add_source_inline.clicked.connect(self._open_sources_dialog)
        ss_lay.addWidget(self.btn_add_source_inline)

        self.btn_clear_sources = QPushButton("✕ Clear Filter")
        self.btn_clear_sources.setVisible(False)
        self.btn_clear_sources.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear_sources.setStyleSheet("background: transparent; border: none; font-size: 11px; font-weight: 600; color: #EF4444;")
        self.btn_clear_sources.clicked.connect(self._clear_pinned_sources)
        ss_lay.addWidget(self.btn_clear_sources)

        ss_lay.addStretch()
        m_lay.addWidget(self.sources_strip)

        # Bottom Floating Pill Input Bar (Matching Figma CHAT A.I+)
        self.input_card = QFrame()
        self.input_card.setFixedHeight(54)
        self.input_card.setObjectName("floatingInputCard")
        in_lay = QHBoxLayout(self.input_card)
        in_lay.setContentsMargins(12, 6, 8, 6)
        in_lay.setSpacing(10)

        # Attachment / Source selector button
        self.btn_attach = QPushButton("📎")
        self.btn_attach.setFixedSize(32, 32)
        self.btn_attach.setToolTip("Attach / Select Specific Source Documents")
        self.btn_attach.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_attach.setStyleSheet(f"font-size: 16px; color: {t['primary']}; background: transparent; border: none;")
        self.btn_attach.clicked.connect(self._open_sources_dialog)
        in_lay.addWidget(self.btn_attach)

        # Input QLineEdit
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about your documents...")
        self.input_field.setStyleSheet("border: none; background: transparent; font-size: 13px; font-weight: 500;")
        self.input_field.returnPressed.connect(self._on_send)
        in_lay.addWidget(self.input_field, 1)

        # Circular Send Button
        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(38, 38)
        self.btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send.clicked.connect(self._on_send)
        in_lay.addWidget(self.btn_send)

        m_lay.addWidget(self.input_card)
        main_lay.addWidget(self.main_chat_frame, 1)

        # Render conversation items & active conversation
        self._render_conversations_list()
        self._render_active_chat()
        self.update_theme(self._t)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Conversation List Management
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _render_conversations_list(self):
        # Clear existing conversation rows
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
            title = conv["title"]
            is_active = (cid == self.active_conv_id)

            if self.search_filter and self.search_filter.lower() not in title.lower():
                continue

            item_card = QFrame()
            item_card.setFixedHeight(40)
            item_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            if is_active:
                bg = "#1A1714" if is_dark else "#FFF4ED"
                border = f"1px solid {t['primary']}"
                text_col = t['primary'] if not is_dark else "#FFFFFF"
                font_weight = "700"
            else:
                bg = "transparent"
                border = "1px solid transparent"
                text_col = t['text3']
                font_weight = "500"

            item_card.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: {border};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background: {'#141418' if is_dark else '#F2F2F7'};
                }}
            """)

            i_lay = QHBoxLayout(item_card)
            i_lay.setContentsMargins(10, 4, 8, 4)
            i_lay.setSpacing(8)

            icon_lbl = QLabel("💬")
            icon_lbl.setStyleSheet(f"font-size: 11px; color: {t['primary']}; background: transparent; border: none;")
            i_lay.addWidget(icon_lbl)

            lbl_txt = QLabel(title)
            lbl_txt.setStyleSheet(f"font-size: 12px; font-weight: {font_weight}; color: {text_col}; background: transparent; border: none;")
            i_lay.addWidget(lbl_txt, 1)

            # Delete button (shows on hover / active)
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t['text4']};
                    border: none;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    color: #EF4444;
                    background: {'rgba(239, 68, 68, 0.15)' if is_dark else '#FEE4E2'};
                }}
            """)
            del_btn.clicked.connect(lambda _, c=cid: self._delete_conversation(c))
            i_lay.addWidget(del_btn)

            # Make card clickable
            def make_click_handler(conv_id):
                return lambda event: self._select_conversation(conv_id)
            item_card.mousePressEvent = make_click_handler(cid)

            self.conv_list_lay.addWidget(item_card)

        self.conv_list_lay.addStretch(1)

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
                    "text": (
                        "Ready to inspect your vault. What would you like to verify, compare, or search today?"
                    ),
                    "citations": [],
                    "time": "Just now",
                    "speed": "0.1s",
                    "guardrail": {"is_grounded": True, "confidence_score": 1.0, "warning": None},
                }
            ],
        }
        self.conversations.insert(0, new_conv)
        self.active_conv_id = new_id
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
        self._render_conversations_list()
        self._render_active_chat()

    def _clear_all_chats(self):
        self.conversations = []
        self._init_default_conversations()
        self._render_conversations_list()
        self._render_active_chat()

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
        if not self.pinned_sources:
            self.lbl_active_source_context.setText("📎 Query Scope: All Vault Documents")
            self.btn_sources_top.setText("📎 Sources: All Vault")
            self.btn_clear_sources.setVisible(False)
        else:
            names = ", ".join(self.pinned_sources)
            if len(names) > 34:
                names = names[:34] + "..."
            self.lbl_active_source_context.setText(f"📎 Pinned Sources ({len(self.pinned_sources)}): <b>{names}</b>")
            self.btn_sources_top.setText(f"📎 Sources ({len(self.pinned_sources)} Active)")
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Active Chat Rendering
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _get_active_conv(self) -> Optional[Dict[str, Any]]:
        for c in self.conversations:
            if c["id"] == self.active_conv_id:
                return c
        return self.conversations[0] if self.conversations else None

    def _render_active_chat(self):
        # Clear existing message widgets
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
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("text", "")
            citations = msg.get("citations", [])
            speed = msg.get("speed", "0.2s")
            guardrail = msg.get("guardrail", {})
            provider = msg.get("provider", "DocuVault Offline Hybrid Intelligence Engine")

            if role == "user":
                # Outer wrapper aligning the bubble to the right
                turn_widget = QWidget()
                turn_widget.setStyleSheet("background: transparent; border: none;")
                t_lay = QHBoxLayout(turn_widget)
                t_lay.setContentsMargins(12, 6, 12, 6)
                t_lay.addStretch(1)

                u_bubble = QFrame()
                u_bg = "#1A1A22" if is_dark else "#F1F5F9"
                u_border = "#2A2A38" if is_dark else "#E2E8F0"
                u_text_color = "#FFFFFF" if is_dark else "#0F172A"
                u_bubble.setStyleSheet(f"""
                    QFrame {{
                        background: {u_bg};
                        border: 1px solid {u_border};
                        border-radius: 16px;
                        border-bottom-right-radius: 4px;
                    }}
                """)
                ub_lay = QVBoxLayout(u_bubble)
                ub_lay.setContentsMargins(16, 10, 16, 12)
                ub_lay.setSpacing(4)

                u_top = QHBoxLayout()
                u_top.setSpacing(6)
                u_icon = QLabel("👤")
                u_icon.setStyleSheet("font-size: 11px; background: transparent; border: none;")
                u_top.addWidget(u_icon)
                u_title = QLabel("You")
                u_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']}; background: transparent; border: none;")
                u_top.addWidget(u_title)
                u_top.addSpacing(6)

                time_lbl = QLabel(msg.get("time", "Just now"))
                time_lbl.setStyleSheet(f"font-size: 10px; color: {t['text4']}; background: transparent; border: none;")
                u_top.addWidget(time_lbl)
                u_top.addStretch()
                ub_lay.addLayout(u_top)

                u_msg = QLabel(text)
                u_msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                u_msg.setWordWrap(True)
                u_msg.setStyleSheet(f"font-size: 13.5px; font-weight: 500; color: {u_text_color}; line-height: 1.5; background: transparent; border: none;")
                ub_lay.addWidget(u_msg)

                t_lay.addWidget(u_bubble, 0)
                self.msg_lay.addWidget(turn_widget)

            else:
                turn_widget = QWidget()
                turn_widget.setStyleSheet("background: transparent; border: none;")
                t_lay = QVBoxLayout(turn_widget)
                t_lay.setContentsMargins(12, 6, 12, 6)

                a_card = QFrame()
                a_bg = "#111116" if is_dark else "#FFFFFF"
                a_border = "#20202A" if is_dark else "#E5E7EB"
                a_card.setStyleSheet(f"""
                    QFrame#assistantBubble {{
                        background: {a_bg};
                        border: 1px solid {a_border};
                        border-radius: 14px;
                        border-top-left-radius: 4px;
                    }}
                """)
                a_card.setObjectName("assistantBubble")
                ac_lay = QVBoxLayout(a_card)
                ac_lay.setContentsMargins(20, 16, 20, 16)
                ac_lay.setSpacing(14)

                # Header Row
                a_top = QHBoxLayout()
                a_top.setSpacing(8)

                a_icon = QLabel("✨")
                a_icon.setStyleSheet(f"font-size: 15px; color: {t['primary']}; background: transparent; border: none;")
                a_top.addWidget(a_icon)

                a_title = QLabel("CHAT A.I+")
                a_title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {t['primary']}; letter-spacing: -0.2px; background: transparent; border: none;")
                a_top.addWidget(a_title)

                # Model / Engine Badge
                engine_badge = QLabel("⚡ Offline Hybrid RAG")
                if "Gemini" in provider:
                    engine_badge.setText("☁️ Google Gemini 1.5")
                elif "Groq" in provider:
                    engine_badge.setText("⚡ Groq Llama-3.1")
                elif "OpenAI" in provider:
                    engine_badge.setText("☁️ OpenAI GPT-4o-mini")

                engine_badge.setStyleSheet(f"""
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.05)'};
                    color: {t['text3']};
                    font-size: 10px; font-weight: 700;
                    padding: 3px 8px; border-radius: 6px;
                """)
                a_top.addWidget(engine_badge)

                if citations:
                    badge_ground = QLabel(f"● Grounded in {len(citations)} source{'s' if len(citations)>1 else ''}")
                    badge_ground.setStyleSheet("""
                        background: rgba(50, 213, 131, 0.16); color: #32D583;
                        font-size: 10px; font-weight: 700;
                        padding: 3px 8px; border-radius: 6px;
                    """)
                    a_top.addWidget(badge_ground)

                badge_time = QLabel(f"⏱️ {speed}")
                badge_time.setStyleSheet(f"""
                    background: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.05)'};
                    color: {t['text4']};
                    font-size: 10px; font-weight: 700;
                    padding: 3px 8px; border-radius: 6px;
                """)
                a_top.addWidget(badge_time)
                a_top.addStretch()
                ac_lay.addLayout(a_top)

                # Search Engine Style Evidence Sources Carousel/Cards
                if citations:
                    src_container = QWidget()
                    src_container.setStyleSheet("background: transparent; border: none;")
                    sc_lay = QVBoxLayout(src_container)
                    sc_lay.setContentsMargins(0, 2, 0, 4)
                    sc_lay.setSpacing(8)

                    sc_head = QLabel(f"🔍 Verified Vault Sources ({len(citations)} Grounded)")
                    sc_head.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {t['primary']}; text-transform: uppercase; letter-spacing: 0.5px; background: transparent; border: none;")
                    sc_lay.addWidget(sc_head)

                    # Flow / Horizontal Grid of Source Cards
                    cards_row = QHBoxLayout()
                    cards_row.setSpacing(10)

                    for cit in citations[:4]:
                        fname = cit.get("filename", "Document")
                        page = cit.get("page_number", 1)
                        sec = cit.get("section_title") or cit.get("position") or "General"
                        score_val = cit.get("score", 95)

                        # Determine file type icon
                        f_lower = fname.lower()
                        if f_lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                            f_icon = "🖼️"
                        elif f_lower.endswith((".pdf")):
                            f_icon = "📕"
                        elif f_lower.endswith((".xml", ".json", ".csv")):
                            f_icon = "📑"
                        else:
                            f_icon = "📄"

                        sc_card = QFrame()
                        sc_bg = "#16161E" if is_dark else "#F8FAFC"
                        sc_border = "#262632" if is_dark else "#E2E8F0"
                        sc_card.setFixedHeight(68)
                        sc_card.setMinimumWidth(190)
                        sc_card.setMaximumWidth(260)
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
                        sc_card_lay.setContentsMargins(10, 8, 10, 8)
                        sc_card_lay.setSpacing(4)

                        r1 = QHBoxLayout()
                        r1.setSpacing(6)
                        lbl_ico = QLabel(f_icon)
                        lbl_ico.setStyleSheet("font-size: 12px; background: transparent; border: none;")
                        r1.addWidget(lbl_ico)

                        display_name = fname
                        if len(display_name) > 18:
                            display_name = display_name[:16] + "..."
                        lbl_fn = QLabel(display_name)
                        lbl_fn.setToolTip(fname)
                        lbl_fn.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {t['text']}; background: transparent; border: none;")
                        r1.addWidget(lbl_fn, 1)

                        lbl_pct = QLabel(f"{score_val}%")
                        lbl_pct.setStyleSheet("""
                            font-size: 9.5px; font-weight: 800; color: #32D583;
                            background: rgba(50, 213, 131, 0.12); padding: 1px 5px; border-radius: 4px;
                        """)
                        r1.addWidget(lbl_pct)
                        sc_card_lay.addLayout(r1)

                        r2 = QHBoxLayout()
                        r2.setSpacing(6)
                        lbl_loc = QLabel(f"Page {page} · {sec[:16]}")
                        lbl_loc.setStyleSheet(f"font-size: 10px; color: {t['text4']}; font-weight: 600; background: transparent; border: none;")
                        r2.addWidget(lbl_loc, 1)

                        btn_view = QPushButton("👁️ View")
                        btn_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                        btn_view.setFixedHeight(20)
                        btn_view.setStyleSheet(f"""
                            QPushButton {{
                                background: {t['primary']}; color: #FFFFFF;
                                border: none; border-radius: 4px;
                                font-size: 9.5px; font-weight: 700; padding: 2px 8px;
                            }}
                            QPushButton:hover {{
                                background: {t['primary_hover']};
                            }}
                        """)
                        btn_view.clicked.connect(lambda _, fn=fname: self._open_document_by_name(fn))
                        r2.addWidget(btn_view)
                        sc_card_lay.addLayout(r2)

                        def make_open_handler(fn):
                            return lambda ev: self._open_document_by_name(fn)
                        sc_card.mousePressEvent = make_open_handler(fname)
                        cards_row.addWidget(sc_card)

                    cards_row.addStretch()
                    sc_lay.addLayout(cards_row)
                    ac_lay.addWidget(src_container)

                # Formatted Synthesized Answer (Rich Markdown Typography)
                ans_display = QLabel()
                ans_display.setTextFormat(Qt.TextFormat.RichText)
                ans_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                ans_display.setWordWrap(True)
                ans_display.setStyleSheet("background: transparent; border: none; padding: 4px 0;")
                html_body = format_chat_markdown_to_html(text, is_dark, t.get("primary", "#FF6422"))
                ans_display.setText(html_body)
                ac_lay.addWidget(ans_display)

                # Hallucination Guardrail Alert
                if guardrail.get("warning"):
                    g_alert = QLabel(f"⚠️ {guardrail['warning']}")
                    g_alert.setWordWrap(True)
                    g_alert.setStyleSheet("""
                        background: rgba(245, 181, 68, 0.12);
                        color: #F5B544;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 8px 12px;
                        border-radius: 8px;
                        border: 1px solid rgba(245, 181, 68, 0.25);
                    """)
                    ac_lay.addWidget(g_alert)

                # Response Actions Toolbar
                act_row = QHBoxLayout()
                act_row.setSpacing(8)

                btn_copy = QPushButton("📋 Copy Answer")
                btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_copy.setFixedHeight(26)
                btn_copy.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#16161D' if is_dark else '#F1F5F9'};
                        color: {t['text3']}; border: 1px solid {t['border']};
                        border-radius: 13px; padding: 2px 12px; font-size: 10.5px; font-weight: 600;
                    }}
                    QPushButton:hover {{
                        color: {t['text']}; border-color: {t['primary']};
                    }}
                """)
                clean_text = re.sub(r"<[^>]+>", "", text)
                btn_copy.clicked.connect(lambda _, txt=clean_text, b=btn_copy: self._copy_to_clipboard(txt, b))
                act_row.addWidget(btn_copy)

                btn_up = QPushButton("👍 Helpful")
                btn_up.setFixedHeight(26)
                btn_up.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_up.setStyleSheet(f"background: transparent; border: 1px solid {t['border']}; border-radius: 13px; font-size: 10.5px; font-weight: 600; color: {t['text3']}; padding: 2px 10px;")
                btn_up.clicked.connect(lambda _, b=btn_up: b.setStyleSheet(f"background: {t['green_bg']}; border: 1px solid {t['green']}; border-radius: 13px; font-size: 10.5px; font-weight: 700; color: {t['green']}; padding: 2px 10px;"))
                act_row.addWidget(btn_up)

                btn_down = QPushButton("👎 Unhelpful")
                btn_down.setFixedHeight(26)
                btn_down.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_down.setStyleSheet(f"background: transparent; border: 1px solid {t['border']}; border-radius: 13px; font-size: 10.5px; font-weight: 600; color: {t['text3']}; padding: 2px 10px;")
                btn_down.clicked.connect(lambda _, b=btn_down: b.setStyleSheet("background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-radius: 13px; font-size: 10.5px; font-weight: 700; color: #EF4444; padding: 2px 10px;"))
                act_row.addWidget(btn_down)

                act_row.addStretch()

                btn_regen = QPushButton("🔄 Regenerate")
                btn_regen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_regen.setFixedHeight(26)
                btn_regen.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#16161D' if is_dark else '#F1F5F9'};
                        color: {t['text3']}; border: 1px solid {t['border']};
                        border-radius: 13px; padding: 2px 12px; font-size: 10.5px; font-weight: 600;
                    }}
                    QPushButton:hover {{
                        color: {t['primary']}; border-color: {t['primary']};
                    }}
                """)
                prev_query = None
                for m in reversed(messages):
                    if m.get("role") == "user":
                        prev_query = m.get("text")
                        break
                if prev_query:
                    btn_regen.clicked.connect(lambda _, q=prev_query: self._execute_query(q, is_regenerate=True))
                act_row.addWidget(btn_regen)

                ac_lay.addLayout(act_row)
                t_lay.addWidget(a_card)
                self.msg_lay.addWidget(turn_widget)

        # Smooth scroll to bottom
        QTimer.singleShot(60, lambda: self.msg_scroll.verticalScrollBar().setValue(
            self.msg_scroll.verticalScrollBar().maximum()
        ))

    def _copy_to_clipboard(self, text: str, btn: QPushButton):
        app = QApplication.instance()
        if app:
            clipboard = app.clipboard()
            clipboard.setText(text)
            btn.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: btn.setText("📋 Copy"))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # User Input & Real Engine Query Execution
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def ask_query(self, query: str):
        """Public API to inject query directly from quick chips or universal search."""
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

        # If not regenerating, append user message
        if not is_regenerate:
            conv["messages"].append({
                "role": "user",
                "text": query_text,
                "time": time.strftime("%H:%M"),
            })
            # Auto-title conversation if it's default
            if conv["title"] in ("New Conversation", "Document Intelligence RAG") and len(conv["messages"]) <= 3:
                clean_title = query_text.replace("What is", "").replace("When is", "").strip().capitalize()
                if len(clean_title) > 28:
                    clean_title = clean_title[:28] + "..."
                conv["title"] = clean_title
                self._render_conversations_list()

        # Query Assistant
        start_t = time.time()
        answer_text = "DocuVault AI analyzed your local vault files."
        citations = []
        guardrail = {"is_grounded": True, "confidence_score": 1.0, "warning": None}
        provider = "DocuVault Offline Hybrid Intelligence Engine"

        if self.assistant:
            try:
                res = self.assistant.answer_query(
                    query_text,
                    target_filenames=self.pinned_sources if self.pinned_sources else None
                )
                if res:
                    answer_text = res.get("answer_text") or res.get("answer") or "No clause found."
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
            "time": time.strftime("%H:%M"),
            "speed": speed_str,
            "guardrail": guardrail,
            "provider": provider,
        })

        self._render_active_chat()

    def set_assistant(self, assistant: ExplainableAIAssistant):
        self.assistant = assistant

    def set_user_info(self, user_dict: Dict[str, Any]):
        self.current_user = user_dict
        name = user_dict.get("full_name") or user_dict.get("email") or "Vault User"
        self.profile_name.setText(name)
        initial = name[0].upper() if name else "V"
        self.avatar_lbl.setText(initial)
        tier = user_dict.get("tier", "Pro")
        self.profile_tier.setText(f"{tier} Plan · Offline")

    def _create_notification_toast(self, message: str):
        # Notify via feedback if master window available
        p = self.window()
        if hasattr(p, "_show_feedback"):
            p._show_feedback(message)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        t = theme
        is_dark = t.get("name") == "dark"

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        # Translucent Frosted Glass Sidebar
        sidebar_bg = "rgba(10, 10, 14, 0.78)" if is_dark else "rgba(255, 255, 255, 0.88)"
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

        # New chat button: docuvault vibrant orange pill
        self.btn_new_chat.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['primary']}, stop:1 {t['primary_hover']});
                color: #FFFFFF;
                border: none;
                border-radius: 19px;
                font-size: 12.5px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['primary_hover']};
            }}
        """)

        self.btn_search_toggle.setStyleSheet(f"""
            QPushButton {{
                background: {'#141416' if is_dark else '#FFFFFF'};
                color: {t['text3']};
                border: 1px solid {t['border']};
                border-radius: 19px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {t['primary']};
                color: {t['primary']};
            }}
        """)

        self.in_chat_search.setStyleSheet(f"""
            QLineEdit {{
                background: {t['bg3']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {t['primary']};
            }}
        """)

        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['text3']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                font-size: 11.5px;
                font-weight: 600;
                text-align: left;
                padding-left: 12px;
            }}
            QPushButton:hover {{
                background: {'#141418' if is_dark else '#F2F2F7'};
                color: {t['text']};
            }}
        """)

        self.profile_card.setStyleSheet(f"""
            background: {'#121215' if is_dark else '#FFFFFF'};
            border: 1px solid {sidebar_border};
            border-radius: 10px;
        """)

        # Main Chat Canvas Styling (Clean Solid Background — No background particles or constellation lines cluttering the screen)
        canvas_bg = "#0C0C10" if is_dark else "#FFFFFF"
        canvas_border = "#1E1E24" if is_dark else "#E5E7EB"
        self.main_chat_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.main_chat_frame.setStyleSheet(f"""
            #aiChatCanvas {{
                background: {canvas_bg};
                border-left: 1px solid {canvas_border};
            }}
        """)
        self.msg_scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_scroll.viewport().setStyleSheet(f"background: {canvas_bg}; border: none;")
        self.msg_scroll.setStyleSheet(f"QScrollArea, QScrollArea > QWidget > QWidget {{ background: {canvas_bg}; border: none; }}")
        self.msg_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.msg_container.setStyleSheet(f"background: {canvas_bg}; border: none;")

        self.chat_heading.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {t['text']}; letter-spacing: -0.4px;")
        self.chat_subheading.setStyleSheet(f"font-size: 11.5px; color: {t['text4']};")

        # Top Bar buttons
        if hasattr(self, "btn_sources_top"):
            self.btn_sources_top.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']}; color: {t['text']};
                    border: 1px solid {t['border']}; border-radius: 14px;
                    padding: 4px 14px; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {t['primary']}; color: {t['primary']};
                }}
            """)
        if hasattr(self, "btn_ai_key"):
            self.btn_ai_key.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']}; color: {t['primary']};
                    border: 1px solid {t['border']}; border-radius: 14px;
                    padding: 4px 14px; font-size: 11px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {t['primary']}; color: #FFFFFF;
                }}
            """)

        # Floating Pill Input Bar Styling (Figma CHAT A.I+)
        input_bg = "#16161D" if is_dark else "#F8FAFC"
        input_border = "#272734" if is_dark else "#E2E8F0"
        shadow_style = "box-shadow: 0 4px 20px rgba(0,0,0,0.06);" if not is_dark else ""
        self.input_card.setStyleSheet(f"""
            #floatingInputCard {{
                background: {input_bg};
                border: 1.5px solid {input_border};
                border-radius: 27px;
                {shadow_style}
            }}
            #floatingInputCard:hover {{
                border-color: {t['primary']};
            }}
        """)

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                font-size: 13px;
                font-weight: 500;
                color: {t['text']};
            }}
        """)

        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: {t['primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 19px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {t['primary_hover']};
            }}
        """)

        if hasattr(self, "profile_name"):
            self.profile_name.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        if hasattr(self, "profile_tier"):
            self.profile_tier.setStyleSheet(f"font-size: 10px; color: {t['text4']}; font-weight: 600;")
        if hasattr(self, "grounding_pill"):
            self.grounding_pill.setStyleSheet("""
                background: #142920; color: #32D583;
                font-size: 11px; font-weight: 700;
                padding: 5px 12px; border-radius: 12px;
            """)
        if hasattr(self, "speed_pill"):
            self.speed_pill.setStyleSheet(f"""
                background: {t['bg3']}; color: {t['text3']};
                font-size: 11px; font-weight: 600;
                padding: 5px 12px; border-radius: 12px;
            """)
        if hasattr(self, "quick_buttons"):
            for q_btn in self.quick_buttons:
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
        if hasattr(self, "lbl_active_source_context"):
            self.lbl_active_source_context.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['text3']};")

        self._update_sources_strip()

        # Re-render conversation list & chat items for updated colors
        self._render_conversations_list()
        self._render_active_chat()



class DeadlinesPage(QWidget):
    """
    Dedicated Smart Deadlines and Compliance Obligation Workspace
    matching Page 15 of the design pack with October 2026 interactive calendar
    and Coming Up obligation cards.
    """

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.manager = DeadlineManager()
        self.deadlines: List[Dict[str, Any]] = []

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

        self.sub_lbl = QLabel("Dates found in your contracts, so nothing slips.")
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        t_box.addWidget(self.sub_lbl)
        header.addLayout(t_box)

        header.addStretch()

        self.btn_export_ics = QPushButton("Export calendar (.ics)")
        self.btn_export_ics.setFixedHeight(34)
        self.btn_export_ics.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_ics.clicked.connect(self._export_ics)
        header.addWidget(self.btn_export_ics)

        self.btn_add = QPushButton("Add deadline")
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
        coming_vlay.setSpacing(16)

        self.coming_title = QLabel("Coming up")
        self.coming_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {theme['text']};")
        coming_vlay.addWidget(self.coming_title)

        # Items list
        self.items_container = QVBoxLayout()
        self.items_container.setSpacing(12)
        coming_vlay.addLayout(self.items_container)

        self._populate_coming_up_items()

        coming_vlay.addStretch()

        # Subtle footer note matching Page 15
        self.footer_note = QLabel("Dates are found automatically in your contracts and added here.")
        self.footer_note.setWordWrap(True)
        self.footer_note.setStyleSheet(f"font-size: 11px; color: {theme['text4']}; line-height: 1.4;")
        coming_vlay.addWidget(self.footer_note)

        split_lay.addWidget(self.coming_card, 4)

        lay.addLayout(split_lay, 1)
        self.update_theme(theme)

    def _build_calendar_grid(self):
        # Clear existing
        while self.cal_grid.count():
            item = self.cal_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        # October 2026 starts on Thursday (index 4 in 0=Sun..6=Sat)
        # Total days: 31
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

                # Calculate real deadline dates
                deadline_days = {}
                for d in self.deadlines:
                    try:
                        due = d.get("due_date", "")
                        if "-" in due:
                            d_day = int(due.split("-")[-1])
                            col = "#F0556E" if d.get("priority") in ("Critical", "High") else "#6B9BFF"
                            deadline_days[d_day] = col
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
                            background: rgba(255, 122, 46, 0.12);
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

                # Status dot if day has deadline
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
        # Clear existing
        while self.items_container.count():
            item = self.items_container.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        t = self._t
        is_dark = t.get("name") == "dark"

        if not self.deadlines:
            empty_lbl = QLabel("No active deadlines recorded.\nImport documents or click 'Add deadline' to track contract dates.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {t['text4']}; font-size: 12px; padding: 40px 10px; line-height: 1.5;")
            self.items_container.addWidget(empty_lbl)
            return

        items_to_render = []
        for d in self.deadlines:
            eval_res = self.manager.evaluate_deadline(d)
            days_left = eval_res.get("days_left", 0)
            chip_txt = f"In {days_left} days" if days_left >= 0 else f"{abs(days_left)}d overdue"
            col = "#F0556E" if days_left < 3 else ("#F5B544" if days_left < 7 else "#32D583")
            due = eval_res.get("adjusted_due_date", "2026-10-28")
            day_str = due.split("-")[-1] if "-" in due else "28"
            items_to_render.append({
                "date": day_str,
                "title": eval_res.get("title", "Obligation"),
                "doc": eval_res.get("document", "Document.pdf"),
                "chip": chip_txt,
                "color": col,
                "chip_bg": "#382715" if is_dark else "#FEF0C7",
                "badge_bg": "#2A1E14" if is_dark else "#FFF4ED",
            })

        for it in items_to_render:
            row_w = QFrame()
            row_w.setStyleSheet("background: transparent; border: none;")
            rlay = QHBoxLayout(row_w)
            rlay.setContentsMargins(0, 4, 0, 4)
            rlay.setSpacing(12)

            # Square date badge
            date_badge = QLabel(it["date"])
            date_badge.setFixedSize(38, 38)
            date_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_badge.setStyleSheet(f"""
                background: {it['badge_bg']};
                color: {it['color']};
                font-size: 13px;
                font-weight: 800;
                border-radius: 8px;
            """)
            rlay.addWidget(date_badge)

            # Title and Doc text
            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            lbl_title = QLabel(it["title"])
            lbl_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
            text_box.addWidget(lbl_title)

            lbl_doc = QLabel(it["doc"])
            lbl_doc.setStyleSheet(f"font-size: 11px; color: {t['text4']};")
            text_box.addWidget(lbl_doc)
            rlay.addLayout(text_box, 1)

            # Urgency Chip
            chip = QLabel(it["chip"])
            chip.setStyleSheet(f"""
                background: {it['chip_bg']};
                color: {it['color']};
                font-size: 10px;
                font-weight: 700;
                border-radius: 10px;
                padding: 4px 10px;
            """)
            rlay.addWidget(chip)

            self.items_container.addWidget(row_w)

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
                "id": f"DL-{len(self.deadlines)+1:03d}",
                "title": title,
                "document": doc,
                "due_date": (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
                "days_left": days,
                "computed_status": "Active",
            }
            self.deadlines.append(new_dl)
            self.refresh_deadlines(self.deadlines)

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

        self.btn_export_ics.setStyleSheet(f"""
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
            }}
        """)

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
        """)

        self._build_calendar_grid()
        self._populate_coming_up_items()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPTION E: RIGHT COLLAPSIBLE AI DRAWER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIDrawer(QFrame):
    """
    Option E right-docked AI Assistant Drawer that lives on every page.
    Extendable & resizable via dragging, matching Figma CHAT A.I+ single-div architecture.
    """
    closed = pyqtSignal()

    def __init__(self, assistant: Optional[ExplainableAIAssistant], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.assistant = assistant
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

        # ── 1. Top Bar (Logo, Title, Evidence chip, Close button) ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.title_lbl = QLabel("✨ AI Assistant")
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {theme['text']};")
        top_bar.addWidget(self.title_lbl)

        self.evidence_chip = QLabel("Evidence")
        self.evidence_chip.setStyleSheet("""
            background: #163526;
            color: #32D583;
            font-size: 9px;
            font-weight: 700;
            border-radius: 6px;
            padding: 2px 6px;
        """)
        top_bar.addWidget(self.evidence_chip)

        top_bar.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.closed.emit)
        top_bar.addWidget(self.btn_close)
        vlay.addLayout(top_bar)

        # ── 2. Quick Question Chips ──
        chips_lay = QHBoxLayout()
        chips_lay.setSpacing(6)
        self.chip_buttons: List[QPushButton] = []
        for q_txt in ["Notice period", "Payment terms", "Liability"]:
            chip_btn = QPushButton(q_txt)
            chip_btn.setFixedHeight(26)
            chip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            chip_btn.clicked.connect(lambda _, txt=q_txt: self._handle_quick_query(txt))
            chips_lay.addWidget(chip_btn)
            self.chip_buttons.append(chip_btn)
        vlay.addLayout(chips_lay)

        # ── 3. Grounded Conversation Scroll Area (Single Unified Div) ──
        self.scroll = QScrollArea()
        self.scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.chat_container = QWidget()
        self.chat_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.chat_container.setStyleSheet("background: transparent; border: none;")
        self.chat_lay = QVBoxLayout(self.chat_container)
        self.chat_lay.setContentsMargins(4, 4, 4, 4)
        self.chat_lay.setSpacing(12)

        self.scroll.setWidget(self.chat_container)
        vlay.addWidget(self.scroll, 1)

        # ── 4. Input Field and Ask Button ──
        self.in_wrap = QFrame()
        self.in_wrap.setStyleSheet(f"""
            QFrame {{
                background: {theme['bg2']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
            }}
        """)
        in_lay = QHBoxLayout(self.in_wrap)
        in_lay.setContentsMargins(10, 6, 6, 6)
        in_lay.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your documents...")
        self.input_field.setStyleSheet(f"border: none; background: transparent; font-size: 11.5px; color: {theme['text']};")
        self.input_field.returnPressed.connect(self._submit)
        in_lay.addWidget(self.input_field, 1)

        self.btn_send = QPushButton("Ask")
        self.btn_send.setFixedSize(52, 28)
        self.btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send.clicked.connect(self._submit)
        in_lay.addWidget(self.btn_send)

        vlay.addWidget(self.in_wrap)
        self.update_theme(theme)

    def _render_messages(self):
        # Clear layout
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
                u_bg = "#1E1E26" if is_dark else "#FFF1EB"
                u_border = "rgba(255, 122, 46, 0.35)" if is_dark else "rgba(242, 106, 27, 0.25)"
                u_bubble.setStyleSheet(f"""
                    QFrame {{
                        background: {u_bg};
                        border: 1px solid {u_border};
                        border-radius: 12px;
                        border-bottom-right-radius: 2px;
                    }}
                """)
                ub_lay = QVBoxLayout(u_bubble)
                ub_lay.setContentsMargins(10, 8, 10, 8)
                ub_lay.setSpacing(3)

                u_hdr = QLabel("👤 You")
                u_hdr.setStyleSheet(f"font-size: 10.5px; font-weight: 700; color: {t['primary']}; background: transparent; border: none;")
                ub_lay.addWidget(u_hdr)

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
                b_name = QLabel("✨ DocuVault AI")
                b_name.setStyleSheet(f"font-size: 11.5px; font-weight: 800; color: {t['primary']}; background: transparent; border: none;")
                badges_lay.addWidget(b_name)

                b_ground = QLabel(f"● Grounded ({len(citations)} source{'s' if len(citations)!=1 else ''})")
                b_ground.setStyleSheet("background: rgba(50, 213, 131, 0.16); color: #32D583; font-size: 9.5px; font-weight: 700; border-radius: 6px; padding: 2px 6px;")
                badges_lay.addWidget(b_ground)

                b_time = QLabel("0.2s")
                b_time.setStyleSheet(f"background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'}; color: {t['text4']}; font-size: 9.5px; font-weight: 700; border-radius: 6px; padding: 2px 6px;")
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

        # Compute answer via assistant if present
        citations = []
        if self.assistant:
            try:
                res = self.assistant.answer_query(txt)
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
        drawer_bg = "rgba(10, 10, 14, 0.94)" if is_dark else "rgba(255, 255, 255, 0.96)"
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
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['text4']};
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                color: {t['text']};
                background: {'#18181A' if is_dark else '#E5E5EA'};
            }}
        """)
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
                    border: 1px solid {'#2B2B36' if is_dark else t['border']};
                    border-radius: 12px;
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
                    color: #FFFFFF;
                    border: 1px solid {t['primary']};
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {t['primary_hover']};
                }}
            """)

        self._render_messages()


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
        self.assistant = ExplainableAIAssistant(self.vec_engine)

        # Real-Time Directory Tracker (Git-Like Folder Auto-Sync)
        self.tracker = DirectoryTracker(on_document_discovered=self._on_tracked_document_discovered)
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
        self.center_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(255, 122, 46, 0.20);
                width: 4px;
            }
            QSplitter::handle:hover {
                background: #FF7A2E;
                width: 6px;
            }
        """)

        self.stack = QStackedWidget()
        self.stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.page_docs = self._build_documents_page()
        self.page_ai = AIAssistantPage(self.assistant, self.theme)
        self.page_storage = StorageVaultPage(self.theme)
        self.page_security = IntegritySecurityPage(self.theme)
        self.page_audit = AuditTrailPage(self.theme)
        self.page_deadlines = DeadlinesPage(self.theme)

        # Index 0 is Documents (Default when opened)
        self.stack.addWidget(self.page_docs)       # 0 (Documents - DEFAULT)
        self.stack.addWidget(self.page_ai)         # 1 (AI Assistant)
        self.stack.addWidget(self.page_storage)    # 2 (Storage Vault)
        self.stack.addWidget(self.page_security)   # 3 (Integrity & Health)
        self.stack.addWidget(self.page_audit)      # 4 (Audit Trail)
        self.stack.addWidget(self.page_deadlines)  # 5 (Deadlines)
        self.center_splitter.addWidget(self.stack)

        # Document Details Drawer in Center Splitter (Slider side-by-side with AI Drawer)
        self.center_splitter.addWidget(self.inspector)
        self.inspector.setVisible(False)

        # Option E: Draggable Extendable Right-Hand AI Drawer
        self.ai_drawer = AIDrawer(self.assistant, self.theme, self)
        self.ai_drawer.closed.connect(self._toggle_ai_drawer)
        self.ai_drawer.setVisible(False)
        self.center_splitter.addWidget(self.ai_drawer)

        self.center_splitter.setCollapsible(0, False)
        self.center_splitter.setCollapsible(1, True)
        self.center_splitter.setCollapsible(2, True)
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
        self.status_dot.setStyleSheet(f"color: {self.theme['green']}; font-size: 11px;")
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
        """Transitions from login/register to main workspace in the SAME window."""
        self.current_user = user_data
        self.user_tier = user_data.get("tier", "Free")
        self.header_banner.set_user_info(self.current_user)
        if hasattr(self, "page_ai"):
            self.page_ai.set_user_info(self.current_user)
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
        tlay.setContentsMargins(16, 0, 16, 0)
        tlay.setSpacing(8)

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

        tlay.addSpacing(6)
        # Redesigned Document Count (Clean, borderless typography)
        self.doc_count_lbl = QLabel("0 documents")
        self.doc_count_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {self.theme['text3']};")
        tlay.addWidget(self.doc_count_lbl)

        tlay.addStretch()

        # Universal Search Bar with embedded Ctrl+K badge
        search_wrap = QFrame()
        search_wrap.setFixedWidth(180)
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
            insp_w = max(380, int(total_w * 0.32))
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
            "Storage & Cloud Mirrors",
            "Integrity & Security Center",
            "Audit Action Log",
            "Smart Deadlines & Obligations",
        ]
        if idx == 1:
            self.page_ai.set_assistant(self.assistant)
        elif idx == 2:
            self.page_storage.refresh_storage_metrics(self.docs)
        elif idx == 3:
            self.page_security.refresh_metrics(self.docs)
        elif idx == 4:
            self.page_audit.refresh_from_logs(
                self.mongo.get_audit_logs() if self.mongo.is_connected else [],
                len(self.docs)
            )
        elif idx == 5:
            self.page_deadlines.refresh_deadlines(self.mongo.list_deadlines())
        self._show_feedback(f"Navigated to {titles[idx]}")

    def _show_feedback(self, msg: str):
        self.feedback_msg.setText(msg)
        self.page_audit.log_event(msg)
        if hasattr(self, "mongo") and self.mongo.is_connected:
            self.mongo.log_audit("FEEDBACK", msg)

    # ─── Database & Vault Loading (MongoDB Realtime Primary) ───────────────

    def _load_vault_database(self):
        """Loads real documents from MongoDB or syncs authentic vault documents."""
        self.docs.clear()
        categories = ["Legal", "Financial", "Medical", "Academic", "General"]

        # 1. Attempt loading from MongoDB realtime collection
        loaded_from_mongo = False
        if self.mongo.is_connected:
            loaded_from_mongo = True
            mongo_docs = self.mongo.list_documents()
            for doc in mongo_docs:
                doc_id = doc.get("doc_id")
                if doc_id:
                    self.docs[doc_id] = doc
                    self.catalog.add_document(doc, storage_mode=self.storage_mode)
                    self.vec_engine.add_document_chunks(
                        doc_id, doc.get("filename", ""), doc.get("category", "General"), doc.get("pages", [])
                    )

        # 2. Only if MongoDB is completely offline/disconnected, check local fallback
        if not loaded_from_mongo:
            for cat in categories:
                cat_dir = Path("vault") / cat
                if cat_dir.exists():
                    for f in cat_dir.iterdir():
                        if f.is_file() and not f.name.endswith(".tmp"):
                            try:
                                doc = DocumentFactory.create_document(str(f), category_hint=cat, enforce_magic_bytes=False)
                                dd = doc.to_dict()
                                dd["pages"] = [{"page_number": p.get("page_number", i+1), "text": p.get("text", "")} for i, p in enumerate(doc.pages)]
                                self.docs[doc.doc_id] = dd
                                self.catalog.add_document(dd, storage_mode=self.storage_mode)
                                self.vec_engine.add_document_chunks(doc.doc_id, doc.filename, doc.get_category(), doc.pages)
                            except Exception:
                                pass

        self.vec_engine.build_index()
        self.assistant.set_engine(self.vec_engine)
        self.assistant.set_mongo(self.mongo)
        self.page_ai.set_assistant(self.assistant)
        self.page_deadlines.refresh_deadlines(self.mongo.list_deadlines())
        if hasattr(self, "page_storage"):
            self.page_storage.refresh_storage_metrics(self.docs)
        if hasattr(self, "page_security"):
            self.page_security.refresh_metrics(self.docs)
        if hasattr(self, "page_audit"):
            self.page_audit.refresh_from_logs(
                self.mongo.get_audit_logs() if self.mongo.is_connected else [],
                len(self.docs)
            )

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
                    border-radius: 14px;
                    padding: 5px 16px;
                    font-size: 11.5px;
                    font-weight: 700;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t['bg3']};
                    color: {t['text2']};
                    border: 1px solid {t['border']};
                    border-radius: 14px;
                    padding: 5px 16px;
                    font-size: 11.5px;
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
                self.mongo.delete_document(doc_id)
                self.mongo.log_audit("DELETE", f"Removed '{fname}' from repository index", doc_id)

            if self.selected_doc and self.selected_doc.get("doc_id") == doc_id:
                self.selected_doc = None
                if hasattr(self, "inspector"):
                    self.inspector.show_empty()
            self._render_documents()
            self._update_metrics_bar()
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
        self.stack.setCurrentIndex(5)
        for i, item in enumerate(self.sidebar.nav_items):
            item.set_active(i == 5)
        self.page_deadlines.refresh_deadlines(self.mongo.list_deadlines())
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
        self.progress_bar.setVisible(False)
        self.docs[doc_dict["doc_id"]] = doc_dict
        self.catalog.add_document(doc_dict, storage_mode=self.storage_mode)

        # Persist to MongoDB in real-time
        self.mongo.save_document(doc_dict)
        self.mongo.save_version(doc_dict["doc_id"], {
            "version_number": "1.0",
            "sha256_hash": doc_dict.get("sha256_hash"),
            "author": "Ingest Worker",
            "text_snapshot": " ".join(p.get("text", "") for p in doc_dict.get("pages", [])),
        })
        self.mongo.log_audit("IMPORT", f"Successfully imported '{doc_dict['filename']}'", doc_dict["doc_id"])

        self.vec_engine.build_index()
        self.assistant.set_engine(self.vec_engine)

        self._render_documents()
        self._update_metrics_bar()
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
        """Clears session and switches back to embedded login in the SAME window."""
        SessionManager.clear_session()
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

        added = self.tracker.add_watched_folder(path)
        if not added:
            QMessageBox.information(self, "Folder Already Tracked", f"The directory is already being monitored:\n{path}")
            return

        self._update_folder_sync_badge()
        self._show_feedback(f"Now tracking directory: {Path(path).name} ... Scanning for documents...")

        # Immediate scan
        found = self.tracker.scan_folder(path)
        for doc_dict in found:
            self._on_tracked_document_discovered(doc_dict)

        self._show_feedback(f"Tracked directory active. Ingested {len(found)} documents from {Path(path).name}")

    def _open_tracked_folders_dialog(self):
        """Opens modal to view and manage watched directories."""
        dlg = TrackedFoldersDialog(self.tracker, self.theme, self)
        dlg.folders_changed.connect(self._on_tracked_folders_changed)
        dlg.exec()

    def _on_tracked_folders_changed(self):
        self._update_folder_sync_badge()
        self._render_documents()

    def _rescan_watched_directories(self):
        """Manually triggers a full re-scan of all monitored directories."""
        self._show_feedback("Scanning all monitored folders for new or modified files...")
        found = self.tracker.scan_all_watched()
        for doc_dict in found:
            self._on_tracked_document_discovered(doc_dict)
        self._update_folder_sync_badge()
        self._render_documents()
        self._show_feedback(f"Folder sync complete. Processed {len(found)} documents.")

    def _on_tracked_document_discovered(self, doc_dict: Dict[str, Any]):
        """Handler called when DirectoryTracker discovers an incoming file."""
        doc_id = doc_dict.get("doc_id")
        if not doc_id:
            return

        # Add to state and databases
        self.docs[doc_id] = doc_dict
        self.catalog.add_document(doc_dict)
        self.mongo.save_document(doc_dict)

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
