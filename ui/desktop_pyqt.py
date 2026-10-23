"""
DocuVault — Production Document Management System (PyQt6)
Enterprise-grade, clean minimalist UI with sliding sidebar, real-time database,
universal search (Ctrl+K), and orange accent themes.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import (
    QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRect, QRectF,
    QSize, Qt, QThread, QTimer, pyqtProperty, pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QDragEnterEvent, QDropEvent, QFont,
    QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap, QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFileDialog, QFrame,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from core.base_document import DocumentFactory
from core.catalog_manager import CatalogManager
from core.exceptions import DocuVaultError
from core.organizer import FileOrganizerDaemon
from core.parsers.binary_parser import BinaryParser
from core.storage_providers import LocalStorageProvider, CloudStorageProvider
from core.vector_search import VectorSearchEngine


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THEME SYSTEM (VIBRANT ORANGE PALETTES)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIGHT = {
    "name": "light",
    "bg": "#F8F9FA",
    "bg2": "#FFFFFF",
    "bg3": "#F1F3F5",
    "bg4": "#E9ECEF",
    "surface": "#FFFFFF",
    "sidebar": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6422, stop:1 #EA580C)",
    "sidebar_solid": "#FF6422",
    "sidebar_text": "#FFFFFF",
    "sidebar_text_muted": "rgba(255, 255, 255, 0.82)",
    "sidebar_item_hover": "rgba(255, 255, 255, 0.16)",
    "sidebar_item_active_bg": "#FFFFFF",
    "sidebar_item_active_text": "#EA580C",
    "sidebar_border": "transparent",
    "hover": "#F8F9FA",
    "active": "#FFF2EC",
    "selected": "#FFF5EE",
    "border": "#E5E7EB",
    "border2": "#D1D5DB",
    "divider": "#F3F4F6",
    "text": "#111827",
    "text2": "#374151",
    "text3": "#6B7280",
    "text4": "#9CA3AF",
    "primary": "#FF6422",
    "primary_h": "#EA580C",
    "primary_p": "#C2410C",
    "primary_bg": "#FFF4ED",
    "primary_border": "#FDBA74",
    "green": "#10B981",
    "green_bg": "#ECFDF5",
    "green_border": "#A7F3D0",
    "red": "#EF4444",
    "red_bg": "#FEF2F2",
    "red_border": "#FECACA",
    "blue": "#0284C7",
    "blue_bg": "#F0F9FF",
    "orange": "#FF6422",
    "shadow": "rgba(0, 0, 0, 0.04)",
    "shadow_card": "0 2px 8px rgba(0,0,0,0.04)",
}

DARK = {
    "name": "dark",
    "bg": "#0B0C0E",
    "bg2": "#14151B",
    "bg3": "#1B1D25",
    "bg4": "#282B36",
    "surface": "#14151B",
    "sidebar": "#0E0F14",
    "sidebar_solid": "#0E0F14",
    "sidebar_text": "#F3F4F6",
    "sidebar_text_muted": "#9CA3AF",
    "sidebar_item_hover": "rgba(255, 107, 43, 0.12)",
    "sidebar_item_active_bg": "rgba(255, 107, 43, 0.20)",
    "sidebar_item_active_text": "#FF7A3D",
    "sidebar_border": "#20222B",
    "hover": "#1D1F28",
    "active": "rgba(255, 107, 43, 0.15)",
    "selected": "rgba(255, 107, 43, 0.18)",
    "border": "#222530",
    "border2": "#313545",
    "divider": "#1C1E26",
    "text": "#F9FAFB",
    "text2": "#D1D5DB",
    "text3": "#9CA3AF",
    "text4": "#6B7280",
    "primary": "#FF7A3D",
    "primary_h": "#FF8F57",
    "primary_p": "#EA580C",
    "primary_bg": "rgba(255, 122, 61, 0.14)",
    "primary_border": "rgba(255, 122, 61, 0.35)",
    "green": "#34D399",
    "green_bg": "rgba(52, 211, 153, 0.14)",
    "green_border": "rgba(52, 211, 153, 0.30)",
    "red": "#F87171",
    "red_bg": "rgba(248, 113, 113, 0.14)",
    "red_border": "rgba(248, 113, 113, 0.30)",
    "blue": "#38BDF8",
    "blue_bg": "rgba(56, 189, 248, 0.14)",
    "orange": "#FF7A3D",
    "shadow": "rgba(0, 0, 0, 0.35)",
    "shadow_card": "0 2px 10px rgba(0,0,0,0.30)",
}


def qss(t: Dict[str, str]) -> str:
    return f"""
        * {{ margin: 0; padding: 0; outline: none; }}
        QMainWindow {{ background: {t['bg']}; }}
        QWidget {{
            color: {t['text']};
            font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
            font-size: 13px;
        }}

        /* ─── Cards & Containers ─── */
        QFrame#unifiedCard {{
            background: {t['surface']};
            border: 1px solid {t['border']};
            border-radius: 14px;
        }}
        QFrame#subCard {{
            background: {t['bg3']};
            border: 1px solid {t['border']};
            border-radius: 10px;
        }}

        /* ─── Buttons ─── */
        QPushButton {{
            font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
            cursor: pointer;
        }}
        QPushButton#primaryBtn {{
            background: {t['primary']};
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 12px;
        }}
        QPushButton#primaryBtn:hover {{ background: {t['primary_h']}; }}
        QPushButton#primaryBtn:pressed {{ background: {t['primary_p']}; }}

        QPushButton#secondaryBtn {{
            background: {t['bg2']};
            color: {t['text2']};
            border: 1px solid {t['border2']};
            border-radius: 8px;
            padding: 7px 14px;
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
            border-radius: 8px;
            padding: 8px 14px;
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
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton#copyBtn:hover {{
            background: {t['primary_bg']};
            color: {t['primary']};
            border-color: {t['primary_border']};
        }}

        /* Segmented Filter Pills */
        QPushButton#filterPill {{
            background: transparent;
            color: {t['text3']};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton#filterPill:hover {{
            background: {t['bg3']};
            color: {t['text']};
        }}
        QPushButton#filterPill[active="true"] {{
            background: {t['primary_bg']};
            color: {t['primary']};
            font-weight: 700;
            border: 1px solid {t['primary_border']};
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
    pen = QPen(c, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    if name == "logo":
        # Vault Shield emblem
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor("#FF7A3D"))
        grad.setColorAt(1, QColor("#EA580C"))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), size * 0.25, size * 0.25)

        # Shield outline inside
        p.setPen(QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        spath = QPainterPath()
        spath.moveTo(size * 0.25, size * 0.30)
        spath.lineTo(size * 0.50, size * 0.22)
        spath.lineTo(size * 0.75, size * 0.30)
        spath.lineTo(size * 0.75, size * 0.52)
        spath.quadTo(QPointF(size * 0.75, size * 0.72), QPointF(size * 0.50, size * 0.80))
        spath.quadTo(QPointF(size * 0.25, size * 0.72), QPointF(size * 0.25, size * 0.52))
        spath.closeSubpath()
        p.drawPath(spath)

        # Center lock circle
        p.drawEllipse(QRectF(size * 0.40, size * 0.42, size * 0.20, size * 0.20))
        p.drawLine(QPointF(size * 0.50, size * 0.35), QPointF(size * 0.50, size * 0.40))
        p.drawLine(QPointF(size * 0.50, size * 0.65), QPointF(size * 0.50, size * 0.70))

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
        p.drawEllipse(QRectF(size * 0.32, size * 0.32, size * 0.36, size * 0.36))
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
        p.drawPath(mpath)

    p.end()
    return pm


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
            icon_color = t['sidebar_item_active_text'] if t['name'] == 'light' else t['primary']
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
            self.text_lbl.setStyleSheet(f"color: {t['sidebar_text_muted']}; font-size: 13px; font-weight: 500;")
            icon_color = "#FFFFFF" if t['name'] == 'light' else t['sidebar_text_muted']
            self.icon_lbl.setPixmap(draw_vector_icon(self.icon_name, icon_color, 22))


class SlidingSidebar(QFrame):
    """
    Production sliding sidebar with smooth QPropertyAnimation on hover.
    Expands smoothly from 68px to 230px when the user hovers over it.
    """
    page_selected = pyqtSignal(int)
    theme_toggled = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self._sidebar_width = 68
        self.setFixedWidth(68)
        self.setObjectName("slidingSidebar")

        # Smooth hover animation
        self.anim = QPropertyAnimation(self, b"sidebarWidth")
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 18, 10, 18)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Brand logo
        self.logo = BrandLogo(theme, self)
        lay.addWidget(self.logo)
        lay.addSpacing(18)

        # Navigation items
        self.nav_items: List[SidebarNavItem] = []
        nav_configs = [
            ("documents", "Documents", 0),
            ("storage", "Storage Vault", 1),
            ("security", "Integrity & Health", 2),
            ("activity", "Audit Trail", 3),
        ]
        for icon, title, idx in nav_configs:
            item = SidebarNavItem(icon, title, theme, self)
            item.clicked.connect(lambda _, i=idx: self._on_select(i))
            lay.addWidget(item)
            self.nav_items.append(item)

        self.nav_items[0].set_active(True)

        lay.addStretch()

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

    def enterEvent(self, e):
        super().enterEvent(e)
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(230)
        self.anim.start()

    def leaveEvent(self, e):
        super().leaveEvent(e)
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
    """Clean metric indicator inside the unified header bar."""

    def __init__(self, title: str, value: str, subtext: str, color_hex: str, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(2)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {theme['text4']}; letter-spacing: 0.8px;")
        lay.addWidget(self.title_lbl)

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color_hex};")
        lay.addWidget(self.val_lbl)

        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setStyleSheet(f"font-size: 11px; color: {theme['text3']};")
        lay.addWidget(self.sub_lbl)

    def set_value(self, val: str, subtext: Optional[str] = None):
        self.val_lbl.setText(val)
        if subtext:
            self.sub_lbl.setText(subtext)

    def update_theme(self, theme: Dict[str, str], color_hex: str):
        self._t = theme
        self.title_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {theme['text4']}; letter-spacing: 0.8px;")
        self.val_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color_hex};")
        self.sub_lbl.setStyleSheet(f"font-size: 11px; color: {theme['text3']};")


