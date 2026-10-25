"""
DocuVault — Unified Authentication & Registration Dialog
Provides tabbed login and registration with PBKDF2 air-gapped security,
Google OAuth2 SSO support, remember-me keyring caching, and sleek dark aesthetic.
"""

import math
import random
import sys
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import (
    QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRect, QRectF, QSize,
    Qt, QThread, QTimer, pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QIcon, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)


from auth.keycloak_client import KeycloakClient
from auth.local_auth import LocalAuthManager
from auth.session_manager import SessionManager
from auth.tier_manager import UserTier
from core.exceptions import AuthenticationError


def draw_vault_logo(size: int = 48) -> QPixmap:
    """Renders crisp vector shield emblem with embedded document matching reference images."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    w = float(size)
    h = float(size)

    # Shield contour
    spath = QPainterPath()
    spath.moveTo(w * 0.16, h * 0.22)
    spath.quadTo(w * 0.50, h * 0.12, w * 0.84, h * 0.22)
    spath.quadTo(w * 0.88, h * 0.52, w * 0.50, h * 0.90)
    spath.quadTo(w * 0.12, h * 0.52, w * 0.16, h * 0.22)
    spath.closeSubpath()

    # Shield gradient fill
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor("#FF7A2E"))
    grad.setColorAt(1.0, QColor("#E04F08"))
    p.setBrush(QBrush(grad))
    p.setPen(QPen(QColor("#FFC46B"), 1.2))
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

    # Folded corner triangle
    fold_path = QPainterPath()
    fold_path.moveTo(dx + dw - fold, dy)
    fold_path.lineTo(dx + dw - fold, dy + fold)
    fold_path.lineTo(dx + dw, dy + fold)
    fold_path.closeSubpath()
    p.setBrush(QBrush(QColor("#FFE7D6")))
    p.drawPath(fold_path)

    # 3 horizontal lines on document
    pen_lines = QPen(QColor("#E04F08"), max(1.2, w * 0.038), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen_lines)
    lx1 = dx + dw * 0.22
    lx2 = dx + dw * 0.78
    p.drawLine(QPointF(lx1, dy + dh * 0.45), QPointF(lx2, dy + dh * 0.45))
    p.drawLine(QPointF(lx1, dy + dh * 0.62), QPointF(lx2, dy + dh * 0.62))
    p.drawLine(QPointF(lx1, dy + dh * 0.79), QPointF(lx2 * 0.85, dy + dh * 0.79))

    p.end()
    return pm


def draw_google_icon(size: int = 20) -> QPixmap:
    """Renders crisp vector Google 'G' icon for social login button."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 4-color Google G approximation
    rect = QRectF(2, 2, size - 4, size - 4)
    pen = QPen(QColor("#4285F4"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
    p.setPen(pen)
    p.drawArc(rect, 45 * 16, 270 * 16)
    p.drawLine(int(size * 0.5), int(size * 0.5), int(size * 0.85), int(size * 0.5))
    p.end()
    return pm


class GoogleAuthWorker(QThread):
    """Asynchronous worker for opening browser-based Google OAuth without UI freeze."""
    auth_finished = pyqtSignal(bool, dict, str)

    def __init__(self, keycloak_client: KeycloakClient, parent=None):
        super().__init__(parent)
        self.kc = keycloak_client

    def run(self):
        try:
            user_info = self.kc.start_google_oauth(callback_port=8088)
            if user_info:
                self.auth_finished.emit(True, user_info, "Google authentication successful.")
            else:
                self.auth_finished.emit(False, {}, "Google login cancelled or timed out.")
        except Exception as e:
            self.auth_finished.emit(False, {}, str(e))


class LoginDialog(QDialog):
    """
    Modern Tabbed Authentication Modal with Local PBKDF2 store,
    Keycloak SSO, 'Remember Me' caching, and visual air-gapped status.
    """
    login_successful = pyqtSignal(dict)

    def __init__(
        self,
        default_email: Optional[str] = None,
        initial_tab: int = 0,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("DocuVault — Access Control")
        self.setFixedSize(460, 640)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.default_email = default_email
        self.initial_tab = initial_tab
        self.local_auth = LocalAuthManager()
        self.keycloak_client = KeycloakClient()
        self.session_user: Optional[Dict[str, Any]] = None
        self._auth_worker: Optional[GoogleAuthWorker] = None

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("authCard")
        card.setStyleSheet("""
            #authCard {
                background-color: #0A0A0A;
                border: 1px solid #1E1E1E;
                border-radius: 18px;
            }
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #F8FAFC;
            }
            QLineEdit {
                background-color: #111111;
                border: 1.5px solid #242424;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13.5px;
                font-weight: 500;
                color: #F5F5F5;
                selection-background-color: #FF7A2E;
            }
            QLineEdit:hover {
                border: 1.5px solid #3A3A3A;
                background-color: #161616;
            }
            QLineEdit:focus {
                border: 2px solid #FF7A2E;
                background-color: #161616;
                color: #FFFFFF;
            }
            QCheckBox {
                color: #9E9E9E;
                font-size: 12.5px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                border-radius: 5px;
                border: 1.5px solid #2A2A2A;
                background: #141414;
            }
            QCheckBox::indicator:hover {
                border-color: #FF7A2E;
            }
            QCheckBox::indicator:checked {
                background-color: #FF7A2E;
                border-color: #FF7A2E;
            }
        """)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 24, 28, 24)
        card_lay.setSpacing(14)

        # Header with Logo & Close button
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(draw_vault_logo(36))
        top_row.addWidget(logo_lbl)

        brand_lay = QVBoxLayout()
        brand_lay.setSpacing(0)
        app_title = QLabel("DocuVault")
        app_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.3px;")
        sub_title = QLabel("Offline-First Document Intelligence")
        sub_title.setStyleSheet("font-size: 11px; color: #94A3B8;")
        brand_lay.addWidget(app_title)
        brand_lay.addWidget(sub_title)
        top_row.addLayout(brand_lay)
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
                background: #1A1A1A;
                color: #F8FAFC;
            }
        """)
        close_btn.clicked.connect(self.reject)
        top_row.addWidget(close_btn)
        card_lay.addLayout(top_row)

        card_lay.addSpacing(6)

        # Tab Segmented Control (Sign In / Register)
        seg_container = QFrame()
        seg_container.setStyleSheet("background-color: #161616; border: 1px solid #262626; border-radius: 10px; padding: 3px;")
        seg_lay = QHBoxLayout(seg_container)
        seg_lay.setContentsMargins(3, 3, 3, 3)
        seg_lay.setSpacing(4)

        self.tab_signin = QPushButton("Sign In")
        self.tab_signin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_signin.setFixedHeight(32)
        self.tab_signin.clicked.connect(lambda: self._switch_tab(0))

        self.tab_register = QPushButton("Create Free Account")
        self.tab_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_register.setFixedHeight(32)
        self.tab_register.clicked.connect(lambda: self._switch_tab(1))

        seg_lay.addWidget(self.tab_signin)
        seg_lay.addWidget(self.tab_register)
        card_lay.addWidget(seg_container)

        # Forms Stack
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_signin_page())
        self.stack.addWidget(self._build_register_page())
        card_lay.addWidget(self.stack)

        # Status Message Label
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 11px; color: #EF4444; min-height: 16px;")
        card_lay.addWidget(self.status_lbl)

        # Google Social Login
        google_btn = QPushButton("  Continue with Google SSO")
        google_btn.setIcon(QIcon(draw_google_icon(18)))
        google_btn.setFixedHeight(40)
        google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        google_btn.setStyleSheet("""
            QPushButton {
                background-color: #141414;
                border: 1px solid #262626;
                border-radius: 10px;
                color: #F8FAFC;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1F1F1F;
                border-color: #383838;
            }
        """)
        google_btn.clicked.connect(self._handle_google_oauth)
        card_lay.addWidget(google_btn)

        # Air-Gapped / Offline Resilience Badge
        footer_badge = QLabel("🛡 Air-Gapped PBKDF2 Local Security Active")
        footer_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_badge.setStyleSheet("font-size: 11px; color: #10B981; font-weight: 600; padding-top: 4px;")
        card_lay.addWidget(footer_badge)

        outer.addWidget(card)
        self._switch_tab(self.initial_tab)
        if self.default_email:
            self.in_signin_email.setText(self.default_email)
            self.in_signin_pwd.setFocus()


    def _build_signin_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 4)
        lay.setSpacing(10)

        # Email
        lbl_e = QLabel("Email Address")
        lbl_e.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_signin_email = QLineEdit()
        self.in_signin_email.setPlaceholderText("name@company.com")
        lay.addWidget(lbl_e)
        lay.addWidget(self.in_signin_email)

        # Password with show/hide
        lbl_p = QLabel("Password")
        lbl_p.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_signin_pwd = QLineEdit()
        self.in_signin_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_signin_pwd.setPlaceholderText("Enter your password")
        self.in_signin_pwd.returnPressed.connect(self._do_signin)
        lay.addWidget(lbl_p)
        lay.addWidget(self.in_signin_pwd)

        # Options row (Remember Me)
        opt_row = QHBoxLayout()
        opt_row.setContentsMargins(0, 2, 0, 2)
        self.chk_remember = QCheckBox("Keep me signed in")
        self.chk_remember.setChecked(True)
        self.chk_remember.setCursor(Qt.CursorShape.PointingHandCursor)
        opt_row.addWidget(self.chk_remember)
        opt_row.addStretch()
        lay.addLayout(opt_row)

        lay.addSpacing(4)

        # Submit button
        submit = QPushButton("Sign In to DocuVault")
        submit.setFixedHeight(42)
        submit.setCursor(Qt.CursorShape.PointingHandCursor)
        submit.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF7A3D, stop:1 #EA580C);
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF8E59, stop:1 #F97316);
            }
        """)
        submit.clicked.connect(self._do_signin)
        lay.addWidget(submit)
        lay.addStretch()
        return w

    def _build_register_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 4)
        lay.setSpacing(8)

        lbl_n = QLabel("Full Name")
        lbl_n.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_reg_name = QLineEdit()
        self.in_reg_name.setPlaceholderText("Alex Vance")
        lay.addWidget(lbl_n)
        lay.addWidget(self.in_reg_name)

        lbl_e = QLabel("Email Address")
        lbl_e.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_reg_email = QLineEdit()
        self.in_reg_email.setPlaceholderText("alex@example.com")
        lay.addWidget(lbl_e)
        lay.addWidget(self.in_reg_email)

        lbl_p = QLabel("Password (min 6 characters)")
        lbl_p.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_reg_pwd = QLineEdit()
        self.in_reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_reg_pwd.setPlaceholderText("Create a secure password")
        lay.addWidget(lbl_p)
        lay.addWidget(self.in_reg_pwd)

        lbl_c = QLabel("Country / Region (Optional)")
        lbl_c.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.in_reg_country = QLineEdit()
        self.in_reg_country.setPlaceholderText("Global")
        lay.addWidget(lbl_c)
        lay.addWidget(self.in_reg_country)

        # Plan highlight note
        plan_note = QLabel("✓ Free Trial includes 5 docs & 10 AI RAG queries")
        plan_note.setStyleSheet("font-size: 11px; color: #38BDF8; font-weight: 500;")
        lay.addWidget(plan_note)

        # Register button
        submit = QPushButton("Create Account & Start Free")
        submit.setFixedHeight(40)
        submit.setCursor(Qt.CursorShape.PointingHandCursor)
        submit.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
            }
        """)
        submit.clicked.connect(self._do_register)
        lay.addWidget(submit)
        lay.addStretch()
        return w

    def _switch_tab(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        self.status_lbl.setText("")
        active_style = """
            QPushButton {
                background-color: #242424;
                border: 1px solid #383838;
                border-radius: 7px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
            }
        """
        inactive_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #8E8E93;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """
        if idx == 0:
            self.tab_signin.setStyleSheet(active_style)
            self.tab_register.setStyleSheet(inactive_style)
        else:
            self.tab_signin.setStyleSheet(inactive_style)
            self.tab_register.setStyleSheet(active_style)

    def _do_signin(self) -> None:
        email = self.in_signin_email.text().strip()
        pwd = self.in_signin_pwd.text()

        if not email or not pwd:
            self.status_lbl.setText("Please enter both email and password.")
            return

        try:
            # Authenticate via Keycloak with local PBKDF2 fallback
            user_data = self.keycloak_client.authenticate_password(email, pwd)
            remember = self.chk_remember.isChecked()
            SessionManager.save_session(user_data, token=user_data.get("token"), remember_me=remember)

            self.session_user = user_data
            self.login_successful.emit(user_data)
            self.accept()
        except AuthenticationError as e:
            self.status_lbl.setText(str(e))
        except Exception as e:
            self.status_lbl.setText(f"Login error: {str(e)}")

    def _do_register(self) -> None:
        name = self.in_reg_name.text().strip()
        email = self.in_reg_email.text().strip()
        pwd = self.in_reg_pwd.text()
        country = self.in_reg_country.text().strip() or "Global"

        if not name:
            self.status_lbl.setText("Please enter your full name.")
            return
        if not email or "@" not in email:
            self.status_lbl.setText("Please enter a valid email address.")
            return
        if len(pwd) < 6:
            self.status_lbl.setText("Password must be at least 6 characters.")
            return

        try:
            # Registers user with Free tier
            user_data = self.keycloak_client.register_user(
                email=email,
                password=pwd,
                full_name=name,
                country=country,
                tier=UserTier.FREE.value,
            )
            SessionManager.save_session(user_data, token=user_data.get("token"), remember_me=True)
            self.session_user = user_data
            self.login_successful.emit(user_data)
            self.accept()
        except AuthenticationError as e:
            self.status_lbl.setText(str(e))
        except Exception as e:
            self.status_lbl.setText(f"Registration error: {str(e)}")

    def _handle_google_oauth(self) -> None:
        """Launches Google OAuth in background thread with visual status feedback."""
        self.status_lbl.setStyleSheet("font-size: 11px; color: #38BDF8; min-height: 16px;")
        self.status_lbl.setText("Opening browser for Google SSO... Waiting for authorization...")

        self._auth_worker = GoogleAuthWorker(self.keycloak_client, self)
        self._auth_worker.auth_finished.connect(self._on_google_oauth_finished)
        self._auth_worker.start()

    def _on_google_oauth_finished(self, success: bool, user_info: dict, message: str) -> None:
        if success and user_info:
            SessionManager.save_session(user_info, token=user_info.get("token"), remember_me=True)
            self.session_user = user_info
            self.login_successful.emit(user_info)
            self.accept()
        else:
            self.status_lbl.setStyleSheet("font-size: 11px; color: #EF4444; min-height: 16px;")
            self.status_lbl.setText(message)


