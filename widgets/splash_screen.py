"""
splash_screen.py
----------------
Professional splash screen with a blueprint grid, stylized motor layout,
and software initialization checklist.
"""

from __future__ import annotations

import math
import pathlib
import sys
from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QPropertyAnimation, QRectF
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QPen, QBrush, QLinearGradient, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
)

class StripedProgressBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._value = 0
        self._max = 100
        self._min = 0
        self._animation_offset = 0.0
        
        # Timer to animate the stripes sliding smoothly
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._step_animation)
        self._anim_timer.start(25) # ~40 FPS for super smooth sliding

    def value(self) -> int:
        return self._value

    def setValue(self, val: int) -> None:
        self._value = max(self._min, min(self._max, val))
        self.update()

    def setRange(self, min_val: int, max_val: int) -> None:
        self._min = min_val
        self._max = max_val
        self.update()

    def _step_animation(self) -> None:
        # Move the stripes by 0.8 pixels per frame
        self._animation_offset = (self._animation_offset + 0.8) % 16
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dimensions of the widget
        width = self.width()
        height = self.height()

        # Margin for glow shadow (draw shadow outside the bar track)
        margin = 5.0
        track_rect = QRectF(margin, margin, width - 2.0 * margin, height - 2.0 * margin)
        radius = track_rect.height() / 2.0

        # 1. Draw Outer Glow (if progress > 0)
        # Multiple passes of thin, semi-transparent outlines to build a smooth glow
        if self._value > 0:
            for i in range(4):
                glow_opacity = 35 - i * 8
                glow_width = 1.5 + i * 2.0
                glow_pen = QPen(QColor(56, 189, 248, int(glow_opacity)), glow_width)
                painter.setPen(glow_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(track_rect, radius, radius)

        # 2. Draw Background Track
        track_color = QColor(15, 23, 42, 230) # Very dark slate blue
        border_color = QColor(255, 255, 255, 10) # Faint track border
        
        painter.setPen(QPen(border_color, 1.2))
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_rect, radius, radius)

        # 3. Draw Progress Fill
        range_val = self._max - self._min
        if range_val <= 0:
            return
        
        percent = (self._value - self._min) / range_val
        if percent <= 0:
            return

        fill_width = track_rect.width() * percent
        # Ensure minimum width covers the rounded ends nicely
        if fill_width < track_rect.height():
            fill_width = track_rect.height()

        fill_rect = QRectF(track_rect.x(), track_rect.y(), fill_width, track_rect.height())

        # Clip painter to the rounded progress bar shape
        clip_path = QPainterPath()
        clip_path.addRoundedRect(fill_rect, radius, radius)
        painter.save()
        painter.setClipPath(clip_path)

        # Blue/Cyan gradient matching the design mockup
        gradient = QLinearGradient(fill_rect.left(), 0, fill_rect.right(), 0)
        gradient.setColorAt(0.0, QColor(29, 78, 216))    # deep blue
        gradient.setColorAt(0.5, QColor(37, 99, 235))    # vibrant blue
        gradient.setColorAt(1.0, QColor(56, 189, 248))   # cyan/light blue
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(fill_rect)

        # 4. Draw Animated Diagonal Stripes
        stripe_color = QColor(255, 255, 255, 35) # Subtle white stripes
        stripe_pen = QPen(stripe_color, 4) # 4px wide lines
        painter.setPen(stripe_pen)

        stripe_spacing = 16
        # Start far enough left to animate smoothly
        start_x = int(fill_rect.left() - track_rect.height() - self._animation_offset)
        end_x = int(fill_rect.right() + track_rect.height())

        for x in range(start_x, end_x, stripe_spacing):
            painter.drawLine(
                x, 
                int(fill_rect.bottom()), 
                x + int(fill_rect.height()), 
                int(fill_rect.top())
            )

        painter.restore()

        # 5. Accent inner glow border
        painter.setPen(QPen(QColor(56, 189, 248, 80), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(track_rect, radius, radius)

class SplashScreen(QWidget):
    loading_finished = Signal()
    progress_changed = Signal(int)

    def __init__(self, assets_dir: pathlib.Path | None = None) -> None:
        super().__init__()
        
        # Window Configuration
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if assets_dir is None:
            assets_dir = pathlib.Path(__file__).parent.parent / "assets"
        self._assets_dir = assets_dir

        # State tracking
        self._progress = 0
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        # Centered Layout
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        main_container = QWidget()
        main_container.setStyleSheet("background: transparent;")
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setFixedSize(920, 620)
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: rgba(11, 17, 32, 0.9);
                border: 1.5px solid rgba(59, 130, 246, 0.4);
                border-radius: 16px;
            }
        """)
        
        # Add subtle outer blue glow
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(35)
        self.glow.setColor(QColor("#2563EB"))
        self.glow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(self.glow)
        
        main_container_layout.addStretch()
        main_container_layout.addWidget(self.main_frame, alignment=Qt.AlignCenter)
        main_container_layout.addStretch()
        
        root_layout.addStretch()
        root_layout.addWidget(main_container, alignment=Qt.AlignCenter)
        root_layout.addStretch()

        # Container Layout inside the frame
        container_layout = QVBoxLayout(self.main_frame)
        container_layout.setContentsMargins(45, 35, 45, 35)
        container_layout.setSpacing(12)
        container_layout.addStretch()

        # ── Header Motor Logo ──
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        logo_path = self._assets_dir / "motor_logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_lbl.setPixmap(pixmap)
        else:
            self.logo_lbl.setText("⚙️")
            self.logo_lbl.setFont(QFont("Segoe UI", 48))
            self.logo_lbl.setStyleSheet("color: #3B82F6;")
            
        logo_glow = QGraphicsDropShadowEffect(self.logo_lbl)
        logo_glow.setBlurRadius(20)
        logo_glow.setColor(QColor("#3B82F6"))
        logo_glow.setOffset(0, 0)
        self.logo_lbl.setGraphicsEffect(logo_glow)
        container_layout.addWidget(self.logo_lbl)

        # ── Title ──
        self.title_lbl = QLabel("SMART <span style='color: #3B82F6;'>MOTOR</span> TEST BENCH")
        self.title_lbl.setFont(QFont("Segoe UI", 38, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.title_lbl)

        # ── Subtitle ──
        self.subtitle_lbl = QLabel("Real-Time Motor Performance Monitoring System")
        self.subtitle_lbl.setFont(QFont("Segoe UI", 13))
        self.subtitle_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        self.subtitle_lbl.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.subtitle_lbl)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border: none;")
        div1.setFixedHeight(1)
        container_layout.addWidget(div1)

        # ── Checklist Box ──
        self.status_box = QFrame()
        self.status_box.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.03);
                border-radius: 12px;
            }
        """)
        box_layout = QHBoxLayout(self.status_box)
        box_layout.setContentsMargins(25, 18, 25, 18)

        # 2-column checklist layout
        checklist_widget = QWidget()
        checklist_widget.setStyleSheet("background: transparent; border: none;")
        checklist_layout = QHBoxLayout(checklist_widget)
        checklist_layout.setContentsMargins(0, 0, 0, 0)
        checklist_layout.setSpacing(40)
        
        col1 = QWidget()
        col1_layout = QVBoxLayout(col1)
        col1_layout.setContentsMargins(0, 0, 0, 0)
        col1_layout.setSpacing(6)
        
        col2 = QWidget()
        col2_layout = QVBoxLayout(col2)
        col2_layout.setContentsMargins(0, 0, 0, 0)
        col2_layout.setSpacing(6)

        self.checks = [
            ("Initializing User Interface", QLabel("🖥️"), QLabel("⏳")),
            ("Loading Theme", QLabel("🎨"), QLabel("⏳")),
            ("Loading Application Resources", QLabel("📦"), QLabel("⏳")),
            ("Initializing Graph Engine", QLabel("📈"), QLabel("⏳")),
            ("Loading Data Logger", QLabel("💾"), QLabel("⏳")),
            ("Loading User Settings", QLabel("⚙️"), QLabel("⏳")),
            ("Preparing Dashboard", QLabel("📊"), QLabel("⏳")),
            ("Launching Smart Motor Test Bench", QLabel("🚀"), QLabel("⏳")),
        ]

        for idx, (text, icon, status) in enumerate(self.checks):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            icon.setStyleSheet("color: #64748B; font-size: 14px;")
            status.setStyleSheet("color: #64748B; font-size: 14px;")

            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet("color: #94A3B8;")

            row_layout.addWidget(icon)
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(status)
            
            if idx < 4:
                col1_layout.addWidget(row)
            else:
                col2_layout.addWidget(row)

        checklist_layout.addWidget(col1)
        checklist_layout.addWidget(col2)
        box_layout.addWidget(checklist_widget)
        container_layout.addWidget(self.status_box)

        # ── Percentage Label centered above Progress Bar ──
        self.percentage_lbl = QLabel("0%")
        self.percentage_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.percentage_lbl.setStyleSheet("color: #38BDF8; background: transparent; border: none;")
        self.percentage_lbl.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.percentage_lbl)

        # ── Custom Glowing Striped Progress Bar ──
        self.progress_bar = StripedProgressBar()
        self.progress_bar.setFixedHeight(32)
        container_layout.addWidget(self.progress_bar)

        # ── Status Label centered below Progress Bar ──
        self.status_lbl = QLabel("Initializing Application...")
        self.status_lbl.setFont(QFont("Segoe UI", 11))
        self.status_lbl.setStyleSheet("color: #8EA6C9; border: none; background: transparent;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.status_lbl)

        # ── Footer Info ──
        footer_layout = QHBoxLayout()
        self.ver_lbl = QLabel("Version 1.0.0")
        self.ver_lbl.setFont(QFont("Segoe UI", 9))
        self.ver_lbl.setStyleSheet("color: #475569; border: none; background: transparent;")

        self.copy_lbl = QLabel("© 2026")
        self.copy_lbl.setFont(QFont("Segoe UI", 9))
        self.copy_lbl.setStyleSheet("color: #475569; border: none; background: transparent;")

        footer_layout.addWidget(self.ver_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_lbl)
        container_layout.addLayout(footer_layout)
        container_layout.addStretch()

        # Simulated progress timer (25ms * 100 = 2500ms total)
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._update_progress)
        self.sim_timer.start(25)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Dark Navy Background
        painter.fillRect(self.rect(), QColor(8, 12, 24))
        
        # 2. Subtle Blueprint Grid (5% opacity blue)
        painter.setPen(QPen(QColor(59, 130, 246, 12), 1))
        grid_size = 40
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
            
        # 3. Large Blueprint Cog/Motor in Background (8% opacity)
        logo_pen = QPen(QColor(59, 130, 246, 18), 2)
        painter.setPen(logo_pen)
        painter.setBrush(Qt.NoBrush)
        
        center = self.rect().center()
        center_y = center.y() - 100
        center_pt = QPoint(center.x(), center_y)
        
        # Concentric circles
        painter.drawEllipse(center_pt, 140, 140)
        painter.drawEllipse(center_pt, 110, 110)
        painter.drawEllipse(center_pt, 80, 80)
        painter.drawEllipse(center_pt, 30, 30)
        
        # Main Crosshairs
        painter.drawLine(center_pt.x() - 180, center_pt.y(), center_pt.x() + 180, center_pt.y())
        painter.drawLine(center_pt.x(), center_pt.y() - 180, center_pt.x(), center_pt.y() + 180)
        
        # Diagonal spokes
        for angle in (45, 135, 225, 315):
            rad = math.radians(angle)
            dx = int(170 * math.cos(rad))
            dy = int(170 * math.sin(rad))
            painter.drawLine(center_pt.x(), center_pt.y(), center_pt.x() + dx, center_pt.y() + dy)
            
        # Cog teeth (12 teeth outer perimeter)
        num_teeth = 12
        tooth_w = 22
        tooth_h = 16
        for i in range(num_teeth):
            angle = (360 / num_teeth) * i
            rad = math.radians(angle)
            bx = center_pt.x() + 140 * math.cos(rad)
            by = center_pt.y() + 140 * math.sin(rad)
            tx = center_pt.x() + 156 * math.cos(rad)
            ty = center_pt.y() + 156 * math.sin(rad)
            
            px = -math.sin(rad)
            py = math.cos(rad)
            
            p1 = QPoint(int(bx - (tooth_w/2) * px), int(by - (tooth_w/2) * py))
            p2 = QPoint(int(tx - (tooth_w/3) * px), int(ty - (tooth_w/3) * py))
            p3 = QPoint(int(tx + (tooth_w/3) * px), int(ty + (tooth_w/3) * py))
            p4 = QPoint(int(bx + (tooth_w/2) * px), int(by + (tooth_w/2) * py))
            
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)
            painter.drawLine(p3, p4)

        super().paintEvent(event)

    def _update_progress(self) -> None:
        self._progress += 1
        if self._progress > 100:
            self._progress = 100
            self.sim_timer.stop()
            self.loading_finished.emit()
            return

        self.progress_bar.setValue(self._progress)
        self.percentage_lbl.setText(f"{self._progress}%")
        self.progress_changed.emit(self._progress)

        # Synchronize active loading steps
        if self._progress <= 10:
            active_idx = 0
        elif self._progress <= 25:
            active_idx = 1
        elif self._progress <= 40:
            active_idx = 2
        elif self._progress <= 55:
            active_idx = 3
        elif self._progress <= 62:
            active_idx = 4
        elif self._progress <= 70:
            active_idx = 5
        elif self._progress <= 85:
            active_idx = 6
        else:
            active_idx = 7

        dots = "." * (1 + (self._progress % 3))

        for idx, (text, icon, status_lbl) in enumerate(self.checks):
            # Completed steps
            if idx < active_idx:
                status_lbl.setText("✓")
                status_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 14px;")
                icon.setStyleSheet("color: #10B981; font-size: 14px;")
            # Active step
            elif idx == active_idx and self._progress < 100:
                status_lbl.setText(dots)
                status_lbl.setStyleSheet("color: #3B82F6; font-weight: bold; font-size: 14px;")
                icon.setStyleSheet("color: #3B82F6; font-size: 14px;")
            # Waiting steps
            else:
                if self._progress >= 100:
                    status_lbl.setText("✓")
                    status_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 14px;")
                    icon.setStyleSheet("color: #10B981; font-size: 14px;")
                else:
                    status_lbl.setText(" ")
                    status_lbl.setStyleSheet("color: #64748B; font-size: 14px;")
                    icon.setStyleSheet("color: #64748B; font-size: 14px;")

        # Update status label above progress bar
        if self._progress < 100:
            self.status_lbl.setText(self.checks[active_idx][0] + "...")
        else:
            self.status_lbl.setText("Ready")
