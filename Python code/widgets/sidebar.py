"""
sidebar.py
----------
Collapsible navigation sidebar widget for the Smart Motor Test Bench.
Includes a custom vector motor graphic and industrial SCADA styled buttons.
"""

from __future__ import annotations
import math

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRectF, Property, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy,
)

class MotorVectorRender(QWidget):
    """
    Custom QPainter widget drawing an industrial schematic of a motor.
    Uses vector operations so it scales perfectly and requires no image files.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(80)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Background
        painter.setBrush(QColor("#0B1120"))
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

        # Draw a technical motor schematic
        pen = QPen(QColor("#007ACC"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        center_x = rect.width() / 2
        center_y = rect.height() / 2
        radius = 24

        # Outer casing
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        # Inner shaft
        painter.drawEllipse(QPointF(center_x, center_y), 5, 5)

        # Cooling fins
        for i in range(8):
            angle = i * (360 / 8)
            rad_angle = angle * math.pi / 180
            x1 = center_x + math.cos(rad_angle) * radius
            y1 = center_y + math.sin(rad_angle) * radius
            x2 = center_x + math.cos(rad_angle) * (radius + 5)
            y2 = center_y + math.sin(rad_angle) * (radius + 5)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Mount base
        painter.drawRect(int(center_x - 20), int(center_y + radius + 4), 40, 5)
        
        # Add tech grid overlay
        grid_pen = QPen(QColor("#111827"))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)
        painter.setPen(grid_pen)
        for x in range(0, int(rect.width()), 20):
            painter.drawLine(x, 0, x, int(rect.height()))
        for y in range(0, int(rect.height()), 20):
            painter.drawLine(0, y, int(rect.width()), y)

        painter.end()


class _SidebarButton(QPushButton):
    """
    A custom animated sidebar button with solid geometric highlights
    fitting an industrial SCADA application.
    """
    def __init__(self, icon_char: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_char = icon_char
        self._label = label
        
        self._hover_progress: float = 0.0
        self._active: bool = False
        
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animations
        self._hover_anim = QPropertyAnimation(self, b"hover_progress")
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.OutQuad)
        
    def _get_hover(self) -> float:
        return self._hover_progress

    def _set_hover(self, val: float) -> None:
        self._hover_progress = val
        self.update()

    hover_progress = Property(float, _get_hover, _set_hover)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def enterEvent(self, event) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Color definitions
        active_bg = QColor("#007ACC")
        hover_bg = QColor("#3F3F46")
        
        # 1. Background — rounded when hovered or active
        inner = rect.adjusted(6, 4, -6, -4)
        radius = 12
        if self._active:
            painter.setBrush(QColor("#0F62FE"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(inner, radius, radius)
            # subtle outer glow
            glow_pen = QPen(QColor(15,98,254,40))
            glow_pen.setWidth(8)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(inner.adjusted(0,0,0,0), radius, radius)
        elif self._hover_progress > 0:
            bg_color = QColor(30, 41, 59, int(255 * self._hover_progress))
            painter.setBrush(bg_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(inner, radius, radius)
            
        # 2. Left indicator (solid accent)
        if self._active:
            indicator_rect = QRectF(inner.left() + 8, inner.top() + 6, 4, inner.height() - 12)
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(indicator_rect, 2, 2)
            
        # 3. Content
        content_color = QColor("#FFFFFF") if self._active else QColor("#A8B3C5")
        if not self._active and self._hover_progress > 0:
            content_color = QColor("#FFFFFF")
            
        # Draw icon (slightly larger size: 16pt)
        painter.setFont(QFont("Segoe UI Symbol", 16))
        painter.setPen(content_color)
        painter.drawText(inner.adjusted(16, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, self._icon_char)
        
        # Draw label (Segoe UI Bold 10pt)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(inner.adjusted(44, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, self._label)
        
        painter.end()


class Sidebar(QWidget):
    """
    Left-hand navigation sidebar.
    Emits page_changed with the zero-based page index when the user clicks a navigation button.
    """
    page_changed = Signal(int)

    # (unicode icon, label) pairs for each navigation entry
    _NAV_ITEMS: list[tuple[str, str]] = [
        ("⊞",  "Dashboard"),
        ("📈",  "Live Graphs"),
        ("📋",  "Data Logger"),
        ("⚙",  "Control Panel"),
        ("⚖",  "Calibration"),
        ("🛠",  "Settings"),
        ("🛈",  "About"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        self._buttons: list[_SidebarButton] = []
        self._active_index: int = 0
        
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 10, 0, 10)
        root.setSpacing(4)

        # Branding block removed per user request
        root.addSpacing(4)

        # Navigation buttons
        for idx, (icon, label) in enumerate(self._NAV_ITEMS):
            btn = _SidebarButton(icon, label)
            btn.clicked.connect(lambda checked=False, i=idx: self._on_nav_click(i))
            self._buttons.append(btn)
            root.addWidget(btn)

        root.addStretch()

        # Premium motor graphic card
        graphic_card = QFrame()
        graphic_card.setObjectName("sidebarCard")
        graphic_card.setStyleSheet("""
            #sidebarCard {
                background-color: #0B1120;
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 12px;
                margin: 4px 12px 10px 12px;
            }
        """)
        
        card_layout = QVBoxLayout(graphic_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        self.motor_graphic = QLabel()
        from pathlib import Path
        from PySide6.QtGui import QPixmap, QImage
        from PySide6.QtCore import QRect
        logo_path = Path(__file__).parent.parent / "assets" / "motor_logo.png"
        if logo_path.exists():
            img = QImage(str(logo_path))
            cropped = img.copy(QRect(26, 0, 645, 627))
            pix = QPixmap.fromImage(cropped).scaledToWidth(226, Qt.SmoothTransformation)
            self.motor_graphic.setPixmap(pix)
            self.motor_graphic.setAlignment(Qt.AlignCenter)
            self.motor_graphic.setFixedSize(226, pix.height())
        else:
            self.motor_graphic.setFixedSize(226, 219)

        self.motor_graphic.setStyleSheet("background: transparent; border: none; border-radius: 11px;")
        card_layout.addWidget(self.motor_graphic, alignment=Qt.AlignCenter)
        
        root.addWidget(graphic_card)

        # Footer removed per user request
        
        # Set initial active button
        self._set_active(0)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            Sidebar {
                background-color: #090F1E;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)

    def _on_nav_click(self, index: int) -> None:
        self._set_active(index)
        self.page_changed.emit(index)

    def _set_active(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self._active_index = index

    def set_active_page(self, index: int) -> None:
        """Programmatically activate a page button (no signal emitted)."""
        self._set_active(index)
