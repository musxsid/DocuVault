"""
DocuVault — User Profile Dialog
Displays active user details, subscription tier badge (Free Trial vs. Pro Plan),
live quota utilization meters (documents, chat queries), and sign-out controls.
"""

from typing import Any, Dict, Optional

from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QVBoxLayout, QWidget,
)

from auth.session_manager import SessionManager
from auth.tier_manager import TierConfig, UserTier
from ui.components.upgrade_modal import UpgradeModal


def draw_user_avatar(name: str, size: int = 56) -> QPixmap:
    """Renders sleek circular avatar with user initials."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Initial extraction
    initials = "".join([part[0].upper() for part in name.strip().split() if part])[:2] or "U"

    # Gradient background
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor("#6366F1"))
    grad.setColorAt(1, QColor("#4F46E5"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(1, 1, size - 2, size - 2))

    # Initials Text
    p.setPen(QColor("#FFFFFF"))
    font = QFont("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto", int(size * 0.36), QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initials)
    p.end()
    return pm


class ProfileDialog(QDialog):
    """
    User account profile modal with live tier badge, quota meters,
    direct upgrade trigger, and sign out mechanism.
    """
    signed_out = pyqtSignal()
    tier_changed = pyqtSignal(dict)

    def __init__(
        self,
        user_info: Dict[str, Any],
        current_doc_count: int = 0,
        current_chat_count: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("DocuVault — User Profile")
        self.setFixedSize(480, 580)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.user = user_info or {}
        self.doc_count = current_doc_count
        self.chat_count = current_chat_count

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("profileCard")
        card.setStyleSheet("""
            #profileCard {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 18px;
            }
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #F8FAFC;
            }
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                color: transparent;
                height: 8px;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background-color: #FF7A3D;
            }
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # Header with Close
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        p_title = QLabel("Account Profile")
        p_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")
        top_row.addWidget(p_title)
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

        # User Info Hero
        hero_box = QFrame()
        hero_box.setStyleSheet("""
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 8px;
        """)
        h_lay = QHBoxLayout(hero_box)
        h_lay.setContentsMargins(12, 10, 12, 10)
        h_lay.setSpacing(14)

        full_name = self.user.get("full_name") or self.user.get("name") or "DocuVault User"
        avatar_lbl = QLabel()
        avatar_lbl.setPixmap(draw_user_avatar(full_name, 50))
        h_lay.addWidget(avatar_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        name_lbl = QLabel(full_name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        email_lbl = QLabel(self.user.get("email", "offline_user@docuvault.local"))
        email_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")

        # Tier Badge Pill
        is_pro = str(self.user.get("tier", "Free")).capitalize() == "Pro"
        badge = QLabel("PRO PLAN" if is_pro else "FREE TRIAL")
        if is_pro:
            badge.setStyleSheet("""
                background-color: #1E3A8A;
                color: #60A5FA;
                font-size: 10px;
                font-weight: 800;
                border-radius: 6px;
                padding: 2px 8px;
                border: 1px solid #3B82F6;
            """)
        else:
            badge.setStyleSheet("""
                background-color: #334155;
                color: #94A3B8;
                font-size: 10px;
                font-weight: 800;
                border-radius: 6px;
                padding: 2px 8px;
                border: 1px solid #475569;
            """)
        badge.setFixedHeight(20)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        badge_row.addWidget(badge)
        badge_row.addStretch()

        info_col.addWidget(name_lbl)
        info_col.addWidget(email_lbl)
        info_col.addLayout(badge_row)
        h_lay.addLayout(info_col)
        h_lay.addStretch()

        lay.addWidget(hero_box)

        # Usage Quota Box
        quota_box = QFrame()
        quota_box.setStyleSheet("""
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
        """)
        q_lay = QVBoxLayout(quota_box)
        q_lay.setContentsMargins(16, 14, 16, 14)
        q_lay.setSpacing(12)

        q_head = QLabel("RESOURCE UTILIZATION")
        q_head.setStyleSheet("font-size: 11px; font-weight: 700; color: #94A3B8; letter-spacing: 0.5px;")
        q_lay.addWidget(q_head)

        # Document quota meter
        doc_row = QHBoxLayout()
        doc_txt = QLabel("Indexed Documents")
        doc_txt.setStyleSheet("font-size: 12px; color: #CBD5E1;")
        if is_pro:
            doc_stat = QLabel(f"{self.doc_count} / Unlimited")
            doc_stat.setStyleSheet("font-size: 12px; font-weight: 700; color: #60A5FA;")
        else:
            doc_stat = QLabel(f"{self.doc_count} / 5 used")
            doc_stat.setStyleSheet("font-size: 12px; font-weight: 700; color: #FF7A3D;")
        doc_row.addWidget(doc_txt)
        doc_row.addStretch()
        doc_row.addWidget(doc_stat)
        q_lay.addLayout(doc_row)

        doc_bar = QProgressBar()
        doc_bar.setRange(0, 100)
        doc_bar.setValue(100 if is_pro else min(int((self.doc_count / 5.0) * 100), 100))
        q_lay.addWidget(doc_bar)

        # Chat queries quota meter
        chat_row = QHBoxLayout()
        chat_txt = QLabel("AI RAG Queries (Session)")
        chat_txt.setStyleSheet("font-size: 12px; color: #CBD5E1;")
        if is_pro:
            chat_stat = QLabel(f"{self.chat_count} / Unlimited")
            chat_stat.setStyleSheet("font-size: 12px; font-weight: 700; color: #60A5FA;")
        else:
            chat_stat = QLabel(f"{self.chat_count} / 10 used")
            chat_stat.setStyleSheet("font-size: 12px; font-weight: 700; color: #FF7A3D;")
        chat_row.addWidget(chat_txt)
        chat_row.addStretch()
        chat_row.addWidget(chat_stat)
        q_lay.addLayout(chat_row)

        chat_bar = QProgressBar()
        chat_bar.setRange(0, 100)
        chat_bar.setValue(100 if is_pro else min(int((self.chat_count / 10.0) * 100), 100))
        q_lay.addWidget(chat_bar)

        # Air-gapped isolation badge
        iso_row = QHBoxLayout()
        iso_lbl = QLabel("Vault Engine: Air-Gapped Local PBKDF2 & Vector Index")
        iso_lbl.setStyleSheet("font-size: 11px; color: #10B981; font-weight: 600;")
        iso_row.addWidget(iso_lbl)
        q_lay.addLayout(iso_row)

        lay.addWidget(quota_box)

        # Upgrade Button (if Free)
        if not is_pro:
            upgrade_btn = QPushButton("★ Upgrade to Pro Plan — Unlock Unlimited Access")
            upgrade_btn.setFixedHeight(40)
            upgrade_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            upgrade_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);
                    border: none;
                    border-radius: 9px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                }
            """)
            upgrade_btn.clicked.connect(self._open_upgrade_modal)
            lay.addWidget(upgrade_btn)

        lay.addStretch()

        # Sign Out button
        signout_btn = QPushButton("Sign Out of Vault")
        signout_btn.setFixedHeight(36)
        signout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #475569;
                border-radius: 8px;
                color: #EF4444;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.12);
                border-color: #EF4444;
            }
        """)
        signout_btn.clicked.connect(self._do_signout)
        lay.addWidget(signout_btn)

        outer.addWidget(card)

    def _open_upgrade_modal(self) -> None:
        modal = UpgradeModal(self.user, parent=self)
        modal.upgraded.connect(self._on_upgraded)
        modal.exec()

    def _on_upgraded(self, updated_user: dict) -> None:
        self.user = updated_user
        self.tier_changed.emit(updated_user)
        self.accept()

    def _do_signout(self) -> None:
        SessionManager.clear_session()
        self.signed_out.emit()
        self.accept()
