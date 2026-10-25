"""
DocuVault — Pro Tier Upgrade Modal
Modal triggered when Free Trial users exceed resource quotas (5 documents, 10 AI queries)
or access Pro-gated features (Cloud Sync, Smart Diff, PII Redaction, Calendar Export).
Provides feature comparisons and instant mock-checkout upgrade logic.
"""

from typing import Any, Dict, Optional

from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QIcon, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from auth.local_auth import LocalAuthManager
from auth.session_manager import SessionManager
from auth.tier_manager import TierConfig, UserTier


def draw_pro_crown_icon(size: int = 56) -> QPixmap:
    """Renders radiant Pro diamond/crown emblem with amber gradient."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Glowing rounded backdrop
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor("#F59E0B"))
    grad.setColorAt(1, QColor("#D97706"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(3, 3, size - 6, size - 6), size * 0.3, size * 0.3)

    # Crown / Gem Path
    p.setBrush(Qt.BrushStyle.NoBrush)
    pen = QPen(QColor("#FFFFFF"), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    cpath = QPainterPath()
    cpath.moveTo(size * 0.25, size * 0.65)
    cpath.lineTo(size * 0.20, size * 0.35)
    cpath.lineTo(size * 0.38, size * 0.48)
    cpath.lineTo(size * 0.50, size * 0.28)
    cpath.lineTo(size * 0.62, size * 0.48)
    cpath.lineTo(size * 0.80, size * 0.35)
    cpath.lineTo(size * 0.75, size * 0.65)
    cpath.closeSubpath()
    p.drawPath(cpath)

    # Base line
    p.drawLine(int(size * 0.25), int(size * 0.71), int(size * 0.75), int(size * 0.71))
    p.end()
    return pm


class UpgradeModal(QDialog):
    """
    Modern subscription upgrade dialog highlighting Pro tier perks
    and performing immediate tier elevation.
    """
    upgraded = pyqtSignal(dict)

    def __init__(
        self,
        current_user: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Upgrade to DocuVault Pro")
        self.setFixedSize(520, 660)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.user = current_user or {}
        self.reason = reason or "Upgrade to unlock unlimited document processing and cloud capabilities."
        self.local_auth = LocalAuthManager()

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("upgradeCard")
        card.setStyleSheet("""
            #upgradeCard {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 20px;
            }
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #F8FAFC;
            }
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        # Header with Dismiss
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748B;
                font-size: 14px;
                font-weight: 600;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #1E293B;
                color: #F8FAFC;
            }
        """)
        close_btn.clicked.connect(self.reject)
        top_row.addWidget(close_btn)
        lay.addLayout(top_row)

        # Hero Section
        hero_center = QVBoxLayout()
        hero_center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_center.setSpacing(10)

        crown_lbl = QLabel()
        crown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        crown_lbl.setPixmap(draw_pro_crown_icon(54))
        hero_center.addWidget(crown_lbl)

        title_lbl = QLabel("Upgrade to DocuVault Pro")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.4px;")
        hero_center.addWidget(title_lbl)

        # Trigger Context / Reason banner
        reason_frame = QFrame()
        reason_frame.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-radius: 9px;
            padding: 8px 12px;
        """)
        reason_lay = QHBoxLayout(reason_frame)
        reason_lay.setContentsMargins(8, 4, 8, 4)
        reason_lbl = QLabel(self.reason)
        reason_lbl.setWordWrap(True)
        reason_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reason_lbl.setStyleSheet("font-size: 12px; color: #FCA5A5; font-weight: 600;")
        reason_lay.addWidget(reason_lbl)
        hero_center.addWidget(reason_frame)

        lay.addLayout(hero_center)

        # Feature Perks Matrix Box
        perks_box = QFrame()
        perks_box.setStyleSheet("""
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
        """)
        perks_lay = QVBoxLayout(perks_box)
        perks_lay.setContentsMargins(18, 16, 18, 16)
        perks_lay.setSpacing(10)

        features = [
            ("Unlimited Document Storage", "Free limited to 5 docs max"),
            ("Unlimited RAG AI Queries & OCR", "Free limited to 10 queries per session"),
            ("Zero-Knowledge Cloud Sync & Web Hub", "Multi-device encrypted backup"),
            ("Automated PII Redaction & Smart Diff", "Compliance and legal audit logs"),
            ("Legal Lifecycle & iCal Calendar Export", "Automated contract expiry alerts"),
        ]

        for title, sub in features:
            row = QHBoxLayout()
            row.setSpacing(10)

            chk = QLabel("✓")
            chk.setStyleSheet("font-size: 14px; font-weight: 900; color: #10B981;")
            row.addWidget(chk)

            text_col = QVBoxLayout()
            text_col.setSpacing(1)
            f_title = QLabel(title)
            f_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F8FAFC;")
            f_sub = QLabel(sub)
            f_sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
            text_col.addWidget(f_title)
            text_col.addWidget(f_sub)
            row.addLayout(text_col)
            row.addStretch()

            perks_lay.addLayout(row)

        lay.addWidget(perks_box)

        # Pricing Pill
        price_row = QHBoxLayout()
        price_lbl = QLabel("<b>$19</b> / month or <b>$190</b> / year (Save 20%)")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_lbl.setStyleSheet("font-size: 13px; color: #FBBF24;")
        price_row.addWidget(price_lbl)
        lay.addLayout(price_row)

        # Actions
        btn_lay = QVBoxLayout()
        btn_lay.setSpacing(8)

        self.upgrade_btn = QPushButton("Upgrade to Pro Plan Now")
        self.upgrade_btn.setFixedHeight(44)
        self.upgrade_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upgrade_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
            }
        """)
        self.upgrade_btn.clicked.connect(self._do_upgrade)
        btn_lay.addWidget(self.upgrade_btn)

        self.later_btn = QPushButton("Maybe Later")
        self.later_btn.setFixedHeight(34)
        self.later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.later_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94A3B8;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #F8FAFC;
            }
        """)
        self.later_btn.clicked.connect(self.reject)
        btn_lay.addWidget(self.later_btn)

        lay.addLayout(btn_lay)
        outer.addWidget(card)

    def _do_upgrade(self) -> None:
        """Executes instant elevation to Pro plan in the database and active session."""
        email = self.user.get("email")
        if not email:
            active_session = SessionManager.load_session()
            if active_session:
                email = active_session.get("email")

        if email:
            self.local_auth.update_user_tier(email, UserTier.PRO.value)
            self.user["tier"] = UserTier.PRO.value
            SessionManager.save_session(self.user, remember_me=True)

        self.upgrade_btn.setText("✓ Upgraded! Welcome to Pro")
        self.upgrade_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        self.upgraded.emit(self.user)
        self.accept()
