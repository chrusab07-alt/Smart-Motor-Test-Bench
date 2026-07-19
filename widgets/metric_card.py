"""
metric_card.py
--------------
Compact, modern monitoring cards for industrial dashboard.

Each card displays:
1. Colored icon on the left inside a circular background badge.
2. Metric title at the top right of the badge.
3. Large current value in bold with measurement unit.
4. Small percentage change below the value with ▲/▼ indicator.
5. Bottom row displaying Maximum value (left) and Minimum value (right).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QRect, QVariantAnimation, QEasingCurve, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)


class _CircularIconBadge(QWidget):
    """
    Circular icon badge with dark translucent accent-tinted background
    and vector graphics for industrial KPI metrics.
    """

    def __init__(self, icon_type: str, accent: str, size: int = 30, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_type = icon_type.lower()
        self._accent = QColor(accent)
        self._size = size
        self.setFixedSize(size, size)

    def set_accent_color(self, accent: str) -> None:
        self._accent = QColor(accent)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(1, 1, self._size - 2, self._size - 2)

        # Circular dark container with accent tint
        bg = QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 32)
        border = QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 90)

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1.2))
        painter.drawEllipse(rect)

        cx, cy = rect.center().x(), rect.center().y()
        w, h = rect.width(), rect.height()

        pen = QPen(self._accent, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        if "voltage" in self._icon_type or self._icon_type == "⚡":
            # Lightning Bolt
            path = QPainterPath()
            path.moveTo(cx + 1, cy - h * 0.35)
            path.lineTo(cx - w * 0.26, cy + h * 0.04)
            path.lineTo(cx - w * 0.02, cy + h * 0.04)
            path.lineTo(cx - w * 0.12, cy + h * 0.35)
            path.lineTo(cx + w * 0.26, cy - h * 0.04)
            path.lineTo(cx + w * 0.02, cy - h * 0.04)
            path.closeSubpath()
            painter.setBrush(QBrush(self._accent))
            painter.drawPath(path)

        elif "current" in self._icon_type or self._icon_type in ("a", "↯"):
            # Capital 'A' for Current
            font = QFont("Segoe UI", int(self._size * 0.44), QFont.Bold)
            painter.setFont(font)
            painter.setPen(self._accent)
            painter.drawText(self.rect(), Qt.AlignCenter, "A")

        elif "rpm" in self._icon_type or "speed" in self._icon_type or self._icon_type == "⊙":
            # Speedometer Gauge Icon
            gauge_rect = QRectF(cx - w * 0.32, cy - h * 0.32, w * 0.64, h * 0.64)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(gauge_rect, -30 * 16, 240 * 16)
            # Needle
            needle_pen = QPen(self._accent, 2.2, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(needle_pen)
            painter.drawLine(QPointF(cx, cy + h * 0.08), QPointF(cx + w * 0.22, cy - h * 0.22))
            # Pivot dot
            painter.setBrush(QBrush(self._accent))
            dot_size = self._size * 0.12
            painter.drawEllipse(QRectF(cx - dot_size/2, cy + h * 0.05, dot_size, dot_size))

        elif "power" in self._icon_type or self._icon_type == "⚛":
            # Pulse / ECG Wave
            path = QPainterPath()
            x0 = cx - w * 0.35
            path.moveTo(x0, cy)
            path.lineTo(x0 + w * 0.14, cy)
            path.lineTo(x0 + w * 0.28, cy - h * 0.28)
            path.lineTo(x0 + w * 0.42, cy + h * 0.28)
            path.lineTo(x0 + w * 0.56, cy - h * 0.12)
            path.lineTo(x0 + w * 0.70, cy)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        elif "temp" in self._icon_type or self._icon_type == "🌡":
            # Thermometer
            painter.setBrush(Qt.NoBrush)
            tw = w * 0.17
            tube = QRectF(cx - tw/2, cy - h * 0.3, tw, h * 0.42)
            painter.drawRoundedRect(tube, tw/2, tw/2)
            bw = w * 0.3
            bulb = QRectF(cx - bw/2, cy + h * 0.05, bw, bw)
            painter.setBrush(QBrush(self._accent))
            painter.drawEllipse(bulb)
            fill_w = tw * 0.55
            painter.fillRect(QRectF(cx - fill_w/2, cy - h * 0.15, fill_w, h * 0.25), QBrush(self._accent))

        elif "eff" in self._icon_type or self._icon_type == "◎":
            # Efficiency Bar Chart with Rising Trend Line
            bw = w * 0.09
            bx0 = cx - w * 0.28
            by_base = cy + h * 0.25
            painter.setBrush(QBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 160)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(bx0, by_base - h * 0.18, bw, h * 0.18))
            painter.drawRect(QRectF(bx0 + w * 0.16, by_base - h * 0.34, bw, h * 0.34))
            painter.drawRect(QRectF(bx0 + w * 0.32, by_base - h * 0.50, bw, h * 0.50))

            arrow_pen = QPen(self._accent, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(arrow_pen)
            arr = QPainterPath()
            arr.moveTo(bx0, cy)
            arr.lineTo(bx0 + w * 0.16, cy - h * 0.16)
            arr.lineTo(bx0 + w * 0.40, cy - h * 0.32)
            painter.drawPath(arr)

            # Arrow head
            head = QPainterPath()
            head.moveTo(bx0 + w * 0.27, cy - h * 0.32)
            head.lineTo(bx0 + w * 0.40, cy - h * 0.32)
            head.lineTo(bx0 + w * 0.40, cy - h * 0.20)
            painter.drawPath(head)

        else:
            font = QFont("Segoe UI Symbol", int(self._size * 0.44), QFont.Bold)
            painter.setFont(font)
            painter.setPen(self._accent)
            painter.drawText(self.rect(), Qt.AlignCenter, self._icon_type)

        painter.end()


class MetricCard(QWidget):
    """
    KPI Monitoring Card for industrial dashboards.
    """

    from PySide6.QtCore import Signal
    clicked = Signal(str)
    _ANIM_STEPS: int = 16

    def __init__(
        self,
        title: str,
        unit: str,
        icon_char: str,
        accent: str,
        parent: QWidget | None = None,
        decimals: int | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title
        self._unit = unit
        self._icon_char = icon_char
        self._accent = accent
        self._decimals = decimals

        # Display title mapping for exact visual match
        self._display_title = "RPM" if title in ("Speed (RPM)", "RPM") else title

        # Internal value tracking
        self._display_value: float = 0.0
        self._start_value: float = 0.0
        self._target_value: float = 0.0
        self._max_val: float = 0.0
        self._min_val: float = float("inf")

        self._anim_step: int = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._animate_step)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(180)
        self.setMinimumHeight(120)
        self.setCursor(Qt.PointingHandCursor)

        # Soft drop shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(16)
        self._shadow.setOffset(0, 6)
        self._shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(self._shadow)

        # Hover animation state
        self._hover_progress: float = 0.0
        self._is_hovered: bool = False
        self._base_geom: QRect | None = None

        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_anim.valueChanged.connect(self._on_hover_anim_step)

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(3)

        # ── 1. Top Row: Circular Icon Badge + Metric Title ─────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        icon_type = self._icon_char
        if self._title in ("Speed (RPM)", "RPM"):
            icon_type = "rpm"
        elif self._title == "Voltage":
            icon_type = "voltage"
        elif self._title == "Current":
            icon_type = "current"
        elif self._title == "Power":
            icon_type = "power"
        elif self._title == "Efficiency":
            icon_type = "efficiency"
        elif self._title == "Temperature":
            icon_type = "temp"

        self._icon_badge = _CircularIconBadge(icon_type, self._accent, size=30)
        top_row.addWidget(self._icon_badge, alignment=Qt.AlignVCenter)

        self._title_lbl = QLabel(self._display_title)
        self._title_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._title_lbl.setStyleSheet("color: #E2E8F0; border: none; background: transparent;")
        top_row.addWidget(self._title_lbl, alignment=Qt.AlignVCenter)
        top_row.addStretch()

        root.addLayout(top_row)

        # ── 2. Value Row: Large bold current value + Unit ──────────────
        val_row = QHBoxLayout()
        val_row.setContentsMargins(0, 0, 0, 0)
        val_row.setSpacing(6)
        val_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._value_lbl = QLabel("0.0")
        self._value_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self._value_lbl.setStyleSheet("color: #FFFFFF; font-weight: 800; border: none; background: transparent;")

        self._unit_lbl = QLabel(self._unit)
        self._unit_lbl.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        self._unit_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")

        val_row.addWidget(self._value_lbl)
        val_row.addWidget(self._unit_lbl)
        val_row.addStretch()

        root.addLayout(val_row)

        # ── 3. Trend Row: ▲ +2.45% ─────────────────────────────────────
        self._trend_lbl = QLabel("▲ +0.00%")
        trend_font = QFont("Segoe UI")
        trend_font.setPixelSize(12)
        trend_font.setBold(True)
        self._trend_lbl.setFont(trend_font)
        self._trend_lbl.setStyleSheet("color: #10B981; border: none; background: transparent;")
        root.addWidget(self._trend_lbl, alignment=Qt.AlignLeft)

        # ── 4. Horizontal Divider Line ────────────────────────────────
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); border: none;")
        root.addWidget(divider)

        # ── 5. Bottom Row: Max (left) and Min (right) ──────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(0)

        self._max_lbl = QLabel("Max: 0.0")
        self._max_lbl.setFont(QFont("Segoe UI", 7))
        self._max_lbl.setStyleSheet("color: rgba(100, 116, 139, 0.7); border: none; background: transparent;")

        self._min_lbl = QLabel("Min: 0.0")
        self._min_lbl.setFont(QFont("Segoe UI", 7))
        self._min_lbl.setStyleSheet("color: rgba(100, 116, 139, 0.7); border: none; background: transparent;")
        self._min_lbl.setAlignment(Qt.AlignRight)

        bottom_row.addWidget(self._max_lbl)
        bottom_row.addStretch()
        bottom_row.addWidget(self._min_lbl)

        root.addLayout(bottom_row)

    def _apply_style(self) -> None:
        self.setStyleSheet("background: transparent; border: none;")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._title)
        super().mousePressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self._is_hovered:
            self._base_geom = self.geometry()

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        if self._base_geom is None or not self.geometry().contains(self._base_geom.center()):
            self._base_geom = self.geometry()
        self.update()
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self.update()
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        radius = 12.0 # 12-14 px rounded corners

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Blend background color based on hover progress
        val = self._hover_progress
        bg1 = QColor("#0E1626")
        bg2 = QColor("#121C2F")
        bg_r = int(bg1.red() + (bg2.red() - bg1.red()) * val)
        bg_g = int(bg1.green() + (bg2.green() - bg1.green()) * val)
        bg_b = int(bg1.blue() + (bg2.blue() - bg1.blue()) * val)
        bg_color = QColor(bg_r, bg_g, bg_b)

        painter.fillPath(path, QBrush(bg_color))

        # Draw top thin accent line matching metric color
        painter.save()
        painter.setClipPath(path)
        accent_color = QColor(self._accent)
        painter.fillRect(QRectF(0, 0, self.width(), 3), QBrush(accent_color))
        painter.restore()

        # Blend border color based on hover progress
        c1 = QColor(255, 255, 255, 20)
        c2 = QColor(self._accent)
        r = int(c1.red() + (c2.red() - c1.red()) * val)
        g = int(c1.green() + (c2.green() - c1.green()) * val)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * val)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * val)
        border_color = QColor(r, g, b, a)

        painter.setPen(QPen(border_color, 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.end()

    def _on_hover_anim_step(self, val: float) -> None:
        self._hover_progress = val
        if hasattr(self, "_shadow"):
            blur = 16 + int((32 - 16) * val)
            offset_y = 6 + int((10 - 6) * val)
            self._shadow.setBlurRadius(blur)
            self._shadow.setOffset(0, offset_y)
            c_base = QColor(0, 0, 0, 160)
            c_accent = QColor(self._accent)
            r = int(c_base.red() + (c_accent.red() - c_base.red()) * val * 0.4)
            g = int(c_base.green() + (c_accent.green() - c_base.green()) * val * 0.4)
            b = int(c_base.blue() + (c_accent.blue() - c_base.blue()) * val * 0.4)
            a = int(c_base.alpha() + (140 - c_base.alpha()) * val)
            self._shadow.setColor(QColor(r, g, b, a))

        if self._base_geom and self._base_geom.isValid():
            dw = int(self._base_geom.width() * 0.02 * val)
            dh = int(self._base_geom.height() * 0.02 * val)
            new_geom = QRect(
                self._base_geom.x() - dw // 2,
                self._base_geom.y() - dh // 2,
                self._base_geom.width() + dw,
                self._base_geom.height() + dh,
            )
            self.setGeometry(new_geom)
        self.update()

    # ------------------------------------------------------------------ #
    #  Public API (Compatibility Guaranteed)
    # ------------------------------------------------------------------ #
    def set_gauge_max(self, max_val: float) -> None:
        """Compatibility method."""
        pass

    def set_value(self, value: float) -> None:
        """Smoothly animate toward new target value and update stats."""
        if self._title == "Temperature":
            if value < 40.0:
                new_accent = "#10B981"  # Green
            elif value <= 60.0:
                new_accent = "#F59E0B"  # Yellow
            else:
                new_accent = "#EF4444"  # Red
                
            if new_accent != self._accent:
                self._accent = new_accent
                self._icon_badge.set_accent_color(new_accent)
                self.update()

        prev = self._target_value
        self._target_value = value

        # Percentage change calculation
        diff = value - prev
        if prev != 0.0:
            pct = (diff / abs(prev)) * 100.0
        else:
            pct = 0.0

        if diff > 0.001:
            self._trend_lbl.setText(f"▲ +{pct:.2f}%")
            self._trend_lbl.setStyleSheet("color: #10B981; font-weight: bold; border: none; background: transparent;")
        elif diff < -0.001:
            self._trend_lbl.setText(f"▼ {pct:.2f}%")
            self._trend_lbl.setStyleSheet("color: #EF4444; font-weight: bold; border: none; background: transparent;")
        else:
            self._trend_lbl.setText("▲ +0.00%")
            self._trend_lbl.setStyleSheet("color: #64748B; font-weight: bold; border: none; background: transparent;")

        # Update stats
        self._max_val = max(self._max_val, value)
        if self._min_val == float("inf"):
            self._min_val = value
        else:
            self._min_val = min(self._min_val, value)

        self._update_stats_labels()

        # Start animation step
        self._start_value = self._display_value
        self._anim_step = 0
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def reset_statistics(self) -> None:
        self._max_val = self._target_value
        self._min_val = self._target_value
        self._update_stats_labels()

    # ------------------------------------------------------------------ #
    #  Animation & formatting helpers
    # ------------------------------------------------------------------ #
    def _animate_step(self) -> None:
        self._anim_step += 1
        t = min(self._anim_step / self._ANIM_STEPS, 1.0)
        t_ease = 1.0 - (1.0 - t) ** 3
        self._display_value = self._start_value + (self._target_value - self._start_value) * t_ease
        self._refresh_value_label()
        if self._anim_step >= self._ANIM_STEPS:
            self._display_value = self._target_value
            self._refresh_value_label()
            self._anim_timer.stop()

    def _refresh_value_label(self) -> None:
        val = self._display_value
        if self._decimals is not None:
            text = f"{val:.{self._decimals}f}"
        elif abs(val) >= 1000:
            text = f"{val:,.1f}" if val % 1 != 0 else f"{val:,.0f}"
        elif abs(val) >= 10:
            text = f"{val:.2f}"
        else:
            text = f"{val:.2f}"
        self._value_lbl.setText(text)

    def _update_stats_labels(self) -> None:
        def fmt(v: float) -> str:
            if self._decimals is not None:
                return f"{v:.{self._decimals}f}"
            return f"{v:,.2f}" if abs(v) < 100 else f"{v:,.1f}"

        max_str = fmt(self._max_val)
        min_v = self._min_val if self._min_val != float("inf") else 0.0
        min_str = fmt(min_v)

        unit_str = f" {self._unit}" if self._unit else ""
        self._max_lbl.setText(f"Max: {max_str}{unit_str}")
        self._min_lbl.setText(f"Min: {min_str}{unit_str}")