class UnifiedHeaderBanner(QFrame):
    """
    Consolidated executive header:
    Combines Repository Metrics and Quick Import Drop Zone into ONE clean, non-cluttered card.
    """
    files_dropped = pyqtSignal(list)
    browse_clicked = pyqtSignal()

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setObjectName("unifiedCard")
        self.setFixedHeight(102)
        self.setAcceptDrops(True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 12, 20, 12)
        lay.setSpacing(16)

        # ── Left: Key Metrics Bar ──
        metrics_box = QHBoxLayout()
        metrics_box.setSpacing(8)

        self.m_total = MetricPill("Documents", "0", "Indexed Files", theme["primary"], theme)
        self.m_size = MetricPill("Vault Storage", "0 B", "Allocated on Disk", theme["blue"], theme)
        self.m_status = MetricPill("Integrity", "100%", "Verified Authentic", theme["green"], theme)
        self.m_cats = MetricPill("Categories", "0", "Organized Folders", theme["orange"], theme)

        metrics_box.addWidget(self.m_total)
        self.div1 = self._make_divider()
        metrics_box.addWidget(self.div1)
        metrics_box.addWidget(self.m_size)
        self.div2 = self._make_divider()
        metrics_box.addWidget(self.div2)
        metrics_box.addWidget(self.m_status)
        self.div3 = self._make_divider()
        metrics_box.addWidget(self.div3)
        metrics_box.addWidget(self.m_cats)

        lay.addLayout(metrics_box, stretch=3)

        # ── Right: Integrated Quick Drop & Upload Capsule ──
        self.drop_capsule = QFrame()
        self.drop_capsule.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.drop_capsule.setFixedHeight(76)
        self.drop_capsule.setMinimumWidth(350)
        dlay = QHBoxLayout(self.drop_capsule)
        dlay.setContentsMargins(16, 8, 16, 8)
        dlay.setSpacing(12)

        self.up_icon = QLabel()
        self.up_icon.setFixedSize(28, 28)
        dlay.addWidget(self.up_icon)

        tbox = QVBoxLayout()
        tbox.setSpacing(2)
        tbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.dtitle = QLabel("Drop documents here to import")
        self.dtitle.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {theme['text']};")
        self.dsub = QLabel("PDF, XML, TXT \u2022 Instant Verification")
        self.dsub.setStyleSheet(f"font-size: 11px; color: {theme['text3']};")
        tbox.addWidget(self.dtitle)
        tbox.addWidget(self.dsub)
        dlay.addLayout(tbox)

        self.btn_import = QPushButton("+ Import Files")
        self.btn_import.setObjectName("primaryBtn")
        self.btn_import.setFixedHeight(34)
        self.btn_import.clicked.connect(self.browse_clicked.emit)
        dlay.addWidget(self.btn_import)

        lay.addWidget(self.drop_capsule, stretch=2)

        self.update_theme(theme)

    def _make_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFixedHeight(44)
        div.setStyleSheet(f"color: {self._t['divider']};")
        return div

    def update_metrics(self, total: int, size_str: str, verified_pct: str, cats: int):
        self.m_total.set_value(str(total), f"{total} Documents" if total != 1 else "1 Document")
        self.m_size.set_value(size_str, "Allocated on Disk")
        self.m_status.set_value(verified_pct, "Verified Authentic")
        self.m_cats.set_value(str(cats), f"{cats} Active Types")

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.setStyleSheet(f"""
            #unifiedCard {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 14px;
            }}
        """)
        self.drop_capsule.setStyleSheet(f"""
            QFrame {{
                background: {theme['bg3']};
                border: 1.5px dashed {theme['border2']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {theme['primary']};
                background: {theme['primary_bg']};
            }}
        """)
        self.up_icon.setPixmap(draw_vector_icon("upload", theme["primary"], 28))
        self.dtitle.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {theme['text']};")
        self.dsub.setStyleSheet(f"font-size: 11px; color: {theme['text3']};")
        self.m_total.update_theme(theme, theme["primary"])
        self.m_size.update_theme(theme, theme["blue"])
        self.m_status.update_theme(theme, theme["green"])
        self.m_cats.update_theme(theme, theme["orange"])
        for div in (self.div1, self.div2, self.div3):
            div.setStyleSheet(f"color: {theme['divider']};")

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.drop_capsule.setStyleSheet(f"""
                QFrame {{
                    background: {self._t['primary_bg']};
                    border: 2px dashed {self._t['primary']};
                    border-radius: 10px;
                }}
            """)

    def dragLeaveEvent(self, e):
        self.update_theme(self._t)

    def dropEvent(self, e: QDropEvent):
        self.update_theme(self._t)
        paths = [u.toLocalFile() for u in e.mimeData().urls() if os.path.isfile(u.toLocalFile())]
        if paths:
            self.files_dropped.emit(paths)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.drop_capsule.geometry().contains(e.pos()):
            self.browse_clicked.emit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOCUMENT ROW ITEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentListItem(QFrame):
    """Modern document list entry with rich feedback and clear status."""
    clicked = pyqtSignal(dict)

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
        self.setFixedHeight(62)
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
    Refined details panel:
    All clickable elements are proper styled buttons.
    Labels are user-friendly without programming jargon.
    """
    view_text_clicked = pyqtSignal()
    verify_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    copy_hash_clicked = pyqtSignal(str)

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        self.setObjectName("inspectorPanel")
        self.setMinimumWidth(340)
        self.setMaximumWidth(420)
        self._current_hash = ""
        self._build()

    def _build(self):
        t = self._t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        # Header tag
        tag_row = QHBoxLayout()
        tag = QLabel("DOCUMENT DETAILS")
        tag.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 1px;")
        tag_row.addWidget(tag)
        tag_row.addStretch()

        self.status_badge = QLabel("")
        tag_row.addWidget(self.status_badge)
        lay.addLayout(tag_row)

        # Document name
        self.title_lbl = QLabel("Select a document")
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {t['text']};")
        self.title_lbl.setWordWrap(True)
        lay.addWidget(self.title_lbl)

        # Divider
        self.div = QFrame()
        self.div.setFixedHeight(1)
        self.div.setStyleSheet(f"background: {t['divider']};")
        lay.addWidget(self.div)

        # Information Cards
        self.info_box = QFrame()
        self.info_box.setObjectName("subCard")
        ilay = QGridLayout(self.info_box)
        ilay.setContentsMargins(14, 12, 14, 12)
        ilay.setSpacing(10)

        ilay.addWidget(self._make_label("FILE SIZE"), 0, 0)
        self.lbl_size = QLabel("—")
        self.lbl_size.setStyleSheet(f"font-weight: 600; color: {t['text']};")
        ilay.addWidget(self.lbl_size, 0, 1)

        ilay.addWidget(self._make_label("PAGE COUNT"), 1, 0)
        self.lbl_pages = QLabel("—")
        self.lbl_pages.setStyleSheet(f"font-weight: 600; color: {t['text']};")
        ilay.addWidget(self.lbl_pages, 1, 1)

        ilay.addWidget(self._make_label("STORAGE TYPE"), 2, 0)
        self.lbl_storage = QLabel("Local Vault")
        self.lbl_storage.setStyleSheet(f"font-weight: 600; color: {t['text']};")
        ilay.addWidget(self.lbl_storage, 2, 1)

        lay.addWidget(self.info_box)

        # Digital Signature / Security Fingerprint (With Copy Button!)
        sig_sec = QLabel("SECURITY FINGERPRINT")
        sig_sec.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.8px;")
        lay.addWidget(sig_sec)

        self.sig_box = QFrame()
        self.sig_box.setObjectName("subCard")
        slay = QHBoxLayout(self.sig_box)
        slay.setContentsMargins(12, 8, 12, 8)
        slay.setSpacing(8)

        self.lbl_hash = QLabel("No document selected")
        self.lbl_hash.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {t['primary']};")
        self.lbl_hash.setWordWrap(True)
        slay.addWidget(self.lbl_hash, 1)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setObjectName("copyBtn")
        self.btn_copy.clicked.connect(self._copy_hash)
        slay.addWidget(self.btn_copy)
        lay.addWidget(self.sig_box)

        # Key Information Extracted (User-friendly section)
        ent_sec = QLabel("DOCUMENT INSIGHTS")
        ent_sec.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['text4']}; letter-spacing: 0.8px;")
        lay.addWidget(ent_sec)

        self.insights_box = QTextEdit()
        self.insights_box.setReadOnly(True)
        self.insights_box.setFixedHeight(120)
        self.insights_box.setStyleSheet(f"background: {t['bg3']}; border: 1px solid {t['border']}; border-radius: 8px; font-size: 11px; color: {t['text2']};")
        lay.addWidget(self.insights_box)

        lay.addStretch()

        # Action Buttons (All enclosed in proper styled buttons!)
        self.btn_view = QPushButton("View Document Content")
        self.btn_view.setObjectName("primaryBtn")
        self.btn_view.setFixedHeight(38)
        self.btn_view.clicked.connect(self.view_text_clicked.emit)
        lay.addWidget(self.btn_view)

        self.btn_verify = QPushButton("Verify Digital Signature")
        self.btn_verify.setObjectName("secondaryBtn")
        self.btn_verify.setFixedHeight(36)
        self.btn_verify.clicked.connect(self.verify_clicked.emit)
        lay.addWidget(self.btn_verify)

        # Danger button (Properly styled button, NOT clickable text)
        self.btn_delete = QPushButton("Remove from Repository")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setFixedHeight(36)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        lay.addWidget(self.btn_delete)

        self.show_empty()

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
        self.title_lbl.setText("Select a document")
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {t['text']};")
        self.status_badge.setText("")
        self.lbl_size.setText("—")
        self.lbl_pages.setText("—")
        self.lbl_storage.setText("Local Vault")
        self.lbl_hash.setText("Select a document to inspect cryptographic integrity")
        self._current_hash = ""
        self.insights_box.setPlainText("Select a file from the repository to view extracted clauses, key entities, and security details.")
        self.btn_view.setEnabled(False)
        self.btn_verify.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.btn_copy.setEnabled(False)

    def show_doc(self, doc: Dict[str, Any], storage_name: str = "Local Vault"):
        t = self._t
        self.title_lbl.setText(doc.get("filename", "Untitled Document"))
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {t['text']};")

        status = doc.get("status", "Verified")
        is_ok = status == "Verified"
        scol = t["green"] if is_ok else t["red"]
        sbg = t["green_bg"] if is_ok else t["red_bg"]
        self.status_badge.setText(f"\u25CF {'Verified' if is_ok else 'Tampered'}")
        self.status_badge.setStyleSheet(f"""
            font-size: 10px; font-weight: 700; color: {scol};
            background: {sbg}; padding: 3px 8px; border-radius: 6px;
        """)

        sz_b = doc.get("size_bytes", 0)
        sz_str = f"{sz_b / (1024*1024):.1f} MB" if sz_b >= 1048576 else (f"{sz_b / 1024:.1f} KB" if sz_b >= 1024 else f"{sz_b} B")
        self.lbl_size.setText(sz_str)
        self.lbl_size.setStyleSheet(f"font-weight: 600; color: {t['text']};")
        self.lbl_pages.setText(f"{doc.get('page_count', 1)} pages")
        self.lbl_pages.setStyleSheet(f"font-weight: 600; color: {t['text']};")
        self.lbl_storage.setText(storage_name)
        self.lbl_storage.setStyleSheet(f"font-weight: 600; color: {t['text']};")

        sha = doc.get("sha256_hash", "N/A")
        self._current_hash = sha
        self.lbl_hash.setText(sha)
        self.lbl_hash.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {t['primary']};")
        self.btn_copy.setEnabled(bool(sha and sha != "N/A"))

        # Insights & extracted entities
        clauses = doc.get("clauses", {})
        currency = doc.get("currency_amounts", [])
        dates = doc.get("extracted_dates", [])

        lines = []
        if dates:
            lines.append(f"Recorded Dates: {', '.join(dates[:3])}")
        if currency:
            lines.append(f"Financial Values: {', '.join(currency[:3])}")
        if clauses:
            for k, v in list(clauses.items())[:5]:
                clean_v = str(v).strip()
                if len(clean_v) > 80:
                    clean_v = clean_v[:80] + "..."
                lines.append(f"{k}: {clean_v}")

        if lines:
            self.insights_box.setPlainText("\n\n".join(lines))
        else:
            self.insights_box.setPlainText("No structured clauses extracted. Standard document text available in viewer.")
        self.insights_box.setStyleSheet(f"background: {t['bg3']}; border: 1px solid {t['border']}; border-radius: 8px; font-size: 11px; color: {t['text2']};")

        self.btn_view.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.setStyleSheet(f"""
            #inspectorPanel {{
                background: {theme['surface']};
                border-left: 1px solid {theme['border']};
            }}
        """)
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {theme['text']};")
        self.lbl_size.setStyleSheet(f"font-weight: 600; color: {theme['text']};")
        self.lbl_pages.setStyleSheet(f"font-weight: 600; color: {theme['text']};")
        self.lbl_storage.setStyleSheet(f"font-weight: 600; color: {theme['text']};")
        self.div.setStyleSheet(f"background: {theme['divider']};")
        self.info_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 10px;")
        self.sig_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 10px;")
        self.lbl_hash.setStyleSheet(f"font-family: monospace; font-size: 10px; color: {theme['primary']};")
        self.insights_box.setStyleSheet(f"background: {theme['bg3']}; border: 1px solid {theme['border']}; border-radius: 8px; font-size: 11px; color: {theme['text2']};")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FULL-TEXT DOCUMENT VIEWER DIALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentViewerDialog(QDialog):
    """Clean reader modal with high legibility and search capability."""

    def __init__(self, doc: Dict[str, Any], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        t = theme
        self.setWindowTitle(f"Document Viewer — {doc.get('filename', 'Document')}")
        self.resize(840, 620)
        self.setStyleSheet(f"background: {t['bg']}; color: {t['text']};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        # Header
        hlay = QHBoxLayout()
        title = QLabel(doc.get("filename", "Untitled Document"))
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {t['text']};")
        hlay.addWidget(title)
        hlay.addStretch()

        status = doc.get("status", "Verified")
        is_ok = status == "Verified"
        st = QLabel(f"\u25CF {'Verified Authentic' if is_ok else 'Integrity Alert'}")
        st.setStyleSheet(f"color: {t['green'] if is_ok else t['red']}; font-weight: 600; font-size: 12px;")
        hlay.addWidget(st)
        lay.addLayout(hlay)

        sub = QLabel(f"Category: {doc.get('category', 'General')}  \u2022  {doc.get('page_count', 1)} pages  \u2022  Size: {doc.get('size_bytes', 0)} bytes")
        sub.setStyleSheet(f"font-size: 11px; color: {t['text4']};")
        lay.addWidget(sub)

        # Content area
        txt = QTextEdit()
        txt.setReadOnly(True)
        pages = doc.get("pages", [])
        if pages:
            body = "\n\n".join(
                f"── Page {p.get('page_number', i+1)} ──\n{p.get('text', '')}"
                for i, p in enumerate(pages)
            )
        else:
            body = doc.get("raw_text", "No readable text content extracted.")
        txt.setPlainText(body)
        lay.addWidget(txt)

        # Bottom close button
        blow = QHBoxLayout()
        blow.addStretch()
        cb = QPushButton("Close")
        cb.setObjectName("secondaryBtn")
        cb.setFixedWidth(100)
        cb.clicked.connect(self.close)
        blow.addWidget(cb)
        lay.addLayout(blow)


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
    """Dedicated Storage & Cloud mirror page."""

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        # Header
        self.t_lbl = QLabel("Storage & Cloud Vault")
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        lay.addWidget(self.t_lbl)

        self.sub = QLabel("Manage physical storage locations, cloud backups, and disk allocation.")
        self.sub.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        lay.addWidget(self.sub)

        # Unified Card
        self.card = QFrame()
        self.card.setObjectName("unifiedCard")
        clay = QVBoxLayout(self.card)
        clay.setContentsMargins(24, 20, 24, 20)
        clay.setSpacing(14)

        self.sec_title = QLabel("STORAGE REPOSITORIES")
        self.sec_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme['text4']};")
        clay.addWidget(self.sec_title)

        self.path_local = QLabel(f"Local Storage Path: {os.path.abspath('vault/local')}")
        self.path_local.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")
        clay.addWidget(self.path_local)

        self.path_cloud = QLabel(f"Cloud Mirror Path: {os.path.abspath('vault/cloud_mirror')}")
        self.path_cloud.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")
        clay.addWidget(self.path_cloud)

        self.div = QFrame()
        self.div.setFixedHeight(1)
        self.div.setStyleSheet(f"background: {theme['divider']};")
        clay.addWidget(self.div)

        self.stats_lbl = QLabel("Active Sync: Real-time File Watching \u2022 Hybrid Storage Mode Active")
        self.stats_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {theme['green']};")
        clay.addWidget(self.stats_lbl)

        lay.addWidget(self.card)
        lay.addStretch()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        self.sub.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        self.card.setStyleSheet(f"""
            #unifiedCard {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 14px;
            }}
        """)
        self.sec_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme['text4']};")
        self.path_local.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")
        self.path_cloud.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")
        self.div.setStyleSheet(f"background: {theme['divider']};")
        self.stats_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {theme['green']};")


class IntegritySecurityPage(QWidget):
    """Dedicated Security & Tamper Detection Page."""

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        self.t_lbl = QLabel("Integrity & Security Center")
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        lay.addWidget(self.t_lbl)

        self.sub = QLabel("Cryptographic SHA-256 integrity audits and quarantined document monitor.")
        self.sub.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        lay.addWidget(self.sub)

        self.card = QFrame()
        self.card.setObjectName("unifiedCard")
        clay = QVBoxLayout(self.card)
        clay.setContentsMargins(24, 20, 24, 20)
        clay.setSpacing(14)

        self.sec_title = QLabel("SECURITY STATUS")
        self.sec_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme['text4']};")
        clay.addWidget(self.sec_title)

        self.status_lbl = QLabel("System Protection: Active \u2022 Magic Byte Validation Enabled")
        self.status_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {theme['green']};")
        clay.addWidget(self.status_lbl)

        self.quarantine_lbl = QLabel(f"Quarantine Folder: {os.path.abspath('vault/quarantine')}")
        self.quarantine_lbl.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")
        clay.addWidget(self.quarantine_lbl)

        lay.addWidget(self.card)
        lay.addStretch()

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        self.sub.setStyleSheet(f"font-size: 12px; color: {theme['text4']};")
        self.card.setStyleSheet(f"""
            #unifiedCard {{
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 14px;
            }}
        """)
        self.sec_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {theme['text4']};")
        self.status_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {theme['green']};")
        self.quarantine_lbl.setStyleSheet(f"font-family: monospace; font-size: 12px; color: {theme['text2']};")


class AuditTrailPage(QWidget):
    """Chronological activity trail of vault actions."""

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self._t = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        self.t_lbl = QLabel("Audit Trail & Action Log")
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        lay.addWidget(self.t_lbl)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(f"background: {theme['surface']}; border: 1px solid {theme['border']}; border-radius: 12px; font-family: monospace; font-size: 12px; color: {theme['text2']};")
        lay.addWidget(self.log_view)

    def log_event(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_view.append(f"[{ts}] {msg}")

    def update_theme(self, theme: Dict[str, str]):
        self._t = theme
        self.t_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']};")
        self.log_view.setStyleSheet(f"background: {theme['surface']}; border: 1px solid {theme['border']}; border-radius: 12px; font-family: monospace; font-size: 12px; color: {theme['text2']};")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRIMARY MAIN WINDOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocuVault(QMainWindow):
    """
    DocuVault Master Application Window:
    - Sliding sidebar on hover
    - Orange brand styling (Light & Dark)
    - Unified workspace card layout
    - Universal Search (Ctrl+K)
    - Real-time database & document operations
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocuVault — Enterprise Document Management")
        self.resize(1380, 880)
        self.setMinimumSize(1080, 680)

        # Core Backend Engines
        self.storage_mode = "Local Vault"
        self.local_prov = LocalStorageProvider(root_dir="vault/local")
        self.cloud_prov = CloudStorageProvider(mirror_dir="vault/cloud_mirror")
        self.catalog = CatalogManager()
        self.vec_engine = VectorSearchEngine()
        self.organizer = FileOrganizerDaemon(vault_root="vault")

        # Application State
        self.docs: Dict[str, Dict[str, Any]] = {}
        self.selected_doc: Optional[Dict[str, Any]] = None
        self.current_filter_cat = "All"
        self.current_search_query = ""
        self._workers: List[QThread] = []
        self._import_queue: List[str] = []

        # Active Theme
        self.theme = LIGHT
        self._apply_theme()
        self._build_ui()
        self._setup_shortcuts()
        self._load_vault_database()

    def _apply_theme(self):
        self.setStyleSheet(qss(self.theme))

    def _toggle_theme(self):
        self.theme = DARK if self.theme["name"] == "light" else LIGHT
        self._apply_theme()
        self.sidebar.update_theme(self.theme)
        self.header_banner.update_theme(self.theme)
        self.inspector.update_theme(self.theme)
        self.page_storage.update_theme(self.theme)
        self.page_security.update_theme(self.theme)
        self.page_audit.update_theme(self.theme)

        # Update feedback bar
        self.feedback_bar.setStyleSheet(f"""
            background: {self.theme['surface']};
            border-top: 1px solid {self.theme['border']};
        """)
        self.feedback_msg.setStyleSheet(f"font-size: 11px; color: {self.theme['text3']};")
        self.shortcut_hint.setStyleSheet(f"font-size: 11px; color: {self.theme['text4']};")

        # Update search bar badge
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
        if hasattr(self, "scroll"):
            self.scroll.setStyleSheet(f"border: none; background: {self.theme['surface']};")
            self.list_container.setStyleSheet(f"background: {self.theme['surface']};")
        if hasattr(self, "workspace_card"):
            self.workspace_card.setStyleSheet(f"""
                #unifiedCard {{
                    background: {self.theme['surface']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, "doc_count_pill"):
            self.doc_count_pill.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {self.theme['text4']};
                background: {self.theme['bg3']};
                padding: 3px 10px;
                border-radius: 6px;
            """)

        self._render_documents()
        if self.selected_doc:
            self.inspector.show_doc(self.selected_doc, self.storage_mode)
        self._show_feedback(f"Switched to {self.theme['name'].capitalize()} Mode")

    def _setup_shortcuts(self):
        # Universal Search Shortcut: Ctrl+K
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self._focus_search)

        # Clear Search Shortcut: Esc
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._clear_search)

    def _focus_search(self):
        self.stack.setCurrentIndex(0)
        self.sidebar.nav_items[0].set_active(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
        self._show_feedback("Universal Search activated (Ctrl+K)")

    def _clear_search(self):
        if self.search_input.hasFocus() or self.search_input.text():
            self.search_input.clear()
            self._show_feedback("Search cleared")

    # ─── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_lay = QHBoxLayout(central)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── 1. Sliding Sidebar (Expands on hover) ──
        self.sidebar = SlidingSidebar(self.theme, self)
        self.sidebar.page_selected.connect(self._on_page_selected)
        self.sidebar.theme_toggled.connect(self._toggle_theme)
        root_lay.addWidget(self.sidebar)

        # ── 2. Main Content Stack ──
        main_content = QWidget()
        mlay = QVBoxLayout(main_content)
        mlay.setContentsMargins(0, 0, 0, 0)
        mlay.setSpacing(0)

        # Top progress bar for background operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        mlay.addWidget(self.progress_bar)

        self.stack = QStackedWidget()
        self.page_docs = self._build_documents_page()
        self.page_storage = StorageVaultPage(self.theme)
        self.page_security = IntegritySecurityPage(self.theme)
        self.page_audit = AuditTrailPage(self.theme)

        self.stack.addWidget(self.page_docs)       # 0
        self.stack.addWidget(self.page_storage)    # 1
        self.stack.addWidget(self.page_security)   # 2
        self.stack.addWidget(self.page_audit)      # 3
        mlay.addWidget(self.stack, 1)

        # ── 3. Bottom Toast / Feedback Bar ──
        self.feedback_bar = QFrame()
        self.feedback_bar.setFixedHeight(32)
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

        self.feedback_msg = QLabel("Ready \u2022 Press Ctrl+K to search")
        self.feedback_msg.setStyleSheet(f"font-size: 11px; color: {self.theme['text3']};")
        flay.addWidget(self.feedback_msg)

        flay.addStretch()

        self.shortcut_hint = QLabel("Search: Ctrl+K  \u2022  Clear: Esc")
        self.shortcut_hint.setStyleSheet(f"font-size: 11px; color: {self.theme['text4']};")
        flay.addWidget(self.shortcut_hint)

        mlay.addWidget(self.feedback_bar)
        root_lay.addWidget(main_content, 1)

    def _build_documents_page(self) -> QWidget:
        """
        Builds the unified single-card workspace for Documents.
        Zero cluttered floating divs — organized into two cohesive surfaces.
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # ── Surface 1: Unified Header Banner (Metrics + Drop Capsule) ──
        self.header_banner = UnifiedHeaderBanner(self.theme, self)
        self.header_banner.files_dropped.connect(self._import_files)
        self.header_banner.browse_clicked.connect(self._open_file_dialog)
        lay.addWidget(self.header_banner)

        # ── Surface 2: Master Document Workspace Card ──
        self.workspace_card = QFrame()
        self.workspace_card.setObjectName("unifiedCard")
        wlay = QVBoxLayout(self.workspace_card)
        wlay.setContentsMargins(0, 0, 0, 0)
        wlay.setSpacing(0)

        # Toolbar inside the card
        toolbar = QFrame()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(f"border-bottom: 1px solid {self.theme['border']};")
        tlay = QHBoxLayout(toolbar)
        tlay.setContentsMargins(18, 0, 18, 0)
        tlay.setSpacing(10)

        # Category Filter Pills
        self.filter_buttons: Dict[str, QPushButton] = {}
        for cat in ["All", "Legal", "Financial", "Medical", "Academic", "General"]:
            btn = QPushButton(cat)
            btn.setObjectName("filterPill")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setProperty("active", cat == "All")
            btn.clicked.connect(lambda _, c=cat: self._set_category_filter(c))
            tlay.addWidget(btn)
            self.filter_buttons[cat] = btn

        tlay.addSpacing(10)
        self.doc_count_pill = QLabel("0 documents")
        self.doc_count_pill.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {self.theme['text4']};
            background: {self.theme['bg3']};
            padding: 3px 10px;
            border-radius: 6px;
        """)
        tlay.addWidget(self.doc_count_pill)

        tlay.addStretch()

        # Universal Search Bar with Ctrl+K badge
        search_wrap = QFrame()
        search_wrap.setFixedWidth(310)
        swlay = QHBoxLayout(search_wrap)
        swlay.setContentsMargins(0, 0, 0, 0)
        swlay.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents, content, or clauses...")
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
            padding: 2px 6px;
        """)
        self.kbadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Place badge inside input
        badge_holder = QHBoxLayout(self.search_input)
        badge_holder.setContentsMargins(0, 0, 8, 0)
        badge_holder.addStretch()
        badge_holder.addWidget(self.kbadge)

        tlay.addWidget(search_wrap)

        # Action Buttons
        btn_verify_all = QPushButton("Verify All")
        btn_verify_all.setObjectName("secondaryBtn")
        btn_verify_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_verify_all.clicked.connect(self._verify_all_documents)
        tlay.addWidget(btn_verify_all)

        btn_sort = QPushButton("Auto-Organize")
        btn_sort.setObjectName("secondaryBtn")
        btn_sort.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_sort.clicked.connect(self._run_auto_organize)
        tlay.addWidget(btn_sort)

        wlay.addWidget(toolbar)

        # Splitter: Document List (Left) + Document Inspector (Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; width: 1px; }")

        # Document List Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"border: none; background: {self.theme['surface']};")

        self.list_container = QWidget()
        self.list_lay = QVBoxLayout(self.list_container)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(0)
        self.list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_container)
        splitter.addWidget(self.scroll)

        # Document Inspector Panel
        self.inspector = DocumentInspector(self.theme, self)
        self.inspector.view_text_clicked.connect(self._view_selected_document_text)
        self.inspector.verify_clicked.connect(self._verify_selected_document)
        self.inspector.delete_clicked.connect(self._delete_selected_document)
        self.inspector.copy_hash_clicked.connect(lambda h: self._show_feedback("Security fingerprint copied to clipboard"))
        splitter.addWidget(self.inspector)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        wlay.addWidget(splitter, 1)
        lay.addWidget(self.workspace_card, 1)

        return page

    # ─── Navigation & Feedback ────────────────────────────────────────────

    def _on_page_selected(self, idx: int):
        self.stack.setCurrentIndex(idx)
        titles = ["Documents Workspace", "Storage & Cloud Mirrors", "Integrity & Security Center", "Audit Action Log"]
        self._show_feedback(f"Navigated to {titles[idx]}")

    def _show_feedback(self, msg: str):
        self.feedback_msg.setText(msg)
        self.page_audit.log_event(msg)

    # ─── Database & Vault Loading ─────────────────────────────────────────

    def _load_vault_database(self):
        """Loads real documents from vault filesystem into memory catalog and search index."""
        self.docs.clear()
        categories = ["Legal", "Financial", "Medical", "Academic", "General"]

        for cat in categories:
            cat_dir = Path("vault") / cat
            if cat_dir.exists():
                for f in cat_dir.iterdir():
                    if f.is_file():
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
        self._render_documents()
        self._update_metrics_bar()

        if self.docs:
            first_doc = next(iter(self.docs.values()))
            self._select_document(first_doc)

        self._show_feedback(f"Loaded {len(self.docs)} authentic documents from vault")

    # ─── Rendering Document List ──────────────────────────────────────────

    def _render_documents(self):
        # Detach and delete existing list items cleanly to avoid any overlapping
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        filtered: List[Dict[str, Any]] = []
        for d in self.docs.values():
            # Category filter
            if self.current_filter_cat != "All" and d.get("category") != self.current_filter_cat:
                continue
            # Search query filter (matches filename, category, or content)
            if self.current_search_query:
                q = self.current_search_query.lower()
                name_match = q in d.get("filename", "").lower()
                cat_match = q in d.get("category", "").lower()
                content_match = any(q in p.get("text", "").lower() for p in d.get("pages", []))
                if not (name_match or cat_match or content_match):
                    continue
            filtered.append(d)

        # Sort descending by creation date
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        for doc in filtered:
            item = DocumentListItem(doc, self.theme)
            if self.selected_doc and self.selected_doc.get("doc_id") == doc.get("doc_id"):
                item.set_selected(True)
            item.clicked.connect(self._select_document)
            self.list_lay.addWidget(item)

        self.doc_count_pill.setText(f"{len(filtered)} {'documents' if len(filtered) != 1 else 'document'}")

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

    def _set_category_filter(self, cat: str):
        self.current_filter_cat = cat
        for c, btn in self.filter_buttons.items():
            btn.setProperty("active", c == cat)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._render_documents()
        self._show_feedback(f"Filtered repository by category: {cat}")

    def _on_search_query_changed(self, text: str):
        self.current_search_query = text.strip()
        self._render_documents()
        count = self.doc_count_pill.text()
        if self.current_search_query:
            self._show_feedback(f"Search results for '{self.current_search_query}': {count}")

    # ─── Document Selection ───────────────────────────────────────────────

    def _select_document(self, doc: Dict[str, Any]):
        self.selected_doc = doc
        self.inspector.show_doc(doc, self.storage_mode)
        # Update selection state on list rows
        for i in range(self.list_lay.count()):
            w = self.list_lay.itemAt(i).widget()
            if isinstance(w, DocumentListItem):
                w.set_selected(w._doc.get("doc_id") == doc.get("doc_id"))
        self._show_feedback(f"Selected: {doc.get('filename')}")

    # ─── Document Actions ─────────────────────────────────────────────────

    def _view_selected_document_text(self):
        if self.selected_doc:
            dialog = DocumentViewerDialog(self.selected_doc, self.theme, self)
            dialog.exec()

    def _verify_selected_document(self):
        if not self.selected_doc:
            return
        fpath = self.selected_doc.get("filepath", "")
        expected = self.selected_doc.get("sha256_hash", "")
        if os.path.exists(fpath):
            actual = BinaryParser.calculate_sha256(fpath)
            if actual.lower() == expected.lower():
                self.selected_doc["status"] = "Verified"
                self._show_feedback(f"Integrity verified for {Path(fpath).name}")
                QMessageBox.information(self, "Integrity Verified", f"Cryptographic SHA-256 fingerprint verified authentic.\nFile content matches disk record exactly.")
            else:
                self.selected_doc["status"] = "Tampered"
                self._show_feedback(f"Warning: Integrity mismatch for {Path(fpath).name}")
                QMessageBox.warning(self, "Integrity Warning", f"Cryptographic mismatch detected!\nFile content does not match recorded signature.")
            self.inspector.show_doc(self.selected_doc, self.storage_mode)
            self._render_documents()
            self._update_metrics_bar()

    def _delete_selected_document(self):
        if not self.selected_doc:
            return
        fname = self.selected_doc.get("filename", "this file")
        reply = QMessageBox.question(
            self, "Remove Document",
            f"Are you sure you want to remove '{fname}' from the vault catalog?\n(The file on disk will remain untouched)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            doc_id = self.selected_doc.get("doc_id")
            if doc_id and doc_id in self.docs:
                del self.docs[doc_id]
            self.selected_doc = None
            self.inspector.show_empty()
            self._render_documents()
            self._update_metrics_bar()
            self._show_feedback(f"Removed '{fname}' from repository index")

    def _verify_all_documents(self):
        tampered_count = 0
        for d in self.docs.values():
            fp = d.get("filepath", "")
            exp = d.get("sha256_hash", "")
            if os.path.exists(fp):
                act = BinaryParser.calculate_sha256(fp)
                d["status"] = "Verified" if act.lower() == exp.lower() else "Tampered"
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

    # ─── Document Import Pipeline ─────────────────────────────────────────

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
        filepath = self._import_queue.pop(0)
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
        self._render_documents()
        self._update_metrics_bar()
        self._select_document(doc_dict)
        self._show_feedback(f"Successfully imported '{doc_dict['filename']}'")
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLICATION ENTRYPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI Variable", 10))
    app.setStyle("Fusion")
    window = DocuVault()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