class AnimatedSegmentedSlider(QFrame):
    """
    Precision hardware-accelerated animated segmented pill control.
    Provides generous 280px width so 'Sign In' and 'Create Account'
    fit comfortably without text clipping, with fluid sliding indicator.
    """
    tab_changed = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("segSlider")
        self.setFixedSize(280, 38)
        self.current_index = 0
        self.theme_mode = "light"

        # Sliding Pill Indicator
        self.indicator = QFrame(self)
        self.indicator.setObjectName("segIndicator")
        self.indicator.setGeometry(3, 3, 134, 32)

        # Tab 0: Sign In
        self.btn_signin = QPushButton("Sign In", self)
        self.btn_signin.setGeometry(3, 3, 134, 32)
        self.btn_signin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_signin.clicked.connect(lambda: self.set_tab(0, animate=True))

        # Tab 1: Create Account
        self.btn_register = QPushButton("Create Account", self)
        self.btn_register.setGeometry(143, 3, 134, 32)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(lambda: self.set_tab(1, animate=True))

        # Animation setup
        self._anim = QPropertyAnimation(self.indicator, b"geometry", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._apply_style()

    def set_tab(self, index: int, animate: bool = True) -> None:
        if index not in (0, 1):
            return
        self.current_index = index
        target_x = 3 if index == 0 else 143
        target_rect = QRect(target_x, 3, 134, 32)

        if animate:
            self._anim.stop()
            self._anim.setStartValue(self.indicator.geometry())
            self._anim.setEndValue(target_rect)
            self._anim.start()
        else:
            self.indicator.setGeometry(target_rect)

        self._apply_button_styles()
        self.tab_changed.emit(index)

    def set_theme(self, theme_mode: str) -> None:
        self.theme_mode = theme_mode.lower()
        self._apply_style()

    def _apply_style(self) -> None:
        is_dark = (self.theme_mode == "dark")
        self.setStyleSheet(f"""
            #segSlider {{
                background-color: {'#111111' if is_dark else '#F1F5F9'};
                border: 1px solid {'#242424' if is_dark else '#E2E8F0'};
                border-radius: 9px;
            }}
            #segIndicator {{
                background-color: {'#262626' if is_dark else '#FFFFFF'};
                border: 1px solid {'#3A3A3A' if is_dark else '#CBD5E1'};
                border-radius: 7px;
            }}
        """)
        self._apply_button_styles()

    def _apply_button_styles(self) -> None:
        is_dark = (self.theme_mode == "dark")
        active_color = "#FFFFFF" if is_dark else "#0F172A"
        inactive_color = "#8E8E93" if is_dark else "#64748B"
        hover_color = "#E0E0E0" if is_dark else "#1E293B"

        style_base = """
            QPushButton {
                background: transparent;
                border: none;
                font-size: 12.5px;
                padding: 0px;
            }
        """

        style_0 = style_base + f"""
            QPushButton {{
                color: {active_color if self.current_index == 0 else inactive_color};
                font-weight: {'700' if self.current_index == 0 else '600'};
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
        """
        style_1 = style_base + f"""
            QPushButton {{
                color: {active_color if self.current_index == 1 else inactive_color};
                font-weight: {'700' if self.current_index == 1 else '600'};
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
        """
        self.btn_signin.setStyleSheet(style_0)
        self.btn_register.setStyleSheet(style_1)


class BrandConstellationParticle:
    """Drifting node in the interactive constellation background."""
    def __init__(self, x: float, y: float, vx: float, vy: float, radius: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius


class AuthBrandPanel(QFrame):
    """
    Interactive left brand panel for EmbeddedAuthWidget matching reference design.
    Features pitch black OLED surface (#000000) with real-time mouse-following
    warm radial amber glow, blueprint grid lines, and an animated floating constellation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._target_x = 220.0
        self._target_y = 260.0
        self._curr_x = 220.0
        self._curr_y = 260.0

        # Seed 20 constellation particles
        random.seed(42)
        self._particles: List[BrandConstellationParticle] = []
        for _ in range(20):
            self._particles.append(
                BrandConstellationParticle(
                    x=random.uniform(20.0, 500.0),
                    y=random.uniform(20.0, 700.0),
                    vx=random.uniform(-0.35, 0.35),
                    vy=random.uniform(-0.35, 0.35),
                    radius=random.uniform(1.8, 3.2),
                )
            )

        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._on_glow_step)
        self._glow_timer.start(16)

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        self._target_x = float(pos.x())
        self._target_y = float(pos.y())
        super().mouseMoveEvent(event)

    def _on_glow_step(self):
        # Smooth lerp mouse glow
        dx = self._target_x - self._curr_x
        dy = self._target_y - self._curr_y
        if abs(dx) > 0.4 or abs(dy) > 0.4:
            self._curr_x += dx * 0.08
            self._curr_y += dy * 0.08

        # Advance particles
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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Base pitch black OLED surface
        p.fillRect(self.rect(), QColor("#000000"))

        # Interactive mouse-following warm amber glow
        radial = QRadialGradient(QPointF(self._curr_x, self._curr_y), 380.0)
        radial.setColorAt(0.0, QColor(255, 122, 46, 52))
        radial.setColorAt(0.35, QColor(224, 79, 8, 20))
        radial.setColorAt(0.75, QColor(0, 0, 0, 0))
        radial.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(radial))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(self.rect())

        # Subtle blueprint grid lines
        grid_pen = QPen(QColor(255, 255, 255, 8), 1.0)
        p.setPen(grid_pen)
        step = 42
        for x in range(0, int(w), step):
            p.drawLine(x, 0, x, int(h))
        for y in range(0, int(h), step):
            p.drawLine(0, y, int(w), y)

        # Draw constellation links between nearby particles
        num_p = len(self._particles)
        for i in range(num_p):
            p1 = self._particles[i]
            for j in range(i + 1, num_p):
                p2 = self._particles[j]
                dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if dist < 105.0:
                    alpha = int((1.0 - dist / 105.0) * 35)
                    p.setPen(QPen(QColor(255, 130, 50, alpha), 1.0))
                    p.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))

            # Connect particle to mouse if nearby
            m_dist = math.hypot(p1.x - self._curr_x, p1.y - self._curr_y)
            if m_dist < 130.0:
                m_alpha = int((1.0 - m_dist / 130.0) * 55)
                p.setPen(QPen(QColor(255, 160, 60, m_alpha), 1.2))
                p.drawLine(QPointF(p1.x, p1.y), QPointF(self._curr_x, self._curr_y))

        # Draw particle nodes
        for pt in self._particles:
            p.setBrush(QBrush(QColor(255, 150, 65, 120)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(pt.x, pt.y), pt.radius, pt.radius)

        p.end()


class EmbeddedAuthWidget(QWidget):
    """
    Embedded Authentication Portal for the Single Unified Application Window.
    Split-screen with dark interactive brand panel on left and floating card on right.
    """
    authenticated = pyqtSignal(dict)
    theme_toggled = pyqtSignal()

    def __init__(
        self,
        default_email: Optional[str] = None,
        initial_tab: int = 0,
        theme_mode: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("embeddedAuthRoot")
        self.default_email = default_email
        self.initial_tab = initial_tab
        self.theme_mode = (theme_mode or SessionManager.get_theme_mode() or "light").lower()
        self.local_auth = LocalAuthManager()
        self.keycloak_client = KeycloakClient()
        self.session_user: Optional[Dict[str, Any]] = None
        self._auth_worker: Optional[GoogleAuthWorker] = None

        self._build_ui()
        self.set_theme(self.theme_mode)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        # When embedded in the main window (larger than initial 1020x610), expand to fill the entire window
        if w > 1020 or h > 610:
            self.card.setFixedSize(w, h)
            left_w = max(460, int(w * 0.48))
            self.left_panel.setFixedWidth(left_w)
            self.right_panel.setFixedWidth(w - left_w)
            is_dark = (self.theme_mode == "dark")
            self.card.setStyleSheet(f"""
                #unifiedAuthCard {{
                    background-color: {'#000000' if is_dark else '#F6F7F9'};
                    border: none;
                    border-radius: 0px;
                }}
            """)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SINGLE UNIFIED CONTAINER (1020 x 610 initially for unit test assertion)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.card = QFrame()
        self.card.setObjectName("unifiedAuthCard")
        self.card.setFixedSize(1020, 610)

        self.card_shadow = QGraphicsDropShadowEffect(self.card)
        self.card_shadow.setBlurRadius(36)
        self.card_shadow.setOffset(0, 10)
        self.card_shadow.setColor(QColor(0, 0, 0, 24))
        self.card.setGraphicsEffect(self.card_shadow)

        card_lay = QHBoxLayout(self.card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # 1. Left Showcase Column (Interactive Pitch-Black Brand Panel)
        self.left_panel = AuthBrandPanel(self.card)
        self.left_panel.setFixedWidth(520)
        self.left_panel.setStyleSheet("""
            AuthBrandPanel {
                background: #000000;
                border: none;
            }
            QLabel {
                background: transparent;
                background-color: transparent;
                border: none;
            }
        """)
        left_lay = QVBoxLayout(self.left_panel)
        left_lay.setContentsMargins(44, 32, 44, 32)
        left_lay.setSpacing(0)

        # Brand Header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(14)
        logo_lbl = QLabel()
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_lbl.setPixmap(draw_vault_logo(42))
        brand_row.addWidget(logo_lbl)

        brand_titles = QVBoxLayout()
        brand_titles.setSpacing(2)
        self.lbl_brand_name = QLabel("DocuVault")
        self.lbl_brand_name.setStyleSheet("background: transparent; font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;")
        self.lbl_brand_tag = QLabel("OFFLINE-FIRST INTELLIGENCE")
        self.lbl_brand_tag.setStyleSheet("background: transparent; font-size: 9px; font-weight: 700; color: #FF9500; letter-spacing: 1.5px;")
        brand_titles.addWidget(self.lbl_brand_name)
        brand_titles.addWidget(self.lbl_brand_tag)
        brand_row.addLayout(brand_titles)
        brand_row.addStretch()

        self.badge_airgap = QLabel("● AIR-GAPPED CORE")
        self.badge_airgap.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.14);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.8px;
        """)
        brand_row.addWidget(self.badge_airgap)
        left_lay.addLayout(brand_row)
        left_lay.addStretch(1)

        # Centered Hero & Value Proposition Content
        center_content = QVBoxLayout()
        center_content.setContentsMargins(0, 0, 0, 0)
        center_content.setSpacing(0)

        # Hero Title
        self.hero_title = QLabel("Enterprise intelligence.\nUncompromised privacy.")
        self.hero_title.setStyleSheet("background: transparent; font-size: 28px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.8px; line-height: 1.16;")
        self.hero_title.setWordWrap(True)
        center_content.addWidget(self.hero_title)

        center_content.addSpacing(8)
        self.hero_subtitle = QLabel("Hardware-isolated document intelligence with zero cloud exfiltration, hybrid neural RAG, and verified citations.")
        self.hero_subtitle.setStyleSheet("background: transparent; font-size: 12px; color: #9E9E9E; line-height: 1.4;")
        self.hero_subtitle.setWordWrap(True)
        center_content.addWidget(self.hero_subtitle)

        center_content.addSpacing(22)

        # Clean, Unboxed Apple Feature Storyboard
        features = [
            ("Zero-knowledge vault", "Hardware AES-256 client encryption before persistence.", "#FF7A2E"),
            ("Search that cites sources", "Sub-second hybrid neural RAG with source verification.", "#38BDF8"),
            ("Autonomous sync & audit", "Continuous directory tracking with legal clause auditing.", "#10B981"),
        ]
        self.feat_cards = []
        for ftitle, fdesc, fcolor in features:
            frow = QFrame()
            frow.setStyleSheet("background: transparent; border: none;")
            frow_lay = QHBoxLayout(frow)
            frow_lay.setContentsMargins(0, 0, 0, 0)
            frow_lay.setSpacing(14)

            # Minimalist glowing accent dot
            dot = QLabel("●")
            dot.setStyleSheet(f"background: transparent; color: {fcolor}; font-size: 13px; font-weight: 900;")
            dot.setFixedWidth(16)
            frow_lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

            tlay = QVBoxLayout()
            tlay.setSpacing(3)
            t_lbl = QLabel(ftitle)
            t_lbl.setStyleSheet("background: transparent; font-size: 13.5px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.2px;")
            d_lbl = QLabel(fdesc)
            d_lbl.setStyleSheet("background: transparent; font-size: 11.5px; color: #8E8E93; line-height: 1.35;")
            d_lbl.setWordWrap(True)
            tlay.addWidget(t_lbl)
            tlay.addWidget(d_lbl)
            frow_lay.addLayout(tlay, 1)

            center_content.addWidget(frow)
            center_content.addSpacing(16)
            self.feat_cards.append((frow, t_lbl, d_lbl, dot))

        center_content.addSpacing(10)

        # Architectural Security Metrics Strip (Clean, unboxed typography)
        self.metrics_card = QFrame()
        self.metrics_card.setFixedHeight(48)
        self.metrics_card.setStyleSheet("background: transparent; border: none;")
        m_lay = QHBoxLayout(self.metrics_card)
        m_lay.setContentsMargins(0, 0, 0, 0)
        m_lay.setSpacing(0)

        stats = [
            ("0 ms", "Cloud Latency", "#FF7A2E"),
            ("256-bit", "AES Encryption", "#38BDF8"),
            ("100%", "Air-Gapped", "#10B981"),
        ]
        for idx, (sval, slbl, scolor) in enumerate(stats):
            col_box = QVBoxLayout()
            col_box.setSpacing(2)
            col_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl = QLabel(sval)
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl.setStyleSheet(f"background: transparent; font-size: 14px; font-weight: 800; color: {scolor}; letter-spacing: -0.3px;")
            n_lbl = QLabel(slbl)
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n_lbl.setStyleSheet("background: transparent; font-size: 10px; font-weight: 600; color: #8E8E93;")
            col_box.addWidget(v_lbl)
            col_box.addWidget(n_lbl)
            m_lay.addLayout(col_box, 1)

            if idx < len(stats) - 1:
                divider = QFrame()
                divider.setFixedWidth(1)
                divider.setFixedHeight(22)
                divider.setStyleSheet("background: rgba(255, 255, 255, 0.12);")
                m_lay.addWidget(divider)

        center_content.addWidget(self.metrics_card)
        left_lay.addLayout(center_content)
        left_lay.addStretch(1)

        # Bottom trust indicator
        self.trust_lbl = QLabel("🔒 Encrypted locally · Works offline · Air-gapped compliance")
        self.trust_lbl.setStyleSheet("background: transparent; font-size: 11px; color: #707070; font-weight: 500;")
        left_lay.addWidget(self.trust_lbl)

        card_lay.addWidget(self.left_panel)

        # 2. Right Column (Form Panel)
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(500)
        right_outer_lay = QVBoxLayout(self.right_panel)
        right_outer_lay.setContentsMargins(40, 24, 40, 24)
        right_outer_lay.addStretch(1)

        # Centered modern webapp form box (fixed width 420px for optimal readability)
        self.form_box = QFrame()
        self.form_box.setFixedWidth(420)
        self.form_box.setStyleSheet("background: transparent; border: none;")
        right_lay = QVBoxLayout(self.form_box)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        # Top Bar: Segmented Tab Switcher (280px) & Theme Toggle
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self.seg_slider = AnimatedSegmentedSlider(self.form_box)
        self.seg_container = self.seg_slider  # Backwards compatibility
        self.tab_signin = self.seg_slider.btn_signin  # Backwards compatibility
        self.tab_register = self.seg_slider.btn_register  # Backwards compatibility
        self.seg_slider.tab_changed.connect(self._switch_tab)
        top_bar.addWidget(self.seg_slider)
        top_bar.addStretch()

        self.btn_theme = QPushButton("☀️ Light" if self.theme_mode == "light" else "🌙 Dark")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setFixedHeight(34)
        self.btn_theme.clicked.connect(self._on_toggle_theme_clicked)
        top_bar.addWidget(self.btn_theme)
        right_lay.addLayout(top_bar)

        right_lay.addSpacing(18)

        # Header Titles
        self.auth_head = QLabel("Unlock your vault")
        self.auth_head.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: -0.5px;")
        self.auth_sub = QLabel("Sign in or create a free account.")
        self.auth_sub.setStyleSheet("font-size: 13px; color: #667085;")
        right_lay.addWidget(self.auth_head)
        right_lay.addSpacing(2)
        right_lay.addWidget(self.auth_sub)

        right_lay.addSpacing(16)

        # Stack for Sign-in & Register forms
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_signin_page())
        self.stack.addWidget(self._build_register_page())
        right_lay.addWidget(self.stack)

        right_lay.addSpacing(14)

        # Sleek Divider: ── or continue with ──
        self.div_container = QWidget()
        div_lay = QHBoxLayout(self.div_container)
        div_lay.setContentsMargins(0, 0, 0, 0)
        div_lay.setSpacing(10)

        self.div_left = QFrame()
        self.div_left.setFrameShape(QFrame.Shape.HLine)
        self.div_left.setFixedHeight(1)

        self.div_text = QLabel("or continue with")
        self.div_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.div_text.setStyleSheet("font-size: 11px; font-weight: 600; color: #808080;")

        self.div_right = QFrame()
        self.div_right.setFrameShape(QFrame.Shape.HLine)
        self.div_right.setFixedHeight(1)

        div_lay.addWidget(self.div_left, 1)
        div_lay.addWidget(self.div_text)
        div_lay.addWidget(self.div_right, 1)
        right_lay.addWidget(self.div_container)

        right_lay.addSpacing(10)

        # Google Button
        self.google_btn = QPushButton("Continue with Google")
        self.google_btn.setIcon(QIcon(draw_google_icon(18)))
        self.google_btn.setFixedHeight(42)
        self.google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.google_btn.clicked.connect(self._handle_google_oauth)
        right_lay.addWidget(self.google_btn)

        right_lay.addSpacing(6)

        # Status Label
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 11px; color: #EF4444; min-height: 16px;")
        right_lay.addWidget(self.status_lbl)

        right_outer_lay.addWidget(self.form_box, 0, Qt.AlignmentFlag.AlignCenter)
        right_outer_lay.addStretch(1)

        card_lay.addWidget(self.right_panel)
        outer.addWidget(self.card)

        self._switch_tab(self.initial_tab)
        if self.default_email:
            self.in_signin_email.setText(self.default_email)
            self.in_signin_pwd.setFocus()
        else:
            self.in_signin_email.clear()
            self.in_signin_email.setFocus()
        self.in_signin_pwd.clear()

    def _build_signin_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.lbl_signin_email = QLabel("Email address")
        self.lbl_signin_email.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_signin_email = QLineEdit()
        self.in_signin_email.setFixedHeight(42)
        self.in_signin_email.setPlaceholderText("name@company.com")
        lay.addWidget(self.lbl_signin_email)
        lay.addWidget(self.in_signin_email)
        lay.addSpacing(6)

        self.lbl_signin_pwd = QLabel("Password")
        self.lbl_signin_pwd.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_signin_pwd = QLineEdit()
        self.in_signin_pwd.setFixedHeight(42)
        self.in_signin_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_signin_pwd.setPlaceholderText("Enter your password")
        self.in_signin_pwd.returnPressed.connect(self._do_signin)
        lay.addWidget(self.lbl_signin_pwd)
        lay.addWidget(self.in_signin_pwd)
        lay.addSpacing(6)

        self.chk_remember = QCheckBox("Keep me signed in")
        self.chk_remember.setChecked(True)
        self.chk_remember.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.chk_remember)
        lay.addSpacing(8)

        self.btn_signin_submit = QPushButton("Unlock vault")
        self.btn_signin_submit.setFixedHeight(44)
        self.btn_signin_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_signin_submit.clicked.connect(self._do_signin)
        lay.addWidget(self.btn_signin_submit)

        return w

    def _build_register_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.lbl_reg_name = QLabel("Full name")
        self.lbl_reg_name.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_reg_name = QLineEdit()
        self.in_reg_name.setFixedHeight(42)
        self.in_reg_name.setPlaceholderText("Alex Vance")
        lay.addWidget(self.lbl_reg_name)
        lay.addWidget(self.in_reg_name)

        self.lbl_reg_email = QLabel("Email address")
        self.lbl_reg_email.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_reg_email = QLineEdit()
        self.in_reg_email.setFixedHeight(42)
        self.in_reg_email.setPlaceholderText("alex@example.com")
        lay.addWidget(self.lbl_reg_email)
        lay.addWidget(self.in_reg_email)

        self.lbl_reg_pwd = QLabel("Password (min 6 characters)")
        self.lbl_reg_pwd.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_reg_pwd = QLineEdit()
        self.in_reg_pwd.setFixedHeight(42)
        self.in_reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_reg_pwd.setPlaceholderText("Create a secure password")
        lay.addWidget(self.lbl_reg_pwd)
        lay.addWidget(self.in_reg_pwd)

        self.lbl_reg_country = QLabel("Country / Region (Optional)")
        self.lbl_reg_country.setStyleSheet("font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;")
        self.in_reg_country = QLineEdit()
        self.in_reg_country.setFixedHeight(42)
        self.in_reg_country.setPlaceholderText("Global")
        lay.addWidget(self.lbl_reg_country)
        lay.addWidget(self.in_reg_country)
        lay.addSpacing(4)

        self.btn_reg_submit = QPushButton("Create Account && Start Free")
        self.btn_reg_submit.setFixedHeight(44)
        self.btn_reg_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reg_submit.clicked.connect(self._do_register)
        lay.addWidget(self.btn_reg_submit)

        return w

    def set_theme(self, theme: Any) -> None:
        """Applies complete Light or Dark styling to the unified auth container."""
        if isinstance(theme, dict):
            mode = theme.get("name", "light").lower()
        else:
            mode = str(theme).lower()

        self.theme_mode = "dark" if mode == "dark" else "light"
        is_dark = (self.theme_mode == "dark")

        # Outer Backdrop (scoped to root ID so children never inherit solid white backgrounds)
        self.setStyleSheet(f"#embeddedAuthRoot {{ background-color: {'#000000' if is_dark else '#F6F7F9'}; }}")

        # Floating Card Container (fills screen borderless when in full application window)
        is_full = (self.width() > 1020 or self.height() > 610)
        radius = "0px" if is_full else "24px"
        border = "none" if is_full else f"1px solid {'#1E1E1E' if is_dark else '#E4E7EC'}"
        self.card.setStyleSheet(f"""
            #unifiedAuthCard {{
                background-color: {'#000000' if is_dark else '#FFFFFF'};
                border: {border};
                border-radius: {radius};
            }}
        """)
        self.left_panel.setStyleSheet("""
            AuthBrandPanel {
                background: #000000;
                border: none;
            }
            QLabel {
                background: transparent;
                background-color: transparent;
                border: none;
            }
        """)
        self.right_panel.setStyleSheet(f"background-color: {'#000000' if is_dark else '#FFFFFF'}; border: none;")
        self.card_shadow.setColor(QColor(0, 0, 0, 90 if is_dark else 14))

        self.auth_head.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {'#FFFFFF' if is_dark else '#101828'}; letter-spacing: -0.5px;")
        self.auth_sub.setStyleSheet(f"font-size: 13px; color: {'#9E9E9E' if is_dark else '#667085'};")

        # Top Bar Theme Button
        self.btn_theme.setText("☀️ Light" if is_dark else "🌙 Dark")
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#141414' if is_dark else '#F6F7F9'};
                border: 1px solid {'#262626' if is_dark else '#E4E7EC'};
                border-radius: 8px;
                color: {'#FFFFFF' if is_dark else '#334155'};
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {'#222222' if is_dark else '#E4E7EC'};
            }}
        """)

        # Segmented Control Slider
        if hasattr(self, 'seg_slider'):
            self.seg_slider.set_theme(self.theme_mode)

        # Inputs Styling (Ultra-premium responsive input design, 42px height)
        input_qss = f"""
            QLineEdit {{
                background-color: {'#111111' if is_dark else '#F8FAFC'};
                border: 1.5px solid {'#242424' if is_dark else '#D0D5DD'};
                border-radius: 10px;
                padding: 0 16px;
                font-size: 13.5px;
                font-weight: 500;
                color: {'#F5F5F5' if is_dark else '#101828'};
                selection-background-color: #FF7A2E;
            }}
            QLineEdit:hover {{
                border: 1.5px solid {'#3A3A3A' if is_dark else '#98A2B3'};
                background-color: {'#161616' if is_dark else '#FFFFFF'};
            }}
            QLineEdit:focus {{
                border: 2px solid {'#FF7A2E' if is_dark else '#F26A1B'};
                background-color: {'#161616' if is_dark else '#FFFFFF'};
                color: {'#FFFFFF' if is_dark else '#101828'};
            }}
        """
        for inp in [self.in_signin_email, self.in_signin_pwd, self.in_reg_name, self.in_reg_email, self.in_reg_pwd, self.in_reg_country]:
            inp.setStyleSheet(input_qss)

        # Label colors
        label_col = '#C7C7C7' if is_dark else '#344054'
        for lbl in (self.lbl_signin_email, self.lbl_signin_pwd, self.lbl_reg_name, self.lbl_reg_email, self.lbl_reg_pwd, self.lbl_reg_country):
            lbl.setStyleSheet(f"font-size: 12.5px; font-weight: 700; color: {label_col}; letter-spacing: 0.2px;")

        # CheckBox
        self.chk_remember.setStyleSheet(f"""
            QCheckBox {{
                color: {'#9E9E9E' if is_dark else '#475467'};
                font-size: 12.5px;
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 17px;
                height: 17px;
                border-radius: 5px;
                border: 1.5px solid {'#2E2E2E' if is_dark else '#D1D5DB'};
                background: {'#111111' if is_dark else '#FFFFFF'};
            }}
            QCheckBox::indicator:hover {{
                border-color: {'#FF7A2E' if is_dark else '#F26A1B'};
            }}
            QCheckBox::indicator:checked {{
                background-color: {'#FF7A2E' if is_dark else '#F26A1B'};
                border-color: {'#FF7A2E' if is_dark else '#F26A1B'};
            }}
        """)

        # Submit Buttons (High-contrast vibrant gradient)
        btn_submit_qss = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {'#FF7A2E' if is_dark else '#F26A1B'}, stop:1 {'#E04F08' if is_dark else '#D04000'});
                border: 1px solid {'#FF9357' if is_dark else '#FDBA74'};
                border-radius: 11px;
                color: #FFFFFF;
                font-size: 13.5px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {'#FF8B47' if is_dark else '#FF7A2E'}, stop:1 {'#F25C13' if is_dark else '#E04F08'});
            }}
            QPushButton:pressed {{
                background: #C23B00;
            }}
        """
        self.btn_signin_submit.setStyleSheet(btn_submit_qss)
        self.btn_reg_submit.setStyleSheet(btn_submit_qss)

        # Divider
        if hasattr(self, 'div_left'):
            line_color = '#222222' if is_dark else '#E2E8F0'
            self.div_left.setStyleSheet(f"background-color: {line_color}; border: none;")
            self.div_right.setStyleSheet(f"background-color: {line_color}; border: none;")
            self.div_text.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {'#757575' if is_dark else '#94A3B8'};")

        # Feature rows unboxed Apple typography
        if hasattr(self, 'feat_cards'):
            for frow, t_lbl, d_lbl, dot in self.feat_cards:
                frow.setStyleSheet("background: transparent; border: none;")
                t_lbl.setStyleSheet("background: transparent; font-size: 13.5px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.2px;")
                d_lbl.setStyleSheet("background: transparent; font-size: 11.5px; color: #8E8E93; line-height: 1.35;")

        # Metrics strip (unboxed Apple typography)
        if hasattr(self, 'metrics_card'):
            self.metrics_card.setStyleSheet("background: transparent; border: none;")

        # Google SSO Button
        self.google_btn.setFixedHeight(42)
        self.google_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#111111' if is_dark else '#FFFFFF'};
                border: 1.5px solid {'#262626' if is_dark else '#D0D5DD'};
                border-radius: 10px;
                color: {'#F0F0F0' if is_dark else '#101828'};
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#1A1A1A' if is_dark else '#F8FAFC'};
                border-color: {'#FF7A2E' if is_dark else '#F26A1B'};
                color: {'#FFFFFF' if is_dark else '#101828'};
            }}
        """)

    def _on_toggle_theme_clicked(self) -> None:
        """User toggled theme button from the auth screen."""
        new_mode = "dark" if self.theme_mode == "light" else "light"
        SessionManager.set_theme_mode(new_mode)
        self.set_theme(new_mode)
        self.theme_toggled.emit()

    def _switch_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.status_lbl.setText("")
        if hasattr(self, 'seg_slider') and self.seg_slider.current_index != index:
            self.seg_slider.set_tab(index, animate=True)
        if hasattr(self, 'auth_head') and hasattr(self, 'auth_sub'):
            if index == 0:
                self.auth_head.setText("Unlock your vault")
                self.auth_sub.setText("Sign in or create a free account.")
            else:
                self.auth_head.setText("Create your vault")
                self.auth_sub.setText("Free trial includes 5 docs and 10 AI RAG queries.")

    def _do_signin(self) -> None:
        email = self.in_signin_email.text().strip()
        pwd = self.in_signin_pwd.text()
        remember = self.chk_remember.isChecked()

        if not email or not pwd:
            self.status_lbl.setText("Please enter both email and password.")
            return

        try:
            user_data = self.keycloak_client.authenticate_password(email, pwd)
            SessionManager.save_session(user_data, token=user_data.get("token"), remember_me=remember)
            self.session_user = user_data
            self.authenticated.emit(user_data)
        except AuthenticationError as e:
            self.status_lbl.setText(str(e))
        except Exception as e:
            self.status_lbl.setText(f"Login error: {str(e)}")

    def _do_register(self) -> None:
        name = self.in_reg_name.text().strip()
        email = self.in_reg_email.text().strip()
        pwd = self.in_reg_pwd.text()
        country = self.in_reg_country.text().strip() or "Global"

        if not name:
            self.status_lbl.setText("Please enter your full name.")
            return
        if not email or "@" not in email:
            self.status_lbl.setText("Please enter a valid email address.")
            return
        if len(pwd) < 6:
            self.status_lbl.setText("Password must be at least 6 characters.")
            return

        try:
            user_data = self.keycloak_client.register_user(
                email=email,
                password=pwd,
                full_name=name,
                country=country,
                tier=UserTier.FREE.value,
            )
            SessionManager.save_session(user_data, token=user_data.get("token"), remember_me=True)
            self.session_user = user_data
            self.authenticated.emit(user_data)
        except AuthenticationError as e:
            self.status_lbl.setText(str(e))
        except Exception as e:
            self.status_lbl.setText(f"Registration error: {str(e)}")

    def _handle_google_oauth(self) -> None:
        self.status_lbl.setStyleSheet("font-size: 11px; color: #EA580C; min-height: 16px;")
        self.status_lbl.setText("Opening browser for Google SSO... Waiting for authorization...")

        self._auth_worker = GoogleAuthWorker(self.keycloak_client, self)
        self._auth_worker.auth_finished.connect(self._on_google_oauth_finished)
        self._auth_worker.start()

    def _on_google_oauth_finished(self, success: bool, user_info: dict, message: str) -> None:
        if success and user_info:
            SessionManager.save_session(user_info, token=user_info.get("token"), remember_me=True)
            self.session_user = user_info
            self.authenticated.emit(user_info)
        else:
            self.status_lbl.setStyleSheet("font-size: 11px; color: #EF4444; min-height: 16px;")
            self.status_lbl.setText(message)

