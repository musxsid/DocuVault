"""
DocuVault — Animated Onboarding Carousel with Skip Trigger
Provides a 3-step feature walkthrough sequence using QStackedWidget,
QPropertyAnimation fading transitions, interactive dot indicators, and persistent skip flag.
"""

from typing import Dict, List

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from auth.session_manager import SessionManager


def draw_carousel_graphic(slide_idx: int, size: int = 120) -> QPixmap:
    """Renders high-resolution vector emblem for each onboarding slide."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Soft glowing circular container
    grad = QLinearGradient(0, 0, size, size)
    if slide_idx == 0:
        grad.setColorAt(0, QColor("#3B82F6"))
        grad.setColorAt(1, QColor("#1D4ED8"))
    elif slide_idx == 1:
        grad.setColorAt(0, QColor("#10B981"))
        grad.setColorAt(1, QColor("#047857"))
    else:
        grad.setColorAt(0, QColor("#FF7A3D"))
        grad.setColorAt(1, QColor("#EA580C"))

    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(10, 10, size - 20, size - 20), (size - 20) * 0.28, (size - 20) * 0.28)

    pen = QPen(QColor("#FFFFFF"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if slide_idx == 0:
        # Shield with Lock
        spath = QPainterPath()
        spath.moveTo(size * 0.30, size * 0.35)
        spath.lineTo(size * 0.50, size * 0.26)
        spath.lineTo(size * 0.70, size * 0.35)
        spath.lineTo(size * 0.70, size * 0.55)
        spath.quadTo(size * 0.70, size * 0.74, size * 0.50, size * 0.82)
        spath.quadTo(size * 0.30, size * 0.74, size * 0.30, size * 0.55)
        spath.closeSubpath()
        p.drawPath(spath)
        # Lock keyhole
        p.drawEllipse(QRectF(size * 0.44, size * 0.46, size * 0.12, size * 0.12))
        p.drawLine(int(size * 0.50), int(size * 0.58), int(size * 0.50), int(size * 0.68))

    elif slide_idx == 1:
        # Document with Checkmark & Hash lines
        dpath = QPainterPath()
        dpath.moveTo(size * 0.32, size * 0.25)
        dpath.lineTo(size * 0.56, size * 0.25)
        dpath.lineTo(size * 0.68, size * 0.37)
        dpath.lineTo(size * 0.68, size * 0.75)
        dpath.lineTo(size * 0.32, size * 0.75)
        dpath.closeSubpath()
        p.drawPath(dpath)
        # Checkmark
        chk = QPainterPath()
        chk.moveTo(size * 0.40, size * 0.52)
        chk.lineTo(size * 0.48, size * 0.60)
        chk.lineTo(size * 0.62, size * 0.44)
        p.drawPath(chk)

    else:
        # Magnifying glass with citation lines
        p.drawEllipse(QRectF(size * 0.28, size * 0.28, size * 0.36, size * 0.36))
        p.drawLine(int(size * 0.56), int(size * 0.56), int(size * 0.74), int(size * 0.74))
        # Inner spark
        p.drawPoint(int(size * 0.46), int(size * 0.46))

    p.end()
    return pm


class OnboardingSlide(QWidget):
    """Individual slide presentation card."""

    def __init__(
        self,
        index: int,
        title: str,
        subtitle: str,
        description: str,
        parent=None,
    ):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Vector Emblem
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(draw_carousel_graphic(index, 110))
        lay.addWidget(icon_lbl)
        lay.addSpacing(8)

        # Title
        t_lbl = QLabel(title)
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;")
        lay.addWidget(t_lbl)

        # Subtitle
        sub_lbl = QLabel(subtitle.upper())
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #38BDF8; letter-spacing: 1.5px;")
        lay.addWidget(sub_lbl)

        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 13px; color: #94A3B8; line-height: 1.6; max-width: 440px;")
        lay.addWidget(desc_lbl)


class OnboardingDialog(QDialog):
    """
    Animated onboarding walkthrough carousel.
    Highlights offline-first intelligence, cryptographic audits, and cited Q&A.
    """
    completed = pyqtSignal()

    SLIDES_DATA = [
        {
            "title": "Offline-First Intelligence",
            "subtitle": "Air-Gapped Local Privacy",
            "description": "Process, catalog, and analyze mission-critical documents with a strict zero-data-leakage architecture. All models and vectors execute locally on your hardware.",
        },
        {
            "title": "Cryptographic Verification",
            "subtitle": "Tamper-Proof Integrity Auditing",
            "description": "Continuous chunked SHA-256 integrity inspection combined with regex-powered compliance audits guarantee your contracts remain intact, authentic, and verified.",
        },
        {
            "title": "Instant Cited Q&A & Deadlines",
            "subtitle": "Sub-Second In-Memory Search",
            "description": "Execute natural language queries across your entire vault to extract immediate summaries, exact page citations, and automated calendar timeline deadlines.",
        },
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to DocuVault")
        self.resize(620, 520)
        self.setFixedSize(620, 520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._current_idx = 0

        self._build_ui()
        self._show_slide(0, animate=False)

    def _build_ui(self):
        # Master card container with border radius and dark backdrop
        main_card = QFrame(self)
        main_card.setObjectName("onboardingCard")
        main_card.setGeometry(0, 0, 620, 520)
        main_card.setStyleSheet("""
            #onboardingCard {
                background: #0F172A;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(main_card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        # ── Header: Brand Tag + Skip Button ──
        header = QHBoxLayout()
        brand_tag = QLabel("DOCUVAULT ONBOARDING")
        brand_tag.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 1.2px;")
        header.addWidget(brand_tag)

        header.addStretch()

        self.btn_skip = QPushButton("Skip \u2715")
        self.btn_skip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
                border-color: #475569;
            }
        """)
        self.btn_skip.clicked.connect(self._on_skip)
        header.addWidget(self.btn_skip)
        layout.addLayout(header)

        # ── Middle: Stacked Carousel Slides ──
        self.stack = QStackedWidget()
        for i, data in enumerate(self.SLIDES_DATA):
            slide = OnboardingSlide(
                index=i,
                title=data["title"],
                subtitle=data["subtitle"],
                description=data["description"],
            )
            self.stack.addWidget(slide)
        layout.addWidget(self.stack, 1)

        # ── Footer: Back, Dot Indicators, Next / Get Started ──
        footer = QHBoxLayout()
        footer.setContentsMargins(10, 10, 10, 10)

        # Back Button
        self.btn_back = QPushButton("\u2190 Back")
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 14px;
            }
            QPushButton:hover { color: #FFFFFF; }
        """)
        self.btn_back.clicked.connect(self._prev_slide)
        footer.addWidget(self.btn_back)

        footer.addStretch()

        # Dot Indicators
        self.dots: List[QPushButton] = []
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(8)
        for i in range(len(self.SLIDES_DATA)):
            dot = QPushButton()
            dot.setFixedSize(8, 8)
            dot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            dot.clicked.connect(lambda _, idx=i: self._show_slide(idx, animate=True))
            dots_layout.addWidget(dot)
            self.dots.append(dot)
        footer.addLayout(dots_layout)

        footer.addStretch()

        # Next / Get Started Button
        self.btn_next = QPushButton("Next \u2192")
        self.btn_next.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 9px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
        """)
        self.btn_next.clicked.connect(self._next_slide)
        footer.addWidget(self.btn_next)

        layout.addLayout(footer)

    def _show_slide(self, index: int, animate: bool = True):
        self._current_idx = index
        self.btn_back.setVisible(index > 0)
        self.btn_next.setText("Get Started \u2713" if index == len(self.SLIDES_DATA) - 1 else "Next \u2192")

        # Update dot indicators
        for i, dot in enumerate(self.dots):
            if i == index:
                dot.setFixedSize(22, 8)
                dot.setStyleSheet("background: #2563EB; border-radius: 4px; border: none;")
            else:
                dot.setFixedSize(8, 8)
                dot.setStyleSheet("background: #334155; border-radius: 4px; border: none;")

        # Switch slide with smooth opacity fade
        target_widget = self.stack.widget(index)
        self.stack.setCurrentIndex(index)

        if animate:
            eff = QGraphicsOpacityEffect(target_widget)
            target_widget.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setDuration(220)
            anim.setStartValue(0.2)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
            target_widget._fade_anim = anim

    def _next_slide(self):
        if self._current_idx < len(self.SLIDES_DATA) - 1:
            self._show_slide(self._current_idx + 1)
        else:
            self._complete_onboarding()

    def _prev_slide(self):
        if self._current_idx > 0:
            self._show_slide(self._current_idx - 1)

    def _on_skip(self):
        self._complete_onboarding()

    def _complete_onboarding(self):
        # Save first-run flag in config/settings.json so subsequent launches skip straight to Auth Gate
        SessionManager.set_onboarding_completed(True)
        self.completed.emit()
        self.accept()
