"""
DocuVault — Dynamic 5-Second Feature Showcase Engine
Choreographed 60-FPS vector animation showcasing DocuVault's 4 core architectural pillars:
1. 🔐 Zero-Knowledge Cryptographic Vault (AES-256 & SHA-256)
2. 📄 Binary Magic-Byte Inspection & Multi-Format OCR
3. ⚡ Neural Hybrid RAG & Reciprocal Rank Fusion (RRF)
4. 📁 Git-Like Directory Auto-Sync & Legal Compliance Audits

Supports interactive step navigation, instant skip (Esc/Space/Button),
and seamless in-window transition to the authentication portal.
"""

import math
import sys
import time
from typing import List, Optional

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QGuiApplication, QKeyEvent, QLinearGradient,
    QMouseEvent, QPainter, QPainterPath, QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from auth.session_manager import SessionManager


class Particle:
    """Floating holographic spark node drifting through the ambient aura."""
    def __init__(self, x: float, y: float, speed: float, size: float, phase: float):
        self.x = x
        self.y = y
        self.speed = speed
        self.size = size
        self.phase = phase


class DocuVaultStartupCanvas(QWidget):
    """
    60 FPS Dynamic Vector Canvas depicting the 4 DocuVault Pillars:
    Stage 0: 3D Vault Shield, Swiss dial tumbler lock, and SHA-256 hash stream.
    Stage 1: Document dossier, electric-blue laser scan beam, and magic-byte tags.
    Stage 2: Quantum orbital rings, neural graph nodes, and RRF grounded citation.
    Stage 3: Circular radar directory scanner and green legal clause audit checks.
    """

    def __init__(
        self,
        duration_ms: int = 5000,
        theme_mode: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self.theme_mode = (theme_mode or SessionManager.get_theme_mode() or "light").lower()
        self.start_time = time.perf_counter()
        self.progress: float = 0.0  # 0.0 to 1.0
        self.stage_idx: int = 0     # 0 to 3
        self.stage_progress: float = 0.0 # 0.0 to 1.0 within stage
        self.scan_pos: float = 0.0
        self.orbit_angle: float = 0.0
        self.radar_angle: float = 0.0

        self.setMouseTracking(True)
        self.mouse_x: float = 400.0
        self.mouse_y: float = 300.0
        self.target_mouse_x: float = 400.0
        self.target_mouse_y: float = 300.0

        # Pre-seed floating ambient particles
        self.particles: List[Particle] = [
            Particle(0.18, 0.75, 0.035, 2.5, 0.0),
            Particle(0.32, 0.85, 0.045, 3.2, 1.2),
            Particle(0.50, 0.90, 0.030, 2.0, 2.4),
            Particle(0.68, 0.80, 0.050, 3.8, 3.6),
            Particle(0.82, 0.70, 0.040, 2.8, 4.8),
            Particle(0.25, 0.40, 0.025, 2.2, 1.7),
            Particle(0.75, 0.45, 0.032, 2.6, 3.1),
            Particle(0.40, 0.25, 0.028, 2.0, 5.0),
            Particle(0.60, 0.28, 0.036, 3.0, 0.8),
        ]

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        self.target_mouse_x = float(pos.x())
        self.target_mouse_y = float(pos.y())
        super().mouseMoveEvent(event)

    def set_theme(self, mode: Any) -> None:
        """Dynamically toggles canvas color scheme between Light and Dark."""
        if isinstance(mode, dict):
            self.theme_mode = mode.get("name", "light").lower()
        else:
            self.theme_mode = str(mode).lower()
        self.update()

    def update_frame(self, elapsed_ms: float) -> None:
        """Called every frame by timer to update physics, angles, and active stage."""
        self.progress = min(1.0, elapsed_ms / float(self.duration_ms))

        # 4 distinct stages over the duration
        stage_raw = self.progress * 4.0
        self.stage_idx = min(3, int(stage_raw))
        self.stage_progress = stage_raw - float(self.stage_idx)

        # Smooth mouse hover interpolation
        self.mouse_x += (self.target_mouse_x - self.mouse_x) * 0.08
        self.mouse_y += (self.target_mouse_y - self.mouse_y) * 0.08

        # Physics variables
        self.orbit_angle = (elapsed_ms / 1000.0) * 90.0
        self.radar_angle = (elapsed_ms / 1000.0) * 180.0

        cycle = (elapsed_ms / 1000.0) * 1.8
        self.scan_pos = (math.sin(cycle * math.pi) + 1.0) / 2.0

        dt = 0.016
        for p in self.particles:
            p.y -= p.speed * dt
            if p.y < 0.05:
                p.y = 0.95
                p.x = (p.x + 0.19) % 0.80 + 0.10

        self.update()

    def set_stage_manual(self, stage_idx: int) -> None:
        """Manual jump to specific feature stage."""
        self.stage_idx = max(0, min(3, stage_idx))
        self.stage_progress = 0.5
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0

        # Base obsidian dark background
        p.fillRect(self.rect(), QColor("#070A10"))

        # Blueprint grid lines
        grid_pen = QPen(QColor(18, 24, 38, 160), 1.0)
        p.setPen(grid_pen)
        step = 40
        for x in range(0, int(w), step):
            p.drawLine(x, 0, x, int(h))
        for y in range(0, int(h), step):
            p.drawLine(0, y, int(w), y)

        # Ambient Radial Breathing Warm Orange Glow with Mouse Hover Parallax
        gx = cx + (self.mouse_x - cx) * 0.22
        gy = cy + (self.mouse_y - cy) * 0.22
        glow_radius = 260.0 + 20.0 * math.sin(self.progress * math.pi * 3.0)
        radial_grad = QRadialGradient(QPointF(gx, gy - 65), glow_radius)
        radial_grad.setColorAt(0.0, QColor(255, 122, 46, 65))
        radial_grad.setColorAt(0.35, QColor(224, 79, 8, 22))
        radial_grad.setColorAt(0.75, QColor(7, 10, 16, 5))
        radial_grad.setColorAt(1.0, QColor(7, 10, 16, 0))
        p.setBrush(QBrush(radial_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(self.rect())

        # Ambient floating spark particles
        for pt in self.particles:
            px = pt.x * w + math.sin(self.progress * 5.0 + pt.phase) * 12.0
            py = pt.y * h
            p_alpha = int(120 + 80 * math.sin(self.progress * 8.0 + pt.phase))
            p.setBrush(QColor(255, 140, 70, max(25, min(220, p_alpha))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(px, py), pt.size, pt.size)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Choreographed Architectural Stage Rendering
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        anim_y = cy - 25.0
        if self.stage_idx == 0:
            self._render_stage0_vault(p, cx, anim_y)
        elif self.stage_idx == 1:
            self._render_stage1_scanner(p, cx, anim_y)
        elif self.stage_idx == 2:
            self._render_stage2_neural_rag(p, cx, anim_y)
        else:
            self._render_stage3_radar_audits(p, cx, anim_y)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Wordmark & Subtitle
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        p.setPen(QColor("#FFFFFF"))
        title_font = QFont("Plus Jakarta Sans", 24, QFont.Weight.Bold)
        title_font.setStyleHint(QFont.StyleHint.SansSerif)
        p.setFont(title_font)
        p.drawText(QRectF(cx - 200, h - 85, 400, 32), Qt.AlignmentFlag.AlignCenter, "DocuVault")

        sub_font = QFont("Plus Jakarta Sans", 8, QFont.Weight.Bold)
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.8)
        p.setFont(sub_font)
        p.setPen(QColor("#FFC46B"))
        p.drawText(QRectF(cx - 250, h - 55, 500, 20), Qt.AlignmentFlag.AlignCenter, "OFFLINE-FIRST DOCUMENT INTELLIGENCE")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Bottom 3px Sleek Progress Line
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        prog_w = min(420.0, w * 0.7)
        prog_h = 3.0
        prog_x = cx - prog_w / 2.0
        prog_y = h - 25.0

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#1F2735"))
        p.drawRoundedRect(QRectF(prog_x, prog_y, prog_w, prog_h), 1.5, 1.5)

        fill_w = max(4.0, prog_w * self.progress)
        p.setBrush(QColor("#EA580C"))
        p.drawRoundedRect(QRectF(prog_x, prog_y, fill_w, prog_h), 1.5, 1.5)

        p.end()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAGE 0: Zero-Knowledge Cryptographic Vault & AES-256
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _render_stage0_vault(self, p: QPainter, cx: float, cy: float) -> None:
        p.save()
        p.translate(cx, cy)

        # Precision Swiss dial tick rings
        p.save()
        p.rotate(self.orbit_angle * 0.8)
        dial_r = 95.0
        pen_dial = QPen(QColor(255, 122, 61, 140), 1.6, Qt.PenStyle.DashLine)
        pen_dial.setDashPattern([6, 10])
        p.setPen(pen_dial)
        p.drawEllipse(QPointF(0, 0), dial_r, dial_r)
        p.restore()

        # Counter-rotating outer hash degree ring
        p.save()
        p.rotate(-self.orbit_angle * 0.5)
        outer_r = 112.0
        p.setPen(QPen(QColor(255, 154, 90, 80), 1.2, Qt.PenStyle.DotLine))
        p.drawEllipse(QPointF(0, 0), outer_r, outer_r)
        p.restore()

        # 3D Vector Vault Shield
        sw, sh = 96.0, 112.0
        hw = sw / 2.0
        spath = QPainterPath()
        spath.moveTo(-hw, -sh * 0.45)
        spath.lineTo(hw, -sh * 0.45)
        spath.lineTo(hw, sh * 0.08)
        spath.quadTo(hw, sh * 0.44, 0.0, sh * 0.56)
        spath.quadTo(-hw, sh * 0.44, -hw, sh * 0.08)
        spath.closeSubpath()

        sgrad = QLinearGradient(-hw, -sh * 0.45, hw, sh * 0.56)
        sgrad.setColorAt(0.0, QColor("#FF7A3D"))
        sgrad.setColorAt(0.4, QColor("#EA580C"))
        sgrad.setColorAt(1.0, QColor("#C2410C"))
        p.setBrush(QBrush(sgrad))
        p.setPen(QPen(QColor(255, 255, 255, 220), 2.2))
        p.drawPath(spath)

        # Padlock Shackle snap animation
        shackle_y = -sh * 0.28
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#FFFFFF"), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        shackle_path = QPainterPath()
        shackle_path.moveTo(-16.0, shackle_y + 10.0)
        shackle_path.lineTo(-16.0, shackle_y)
        shackle_path.quadTo(-16.0, shackle_y - 20.0, 0.0, shackle_y - 20.0)
        shackle_path.quadTo(16.0, shackle_y - 20.0, 16.0, shackle_y)
        shackle_path.lineTo(16.0, shackle_y + 10.0)
        p.drawPath(shackle_path)

        # Padlock Body
        is_dark = (self.theme_mode == "dark")
        p.setBrush(QColor("#0F172A" if is_dark else "#FFFFFF"))
        p.setPen(QPen(QColor("#FF7A3D" if is_dark else "#EA580C"), 2.0))
        p.drawRoundedRect(QRectF(-22.0, shackle_y + 4.0, 44.0, 36.0), 6.0, 6.0)

        # Glowing Keyhole
        p.setBrush(QColor("#FFFFFF" if is_dark else "#0F172A"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0.0, shackle_y + 18.0), 3.8, 3.8)
        key_stem = QPainterPath()
        key_stem.moveTo(-1.8, shackle_y + 20.0)
        key_stem.lineTo(1.8, shackle_y + 20.0)
        key_stem.lineTo(1.2, shackle_y + 28.0)
        key_stem.lineTo(-1.2, shackle_y + 28.0)
        key_stem.closeSubpath()
        p.drawPath(key_stem)

        # Simulated Real-time SHA-256 Stream underneath
        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(255, 200, 150, 180) if is_dark else QColor(100, 116, 139, 220))
        p.drawText(QRectF(-140.0, sh * 0.62, 280.0, 20.0), Qt.AlignmentFlag.AlignCenter, "SHA-256: 7f83b165...e44c735d117")

        p.restore()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAGE 1: Binary Magic-Byte Inspection & Multi-Format OCR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _render_stage1_scanner(self, p: QPainter, cx: float, cy: float) -> None:
        p.save()
        p.translate(cx, cy)
        is_dark = (self.theme_mode == "dark")

        # Architectural Document Dossier
        dw, dh = 110.0, 134.0
        dx, dy = -dw / 2.0, -dh / 2.0
        fold = 16.0

        dpath = QPainterPath()
        dpath.moveTo(dx, dy)
        dpath.lineTo(dx + dw - fold, dy)
        dpath.lineTo(dx + dw, dy + fold)
        dpath.lineTo(dx + dw, dy + dh)
        dpath.lineTo(dx, dy + dh)
        dpath.closeSubpath()

        p.setBrush(QColor(15, 23, 42, 240) if is_dark else QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(56, 189, 248, 200) if is_dark else QColor(2, 132, 199, 220), 2.0))
        p.drawPath(dpath)

        # Fold corner
        fpath = QPainterPath()
        fpath.moveTo(dx + dw - fold, dy)
        fpath.lineTo(dx + dw - fold, dy + fold)
        fpath.lineTo(dx + dw, dy + fold)
        p.setBrush(QColor(56, 189, 248, 100) if is_dark else QColor(224, 242, 254, 220))
        p.setPen(QPen(QColor(56, 189, 248, 220) if is_dark else QColor(2, 132, 199, 220), 1.2))
        p.drawPath(fpath)

        # Code & Text Lines
        p.setPen(QPen(QColor(255, 255, 255, 170) if is_dark else QColor(148, 163, 184, 220), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        line_left = dx + 14.0
        max_w = dw - 28.0
        for i, frac in enumerate([0.75, 0.90, 0.55, 0.82, 0.68, 0.40]):
            ly = dy + 26.0 + i * 15.0
            p.drawLine(QPointF(line_left, ly), QPointF(line_left + max_w * frac, ly))

        # Holographic Laser Scanning Beam
        scan_y = dy + 10.0 + self.scan_pos * (dh - 20.0)
        beam_grad = QLinearGradient(-dw * 0.7, scan_y, dw * 0.7, scan_y)
        beam_grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        beam_grad.setColorAt(0.3, QColor(56, 189, 248, 200))
        beam_grad.setColorAt(0.5, QColor(255, 255, 255, 255))
        beam_grad.setColorAt(0.7, QColor(56, 189, 248, 200))
        beam_grad.setColorAt(1.0, QColor(56, 189, 248, 0))
        p.setPen(QPen(QBrush(beam_grad), 2.5))
        p.drawLine(QPointF(-dw * 0.7, scan_y), QPointF(dw * 0.7, scan_y))

        # Laser beam flare cone
        cone = QPainterPath()
        cone.moveTo(-dw * 0.65, scan_y)
        cone.lineTo(dw * 0.65, scan_y)
        cone.lineTo(dw * 0.55, scan_y + 10.0)
        cone.lineTo(-dw * 0.55, scan_y + 10.0)
        cone.closeSubpath()
        p.setBrush(QColor(56, 189, 248, 50))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(cone)

        # Magic-Byte Badges
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tags = [("%PDF-1.7", -65.0, dh * 0.58), ("PK\\x03\\x04", 0.0, dh * 0.58), ("<?xml", 65.0, dh * 0.58)]
        for tag, tx, ty in tags:
            p.setBrush(QColor(16, 185, 129, 40) if is_dark else QColor(236, 253, 245, 220))
            p.setPen(QPen(QColor(16, 185, 129, 200) if is_dark else QColor(16, 185, 129, 220), 1.0))
            p.drawRoundedRect(QRectF(tx - 26.0, ty - 8.0, 52.0, 16.0), 4.0, 4.0)
            p.setPen(QColor(16, 185, 129) if is_dark else QColor(5, 150, 105))
            p.drawText(QRectF(tx - 26.0, ty - 8.0, 52.0, 16.0), Qt.AlignmentFlag.AlignCenter, tag)

        p.restore()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAGE 2: Neural Hybrid RAG & Reciprocal Rank Fusion
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _render_stage2_neural_rag(self, p: QPainter, cx: float, cy: float) -> None:
        p.save()
        p.translate(cx, cy)
        is_dark = (self.theme_mode == "dark")

        # Interconnected Neural Graph Nodes
        nodes = [
            QPointF(-70.0, -50.0),
            QPointF(65.0, -45.0),
            QPointF(-80.0, 40.0),
            QPointF(75.0, 45.0),
            QPointF(0.0, -85.0),
            QPointF(0.0, 75.0),
            QPointF(0.0, 0.0), # Central Hub
        ]

        # Draw glowing neural connecting vectors
        p.setPen(QPen(QColor(168, 85, 247, 130 if is_dark else 170), 1.5, Qt.PenStyle.SolidLine))
        for i in range(len(nodes) - 1):
            p.drawLine(nodes[-1], nodes[i])
            next_idx = (i + 1) % (len(nodes) - 1)
            p.drawLine(nodes[i], nodes[next_idx])

        # Draw pulse spark on neural paths
        pulse_frac = (self.progress * 8.0) % 1.0
        for i in range(len(nodes) - 1):
            px = nodes[-1].x() + (nodes[i].x() - nodes[-1].x()) * pulse_frac
            py = nodes[-1].y() + (nodes[i].y() - nodes[-1].y()) * pulse_frac
            p.setBrush(QColor(216, 180, 254) if is_dark else QColor(147, 51, 234))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(px, py), 2.5, 2.5)

        # Draw node discs
        for i, nd in enumerate(nodes):
            is_center = (i == len(nodes) - 1)
            r = 8.0 if is_center else 5.5
            p.setBrush(QColor("#A855F7" if is_center else "#7E22CE"))
            p.setPen(QPen(QColor("#FFFFFF"), 1.8 if is_center else 1.2))
            p.drawEllipse(nd, r, r)

        # Floating RRF Formula & Citation Banner
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        banner_rect = QRectF(-130.0, 95.0, 260.0, 22.0)
        p.setBrush(QColor(15, 23, 42, 220) if is_dark else QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(168, 85, 247, 180 if is_dark else 220), 1.2))
        p.drawRoundedRect(banner_rect, 6.0, 6.0)
        p.setPen(QColor(216, 180, 254) if is_dark else QColor(107, 33, 168))
        p.drawText(banner_rect, Qt.AlignmentFlag.AlignCenter, "RRF Fused • Page 3, §4.2 Citation Grounded ✓")

        p.restore()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAGE 3: Git-Like Folder Auto-Sync & Legal Compliance Audits
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _render_stage3_radar_audits(self, p: QPainter, cx: float, cy: float) -> None:
        p.save()
        p.translate(cx, cy)
        is_dark = (self.theme_mode == "dark")

        # Circular Radar Screen
        radar_r = 90.0
        p.setBrush(QColor(15, 23, 42, 200) if is_dark else QColor(240, 253, 244, 200))
        p.setPen(QPen(QColor(16, 185, 129, 140 if is_dark else 170), 1.5))
        p.drawEllipse(QPointF(0, 0), radar_r, radar_r)
        p.drawEllipse(QPointF(0, 0), radar_r * 0.65, radar_r * 0.65)
        p.drawEllipse(QPointF(0, 0), radar_r * 0.35, radar_r * 0.35)

        # Radar Crosshairs
        p.setPen(QPen(QColor(16, 185, 129, 60 if is_dark else 90), 1.0))
        p.drawLine(QPointF(-radar_r, 0), QPointF(radar_r, 0))
        p.drawLine(QPointF(0, -radar_r), QPointF(0, radar_r))

        # Rotating Radar Beam Cone
        p.save()
        p.rotate(self.radar_angle)
        sweep_path = QPainterPath()
        sweep_path.moveTo(0, 0)
        sweep_path.arcTo(QRectF(-radar_r, -radar_r, radar_r * 2.0, radar_r * 2.0), 0, 45)
        sweep_path.closeSubpath()
        sweep_grad = QLinearGradient(0, 0, radar_r * 0.7, radar_r * 0.7)
        sweep_grad.setColorAt(0.0, QColor(16, 185, 129, 150))
        sweep_grad.setColorAt(1.0, QColor(16, 185, 129, 0))
        p.setBrush(QBrush(sweep_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(sweep_path)
        p.restore()

        # Detected Folder Targets (Pulsing Blips)
        blips = [(-45.0, -35.0, "vault/contracts"), (50.0, -25.0, "vault/invoices"), (-25.0, 45.0, "vault/hr")]
        p.setFont(QFont("Segoe UI", 7))
        for bx, by, lbl in blips:
            p.setBrush(QColor(16, 185, 129) if is_dark else QColor(5, 150, 105))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(bx, by), 3.5, 3.5)
            p.setPen(QColor(167, 243, 208) if is_dark else QColor(6, 95, 70))
            p.drawText(QPointF(bx + 6.0, by + 4.0), lbl)

        # Legal Clause Audit Checklist Badge
        badge_y = radar_r + 14.0
        checks_rect = QRectF(-140.0, badge_y, 280.0, 22.0)
        p.setBrush(QColor(15, 23, 42, 230) if is_dark else QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(16, 185, 129, 180 if is_dark else 220), 1.2))
        p.drawRoundedRect(checks_rect, 6.0, 6.0)
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.setPen(QColor(16, 185, 129) if is_dark else QColor(4, 120, 87))
        p.drawText(checks_rect, Qt.AlignmentFlag.AlignCenter, "✔ Notice Period  •  ✔ Jurisdiction  •  ✔ RFC 5545 .ics")

        p.restore()


class StartupShowcaseWidget(QWidget):
    """
    Dynamic 5-Second Feature Showcase Engine designed for embedding inside
    the single unified application window. Emits finished() upon completion or skip.
    """

    finished = pyqtSignal()

    FEATURE_DATA = [
        {
            "step": "PILLAR 01 // CORE ARCHITECTURE",
            "title": "Zero-Knowledge Cryptographic Vault",
            "subtitle": "AIR-GAPPED CLIENT-SIDE AES-256 ENCRYPTION",
            "bullets": [
                "Client-derived AES-256 encryption before any byte touches disk",
                "SHA-256 cryptographic tamper-proofing detecting byte alterations",
                "Complete local data sovereignty with zero cloud exfiltration",
            ],
            "badge": "Hardware-Isolated • Air-Gapped",
            "color": "#FF7A3D",
            "bg": "rgba(255, 122, 61, 0.12)",
        },
        {
            "step": "PILLAR 02 // INGESTION & OCR",
            "title": "Binary Magic-Byte Inspection & OCR",
            "subtitle": "PRE-EXECUTION THREAT NEUTRALIZATION",
            "bullets": [
                "Inspects raw initial bytes (%PDF, PK) blocking disguised files",
                "Optical Character Recognition (OCR) for scanned receipts & notes",
                "Structured ElementTree extraction for XML invoices & records",
            ],
            "badge": "Multi-Format • Instant Parsing",
            "color": "#38BDF8",
            "bg": "rgba(56, 189, 248, 0.12)",
        },
        {
            "step": "PILLAR 03 // INTELLIGENCE & RAG",
            "title": "Neural Hybrid Search & Grounded RAG",
            "subtitle": "DENSE + SPARSE RECIPROCAL RANK FUSION (RRF)",
            "bullets": [
                "Sub-second in-memory NumPy TF-IDF cosine similarity dot products",
                "Exact keyword matching fused with dense semantic vectors (RRF)",
                "Response Hallucination Guardrail verifying exact file citations",
            ],
            "badge": "< 0.3s Query Latency • Citation-Backed",
            "color": "#A855F7",
            "bg": "rgba(168, 85, 247, 0.12)",
        },
        {
            "step": "PILLAR 04 // AUTOMATION & AUDITS",
            "title": "Git-Like Folder Sync & Legal Audits",
            "subtitle": "BACKGROUND DIRECTORY MONITOR & CALENDAR EXPORT",
            "bullets": [
                "Autonomous folder watcher auto-extracting & indexing incoming files",
                "Regex legal clause auditing for Notice Period, Liability & Terms",
                "Proactive deadline extraction with working-day shift to RFC 5545 .ics",
            ],
            "badge": "Append-Only Audit Log • RFC 5545 Sync",
            "color": "#10B981",
            "bg": "rgba(16, 185, 129, 0.12)",
        },
    ]

    theme_toggled = pyqtSignal()

    def __init__(
        self,
        duration_ms: int = 5000,
        theme_mode: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self.theme_mode = (theme_mode or SessionManager.get_theme_mode() or "light").lower()
        self._closing: bool = False
        self._start_perf: float = 0.0
        self.current_stage: int = 0

        self.setObjectName("showcaseRoot")
        self._build_ui()
        self.set_theme(self.theme_mode)
        self._init_timer()

    def showEvent(self, event):
        super().showEvent(event)
        # Always reset animation timeline to 0ms when the showcase appears on screen
        self._start_perf = time.perf_counter()
        self._closing = False
        if hasattr(self, "timer") and not self.timer.isActive():
            self.timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if w > 1040 or h > 620:
            self.card.setFixedSize(w, h)
            is_dark = (self.theme_mode == "dark")
            self.card.setStyleSheet(f"""
                #showcaseCard {{
                    background-color: {'#050505' if is_dark else '#FFFFFF'};
                    border: none;
                    border-radius: 0px;
                }}
            """)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Single Unified Showcase Card Container
        self.card = QFrame()
        self.card.setObjectName("showcaseCard")
        self.card.setFixedSize(1040, 620)

        self.card_shadow = QGraphicsDropShadowEffect(self.card)
        self.card_shadow.setBlurRadius(28)
        self.card_shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(self.card_shadow)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(36, 26, 36, 26)
        card_lay.setSpacing(16)

        # ── 1. Top Bar: Live System Indicator, Theme Switcher & Skip Button ──
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)

        self.status_pill = QLabel("● LIVE ARCHITECTURE DEMO")
        self.status_pill.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #10B981;
            background: rgba(16, 185, 129, 0.12);
            border-radius: 12px;
            padding: 4px 12px;
            letter-spacing: 1.2px;
        """)
        top_bar.addWidget(self.status_pill)
        top_bar.addStretch()

        # Global Theme Switcher Pill Button
        self.btn_theme = QPushButton("☀️ Light" if self.theme_mode == "light" else "🌙 Dark")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setFixedHeight(30)
        self.btn_theme.setToolTip("Toggle Light / Dark mode for the application")
        self.btn_theme.clicked.connect(self._on_theme_btn_clicked)
        top_bar.addWidget(self.btn_theme)

        self.btn_skip = QPushButton("Skip Intro ❯ (Esc)")
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.setFixedHeight(30)
        self.btn_skip.clicked.connect(self._finish_and_close)
        top_bar.addWidget(self.btn_skip)
        card_lay.addLayout(top_bar)

        # ── 2. Split Showcase Body: Vector Canvas (Left) + Feature Presentation (Right) ──
        split_row = QHBoxLayout()
        split_row.setSpacing(32)

        # Left: 60 FPS Dynamic Vector Canvas
        self.canvas = DocuVaultStartupCanvas(duration_ms=self.duration_ms, theme_mode=self.theme_mode, parent=self)
        self.canvas.setMinimumSize(420, 360)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        split_row.addWidget(self.canvas, 5)

        # Right: Synchronized Feature Storyboard (Unboxed, clean Apple typography)
        self.info_panel = QFrame()
        self.info_panel.setStyleSheet("background: transparent; border: none;")
        info_lay = QVBoxLayout(self.info_panel)
        info_lay.setContentsMargins(16, 12, 16, 12)
        info_lay.setSpacing(12)
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_step = QLabel("PILLAR 01 · CORE ARCHITECTURE")
        self.lbl_step.setStyleSheet("font-size: 11px; font-weight: 700; color: #FF7A3D; letter-spacing: 1.5px;")
        info_lay.addWidget(self.lbl_step)

        self.lbl_title = QLabel("Zero-Knowledge Cryptographic Vault")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.15;")
        self.lbl_title.setWordWrap(True)
        info_lay.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("AIR-GAPPED CLIENT-SIDE AES-256 ENCRYPTION")
        self.lbl_subtitle.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 1.2px;")
        info_lay.addWidget(self.lbl_subtitle)

        info_lay.addSpacing(6)

        # Bullets
        self.bullet_labels = []
        for _ in range(3):
            blbl = QLabel("• ")
            blbl.setWordWrap(True)
            blbl.setStyleSheet("font-size: 13.5px; line-height: 1.55;")
            info_lay.addWidget(blbl)
            self.bullet_labels.append(blbl)

        info_lay.addSpacing(8)

        # Capability Pill Badge
        self.lbl_badge = QLabel("Hardware-Isolated • Air-Gapped")
        self.lbl_badge.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #FF7A3D;
            background: rgba(255, 122, 61, 0.12);
            border-radius: 8px;
            padding: 4px 12px;
        """)
        info_lay.addWidget(self.lbl_badge)

        self.info_panel.setVisible(True)
        split_row.addWidget(self.info_panel, 5)
        card_lay.addLayout(split_row, 1)

        # Bottom Stepper Navigation (Matching 4 core pillars)
        self.stepper_container = QWidget()
        self.stepper_container.setVisible(True)
        stepper_row = QHBoxLayout(self.stepper_container)
        stepper_row.setSpacing(10)

        self.step_buttons: List[QPushButton] = []
        step_titles = [
            "01 🔐 Cryptographic Vault",
            "02 📄 Magic-Byte & OCR",
            "03 ⚡ Hybrid Neural RAG",
            "04 📁 Folder Sync & Audits",
        ]
        for idx, stitle in enumerate(step_titles):
            sbtn = QPushButton(stitle)
            sbtn.setFixedHeight(34)
            sbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            sbtn.clicked.connect(lambda checked, s=idx: self._jump_to_stage(s))
            stepper_row.addWidget(sbtn)
            self.step_buttons.append(sbtn)

        card_lay.addWidget(self.stepper_container)

        self.prog_track = QFrame()
        self.prog_track.setFixedHeight(4)
        self.prog_track.setVisible(True)
        track_lay = QHBoxLayout(self.prog_track)
        track_lay.setContentsMargins(0, 0, 0, 0)

        self.prog_bar = QFrame()
        self.prog_bar.setFixedHeight(4)
        self.prog_bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF7A3D, stop:1 #EA580C); border-radius: 2px;")
        track_lay.addWidget(self.prog_bar)
        track_lay.addStretch()

        card_lay.addWidget(self.prog_track)
        outer.addWidget(self.card)

        self._update_stage_ui(0)

    def set_theme(self, theme: Any) -> None:
        """Dynamically applies complete Light or Dark styling across showcase engine."""
        if isinstance(theme, dict):
            mode = theme.get("name", "light").lower()
        else:
            mode = str(theme).lower()

        self.theme_mode = "dark" if mode == "dark" else "light"
        is_dark = (self.theme_mode == "dark")

        # Update Vector Canvas
        self.canvas.set_theme(self.theme_mode)

        # Outer Backdrop (scoped to root ID so children never inherit solid backgrounds)
        self.setStyleSheet(f"#showcaseRoot {{ background-color: {'#000000' if is_dark else '#F8FAFC'}; }}")

        # Main Showcase Card (borderless when filling the window)
        is_full = (self.width() > 1040 or self.height() > 620)
        radius = "0px" if is_full else "20px"
        border = "none" if is_full else f"1px solid {'#1A1A1A' if is_dark else '#E2E8F0'}"
        self.card.setStyleSheet(f"""
            #showcaseCard {{
                background-color: {'#050505' if is_dark else '#FFFFFF'};
                border: {border};
                border-radius: {radius};
            }}
        """)
        self.card_shadow.setColor(QColor(0, 0, 0, 90 if is_dark else 18))

        # Synchronized Right Info Panel (Unboxed, clean Apple presentation)
        self.info_panel.setStyleSheet("background: transparent; border: none;")

        # Titles and Text
        self.lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {'#FFFFFF' if is_dark else '#1C1C1E'}; letter-spacing: -0.5px; line-height: 1.15;")
        self.lbl_subtitle.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {'#8E8E93' if is_dark else '#636366'}; letter-spacing: 1.2px;")
        for blbl in self.bullet_labels:
            blbl.setStyleSheet(f"font-size: 13.5px; color: {'#D1D1D6' if is_dark else '#3A3A3C'}; line-height: 1.55;")

        # Top Bar Theme Button
        self.btn_theme.setText("☀️ Light" if is_dark else "🌙 Dark")
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#141414' if is_dark else '#F2F2F7'};
                border: 1px solid {'#262626' if is_dark else '#E5E5EA'};
                border-radius: 8px;
                color: {'#F8FAFC' if is_dark else '#1C1C1E'};
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {'#222222' if is_dark else '#E5E5EA'};
            }}
        """)

        # Skip Button
        self.btn_skip.setStyleSheet(f"""
            QPushButton {{
                background: {'#141414' if is_dark else '#F2F2F7'};
                border: 1px solid {'#262626' if is_dark else '#E5E5EA'};
                border-radius: 8px;
                color: {'#D1D1D6' if is_dark else '#636366'};
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {'#222222' if is_dark else '#E5E5EA'};
                color: {'#FFFFFF' if is_dark else '#1C1C1E'};
                border-color: #FF7A3D;
            }}
        """)

        # Progress Track
        self.prog_track.setStyleSheet(f"background: {'#1A1A1A' if is_dark else '#E2E8F0'}; border-radius: 2px;")

        # Refresh active stage highlights
        self._update_stage_ui(self.current_stage)

    def _on_theme_btn_clicked(self) -> None:
        """User toggled theme button from the startup showcase."""
        new_mode = "dark" if self.theme_mode == "light" else "light"
        SessionManager.set_theme_mode(new_mode)
        self.set_theme(new_mode)
        self.theme_toggled.emit()

    def _init_timer(self) -> None:
        """Starts 60 FPS animation timer."""
        self._start_perf = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

    def _on_tick(self) -> None:
        if self._closing:
            return

        elapsed_ms = (time.perf_counter() - self._start_perf) * 1000.0
        self.canvas.update_frame(elapsed_ms)

        prog = min(1.0, elapsed_ms / float(self.duration_ms))

        # Update progress bar width
        track_width = max(100, self.prog_track.width())
        self.prog_bar.setFixedWidth(int(track_width * prog))

        # Check if active stage changed
        new_stage = self.canvas.stage_idx
        if new_stage != self.current_stage:
            self.current_stage = new_stage
            self._update_stage_ui(new_stage)

        if elapsed_ms >= self.duration_ms:
            self._finish_and_close()

    def _jump_to_stage(self, stage_idx: int) -> None:
        """User manually clicked one of the 4 feature stepper buttons."""
        self.current_stage = stage_idx
        self.canvas.set_stage_manual(stage_idx)
        # Advance clock to start of that stage
        target_elapsed = (stage_idx / 4.0) * self.duration_ms + 10.0
        self._start_perf = time.perf_counter() - (target_elapsed / 1000.0)
        self._update_stage_ui(stage_idx)

    def _update_stage_ui(self, stage_idx: int) -> None:
        """Updates text, colors, and stepper highlights for the active feature."""
        data = self.FEATURE_DATA[stage_idx]
        color = data["color"]
        is_dark = (self.theme_mode == "dark")

        self.lbl_step.setText(data["step"])
        self.lbl_step.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {color}; letter-spacing: 1.5px;")

        self.lbl_title.setText(data["title"])
        self.lbl_subtitle.setText(data["subtitle"])

        for i, text in enumerate(data["bullets"]):
            self.bullet_labels[i].setText(f"•  {text}")

        self.lbl_badge.setText(data["badge"])
        self.lbl_badge.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {color};
            background: {data['bg'] if is_dark else 'rgba(0, 0, 0, 0.04)'};
            border-radius: 8px;
            padding: 4px 12px;
        """)

        # Update stepper buttons
        for idx, btn in enumerate(self.step_buttons):
            if idx == stage_idx:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {color};
                        border: none;
                        border-radius: 8px;
                        color: #FFFFFF;
                        font-size: 11.5px;
                        font-weight: 700;
                        padding: 0 12px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {'#121212' if is_dark else '#F2F2F7'};
                        border: none;
                        border-radius: 8px;
                        color: {'#8E8E93' if is_dark else '#636366'};
                        font-size: 11.5px;
                        font-weight: 600;
                        padding: 0 12px;
                    }}
                    QPushButton:hover {{
                        background: {'#1C1C1C' if is_dark else '#E5E5EA'};
                        color: {'#FFFFFF' if is_dark else '#1C1C1E'};
                    }}
                """)

    def _finish_and_close(self) -> None:
        """Triggered upon 5.0s completion or skip."""
        if self._closing:
            return
        self._closing = True
        self.timer.stop()
        self.finished.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Allow skipping on Escape, Space, or Enter."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Space, Qt.Key.Key_Return):
            self._finish_and_close()
        else:
            super().keyPressEvent(event)


class StartupSplashDialog(QDialog):
    """
    Backwards-compatible Dialog wrapper embedding StartupShowcaseWidget.
    Preserves seamless unit test execution while delegating rendering to the showcase engine.
    """

    def __init__(self, duration_ms: int = 5000, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self.setWindowTitle("DocuVault AI")
        self.resize(1080, 680)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.showcase = StartupShowcaseWidget(duration_ms=duration_ms, parent=self)
        self.showcase.finished.connect(self.accept)
        outer.addWidget(self.showcase)

        # Alias properties for backwards test compatibility
        self.lbl_status = self.showcase.lbl_title
        self.canvas = self.showcase.canvas
        self._closing = False

    def _finish_and_close(self) -> None:
        self._closing = True
        self.showcase._finish_and_close()
        self.accept()
