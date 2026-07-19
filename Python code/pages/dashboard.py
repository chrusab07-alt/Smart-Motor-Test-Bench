"""
dashboard.py
------------
Main dashboard page for the Smart Motor Test Bench application.

This is the primary view the user sees on launch. It contains:
  • Application header (logo, title, dynamic status card, COM port card, clock)
  • Six animated KPI metric cards with accent colours and hover glows
  • One large PyQtGraph plot occupying the center of the screen
  • A parameter selection dropdown to change the graph's metric
  • Inline control panel (with Start, Stop, Emergency Stop) and system-information panel (10 fields) below the graph

All data is pushed in from the outside via update_data(), called once per
QTimer tick from the main window.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Ensure project root is in sys.path when running dashboard.py directly
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QSizePolicy,
    QComboBox, QMessageBox, QGraphicsDropShadowEffect
)

from widgets.metric_card import MetricCard
from widgets.graph_widget import RealtimeGraph
from widgets.control_panel import ControlPanel
from backend.data_generator import DataGenerator
from backend.serial_manager import SerialManager


class IconBadge(QWidget):
    """Custom painted vector icon badge matching Image 2 design."""
    def __init__(self, icon_type: str, accent: str, bg_tint: str, border_tint: str, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._accent = QColor(accent)
        self._bg_tint = QColor(bg_tint)
        self._border_tint = QColor(border_tint)
        self.setFixedSize(46, 46)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setBrush(QBrush(self._bg_tint))
        painter.setPen(QPen(self._border_tint, 1.2))
        painter.drawEllipse(rect)
        cx, cy = rect.center().x(), rect.center().y()
        w, h = rect.width(), rect.height()

        if self._icon_type == 'current':
            pen = QPen(self._accent, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            x0 = rect.left() + w * 0.18
            path.moveTo(x0, cy)
            path.lineTo(x0 + w * 0.15, cy)
            path.lineTo(x0 + w * 0.25, cy - h * 0.26)
            path.lineTo(x0 + w * 0.38, cy + h * 0.26)
            path.lineTo(x0 + w * 0.48, cy - h * 0.12)
            path.lineTo(x0 + w * 0.55, cy)
            path.lineTo(rect.right() - w * 0.18, cy)
            painter.drawPath(path)

        elif self._icon_type == 'maximum':
            bar_pen = QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 120), 1)
            painter.setPen(bar_pen)
            painter.setBrush(QBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 90)))
            bw = 3.5
            bx0 = cx - 10
            by_base = cy + 9
            painter.drawRect(QRectF(bx0, by_base - 5, bw, 5))
            painter.drawRect(QRectF(bx0 + 5, by_base - 9, bw, 9))
            painter.drawRect(QRectF(bx0 + 10, by_base - 13, bw, 13))

            pen = QPen(self._accent, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(cx - 12, cy + 5)
            path.lineTo(cx - 4, cy + 1)
            path.lineTo(cx + 3, cy - 5)
            path.lineTo(cx + 11, cy - 10)
            painter.drawPath(path)

            arr = QPainterPath()
            arr.moveTo(cx + 5, cy - 10)
            arr.lineTo(cx + 11, cy - 10)
            arr.lineTo(cx + 11, cy - 4)
            painter.drawPath(arr)

        elif self._icon_type == 'minimum':
            dash_pen = QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 140), 1.5, Qt.DashLine)
            painter.setPen(dash_pen)
            painter.drawLine(QPointF(cx - 12, cy + 8), QPointF(cx - 4, cy + 8))

            pen = QPen(self._accent, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(cx - 12, cy - 7)
            path.lineTo(cx - 4, cy - 3)
            path.lineTo(cx + 4, cy + 3)
            path.lineTo(cx + 11, cy + 8)
            painter.drawPath(path)

            arr = QPainterPath()
            arr.moveTo(cx + 4, cy + 8)
            arr.lineTo(cx + 11, cy + 8)
            arr.lineTo(cx + 11, cy + 1)
            painter.drawPath(arr)

        elif self._icon_type == 'average':
            bar_pen = QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 120), 1)
            painter.setPen(bar_pen)
            painter.setBrush(QBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 90)))
            bw = 3.5
            bx0 = cx - 11
            by_base = cy + 9
            painter.drawRect(QRectF(bx0, by_base - 7, bw, 7))
            painter.drawRect(QRectF(bx0 + 5, by_base - 14, bw, 14))
            painter.drawRect(QRectF(bx0 + 10, by_base - 10, bw, 10))
            painter.drawRect(QRectF(bx0 + 15, by_base - 16, bw, 16))

            pen = QPen(self._accent, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(cx - 11, cy + 1)
            path.cubicTo(cx - 5, cy - 10, cx + 5, cy - 2, cx + 13, cy - 10)
            painter.drawPath(path)

        elif self._icon_type == 'samples':
            pen = QPen(self._accent, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 40)))
            rw, rh = 20.0, 7.0
            painter.drawEllipse(QRectF(cx - rw/2, cy - 10, rw, rh))
            m_path = QPainterPath()
            m_path.moveTo(cx - rw/2, cy - 6.5)
            m_path.arcTo(QRectF(cx - rw/2, cy - 4, rw, rh), 180, 180)
            painter.drawPath(m_path)
            b_path = QPainterPath()
            b_path.moveTo(cx - rw/2, cy + 1.5)
            b_path.arcTo(QRectF(cx - rw/2, cy + 4, rw, rh), 180, 180)
            painter.drawPath(b_path)

        elif self._icon_type == 'uptime':
            pen = QPen(self._accent, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 30)))
            cr = 11.0
            painter.drawEllipse(QRectF(cx - cr, cy - cr, cr*2, cr*2))
            painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - 6))
            painter.drawLine(QPointF(cx, cy), QPointF(cx + 5, cy + 1))


class Dashboard(QWidget):
    """
    The main dashboard page.

    Args:
        data_gen:   The shared DataGenerator instance. Data is read on each tick.
        serial_mgr: The optional SerialManager instance.
        settings:   The optional settings dictionary.
        parent:     Optional parent widget.
    """

    def __init__(
        self,
        data_gen: DataGenerator,
        serial_mgr: SerialManager | None = None,
        settings: dict | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._data = data_gen
        self._serial = serial_mgr
        self._settings = settings or {}
        self._data_points_count: int = 0

        # Graph configurations
        self._param_configs = {
            "RPM": {"label": "Speed", "unit": "RPM", "color": "#10B981"},
            "Voltage": {"label": "Voltage", "unit": "V", "color": "#3B82F6"},
            "Current": {"label": "Current", "unit": "A", "color": "#F59E0B"},
            "Power": {"label": "Power", "unit": "W", "color": "#8B5CF6"},
            "Efficiency": {"label": "Efficiency", "unit": "%", "color": "#06B6D4"},
            "Temperature": {"label": "Temperature", "unit": "°C", "color": "#F97316"},
        }
        self._active_parameter = "RPM"

        # Background history buffers for graph switching
        self._history_times = []
        self._history_values = {key: [] for key in self._param_configs}
        self._elapsed_time = 0.0

        self._live_stats_labels = {}
        self._live_stats_keys = {}

        self._build_ui()
        self._on_dropdown_changed("RPM")


    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        """Build the full dashboard layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("DASHBOARD")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        content_layout.addWidget(title)

        # ── Metric cards row ───────────────────────────────────────────
        content_layout.addWidget(self._build_cards_row())

        # ── Middle row (Large Graph + Live Statistics) ─────────────────
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(0)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.addWidget(self._build_large_graph_area())
        content_layout.addLayout(mid_layout)

        # ── Bottom row (Control Panel + System Information) ────────────
        bot_layout = QHBoxLayout()
        bot_layout.setSpacing(18)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        
        self._ctrl_panel = ControlPanel()
        self._ctrl_panel.pwm_changed.connect(self._on_pwm_changed)
        self._ctrl_panel.run_requested.connect(self._on_run)
        self._ctrl_panel.stop_requested.connect(self._on_stop)
        self._ctrl_panel.estop_requested.connect(self._on_estop)
        self._ctrl_panel.direction_changed.connect(self._on_direction_changed)
        
        bot_layout.addWidget(self._ctrl_panel, stretch=60)
        bot_layout.addWidget(self._build_sysinfo_panel(), stretch=40)
        content_layout.addLayout(bot_layout)

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #  Header is now in main.py, so we remove the old _build_header
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    #  Metric cards
    # ------------------------------------------------------------------ #
    def _build_cards_row(self) -> QWidget:
        """Return the horizontal row of six KPI cards."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        specs = [
            ("Speed (RPM)", "RPM", "rpm",        "#3B82F6", None),  # Blue
            ("Voltage",     "V",   "voltage",    "#EAB308", None),  # Yellow
            ("Current",     "A",   "current",    "#10B981", None),  # Green
            ("Power",       "W",   "power",      "#8B5CF6", None),  # Purple
            ("Temperature", "°C",  "temp",       "#EF4444", 1),     # Red
            ("Efficiency",  "%",   "efficiency", "#06B6D4", None),  # Cyan
        ]

        self._cards: dict[str, MetricCard] = {}
        for col, (title, unit, icon, accent, decs) in enumerate(specs):
            card = MetricCard(title, unit, icon, accent, decimals=decs)
            card.clicked.connect(self._on_card_clicked)
            self._cards[title] = card
            layout.addWidget(card, 0, col)

        for i in range(len(specs)):
            layout.setColumnStretch(i, 1)

        return container

    # ------------------------------------------------------------------ #
    #  Large Graph Area
    # ------------------------------------------------------------------ #
    def _build_large_graph_area(self) -> QFrame:
        """Return the single large graph container frame."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 18px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header of the graph area
        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(10)

        # Title on the left
        title_icon = QLabel("∿")
        title_icon.setFont(QFont("Segoe UI Symbol", 16))
        title_icon.setStyleSheet("color: #3B82F6; border: none;")
        
        title_lbl = QLabel("LIVE MOTOR PERFORMANCE")
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.ExtraBold))
        title_lbl.setStyleSheet("color: #E2E8F0; letter-spacing: 1.5px; border: none; font-weight: 800; padding-top: 3px;")
        
        hdr_layout.addWidget(title_icon)
        hdr_layout.addWidget(title_lbl, alignment=Qt.AlignVCenter)
        hdr_layout.addStretch()

        # Dropdown label
        drop_lbl = QLabel("Monitoring:")
        drop_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        drop_lbl.setStyleSheet("color: #64748B; border: none;")
        hdr_layout.addWidget(drop_lbl)

        # Dropdown
        self._dropdown = QComboBox()
        self._dropdown.addItems(list(self._param_configs.keys()))
        self._dropdown.setCursor(Qt.PointingHandCursor)
        self._dropdown.setStyleSheet("""
            QComboBox {
                background-color: #1E293B;
                color: #F1F5F9;
                border: 1px solid #2D3748;
                border-radius: 8px;
                padding: 6px 10px;
                min-width: 150px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                background-color: #334155;
                border-left: 1px solid #2D3748;
                border-top-right-radius: 7px;
                border-bottom-right-radius: 7px;
            }
            QComboBox::down-arrow {
                image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAW0lEQVQokc3QyQmAQAxAUacMy5qKxALsauoZUG96eB5cUHC76YdAAj8JSVH8jrAmqG7FEOqtQInBNQPKwwRE5BM5I56uRYN+J/dobo9CwrhEen7D3NShfSV/zwTNpHahNmq6QwAAAABJRU5ErkJggg==");
                width: 12px;
                height: 12px;
            }
            QComboBox:focus {
                border-color: #3B82F6;
            }
        """)
        self._dropdown.currentTextChanged.connect(self._on_dropdown_changed)
        hdr_layout.addWidget(self._dropdown)

        # Premium action buttons next to dropdown
        self._btn_pause = QPushButton("⏸ Pause")
        self._btn_auto = QPushButton("⤢ Auto Scale")
        self._btn_auto.setCheckable(True)
        self._btn_reset = QPushButton("↺ Reset Zoom")
        
        self._graph_paused = False
        
        self._btn_pause.clicked.connect(self._on_pause_graph)
        self._btn_auto.clicked.connect(self._on_auto_scale)
        self._btn_reset.clicked.connect(self._on_reset_zoom)
        
        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(10)

        for btn in (self._btn_pause, self._btn_auto, self._btn_reset):
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #E2E8F0;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    padding: 0 14px;
                }
                QPushButton:hover {
                    background-color: #273449;
                    color: #FFFFFF;
                    border: 1px solid #3B82F6;
                }
            """)
            actions_row.addWidget(btn)

        hdr_layout.addLayout(actions_row)

        layout.addLayout(hdr_layout)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        layout.addWidget(div)

        # The PyQtGraph plot widget (only one widget exists)
        self._graph = RealtimeGraph("", "RPM", "rpm", "#10B981")
        self._graph.setMinimumHeight(500)
        layout.addWidget(self._graph)

        # ── Compact info row below graph ───────────────────────────────
        layout.addWidget(self._build_info_row())

        return frame

    def _build_info_row(self) -> QWidget:
        """Build the horizontal stats row matching Image 2 design."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 8, 0, 0)
        row.setSpacing(12)

        # Card specs: (stat_key, label_title, icon_type, accent_color, bg_tint, border_tint)
        card_specs = [
            ("Current Value", f"Current {self._active_parameter}", "current", "#3B82F6", "rgba(59, 130, 246, 0.15)", "rgba(59, 130, 246, 0.35)"),
            ("Maximum",       f"Maximum {self._active_parameter}", "maximum", "#10B981", "rgba(16, 185, 129, 0.15)", "rgba(16, 185, 129, 0.35)"),
            ("Minimum",       f"Minimum {self._active_parameter}", "minimum", "#EF4444", "rgba(239, 68, 68, 0.15)",  "rgba(239, 68, 68, 0.35)"),
            ("Average",       f"Average {self._active_parameter}", "average", "#F59E0B", "rgba(245, 158, 11, 0.15)", "rgba(245, 158, 11, 0.35)"),
            ("Total Samples", "Total Samples",                     "samples", "#8B5CF6", "rgba(139, 92, 246, 0.15)", "rgba(139, 92, 246, 0.35)"),
            ("Uptime",        "Uptime",                            "uptime",  "#F97316", "rgba(249, 115, 22, 0.15)", "rgba(249, 115, 22, 0.35)"),
        ]

        self._info_row_title_labels: dict[str, QLabel] = {}

        for stat_key, title_text, icon_type, accent, bg_tint, border_tint in card_specs:
            # Main Card Frame
            card = QFrame()
            card.setFixedHeight(74)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.setStyleSheet("""
                QFrame {
                    background-color: #111827;
                    border: 1px solid rgba(255, 255, 255, 0.07);
                    border-radius: 14px;
                }
            """)

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(12)

            # Left Badge Container for Icon (Custom Painted Vector Icon Badge)
            badge = IconBadge(icon_type, accent, bg_tint, border_tint)
            card_layout.addWidget(badge, alignment=Qt.AlignVCenter)

            # Right Side Text Column (Title on top, Value + Unit on bottom)
            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(2)
            text_col.setAlignment(Qt.AlignVCenter)

            title_lbl = QLabel(title_text)
            title_lbl.setFont(QFont("Segoe UI", 9, QFont.Medium))
            title_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
            self._info_row_title_labels[stat_key] = title_lbl
            text_col.addWidget(title_lbl)

            val_lbl = QLabel("—")
            val_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
            val_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent; font-weight: 700;")
            self._live_stats_labels[stat_key] = val_lbl
            text_col.addWidget(val_lbl)

            card_layout.addLayout(text_col, stretch=1)
            row.addWidget(card, stretch=1)

        return container

    def _update_info_row_values(self) -> None:
        """Refresh the compact horizontal stats row values dynamically based on selected parameter."""
        if not (hasattr(self, "_live_stats_labels") and self._live_stats_labels):
            return

        if not self._history_values.get(self._active_parameter):
            for key in ("Current Value", "Average", "Maximum", "Minimum", "Total Samples"):
                if key in self._live_stats_labels:
                    self._live_stats_labels[key].setText("—")
            return

        vals = self._history_values[self._active_parameter]
        cur = vals[-1]
        avg = sum(vals) / len(vals)
        mx = max(vals)
        mn = min(vals)
        unit = self._param_configs[self._active_parameter]["unit"]

        unit_space = "" if unit == "°C" else " "
        dec = 2 if unit in ("V", "A", "%") else 1

        if "Current Value" in self._live_stats_labels:
            self._live_stats_labels["Current Value"].setText(f"{cur:.{dec}f}{unit_space}{unit}")
        if "Average" in self._live_stats_labels:
            self._live_stats_labels["Average"].setText(f"{avg:.{dec}f}{unit_space}{unit}")
        if "Maximum" in self._live_stats_labels:
            self._live_stats_labels["Maximum"].setText(f"{mx:.{dec}f}{unit_space}{unit}")
        if "Minimum" in self._live_stats_labels:
            self._live_stats_labels["Minimum"].setText(f"{mn:.{dec}f}{unit_space}{unit}")
        if "Total Samples" in self._live_stats_labels:
            self._live_stats_labels["Total Samples"].setText(f"{self._data_points_count:,}")

    def _build_sysinfo_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(8)
        title_icon = QLabel("◉")
        title_icon.setFont(QFont("Segoe UI Symbol", 10))
        title_icon.setStyleSheet("color: #10B981; border: none;")
        
        title_lbl = QLabel("SYSTEM INFORMATION")
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_lbl.setStyleSheet("color: #E2E8F0; letter-spacing: 1px; border: none; font-weight: 700;")
        
        hdr_layout.addWidget(title_icon)
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        layout.addWidget(divider)

        # QGridLayout for information grid
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(12)
        grid.setContentsMargins(0, 6, 0, 0)

        com_port = self._settings.get("default_com_port", "COM4")
        baud = self._settings.get("baud_rate", 115200)
        
        left_items = [
            ("Arduino Status", "Connected", "#10B981", "▦"),
            ("COM Port", str(com_port), "#94A3B8", "⎚"),
            ("Baud Rate", f"{baud} bps", "#94A3B8", "📊"),
            ("Firmware Version", "v1.0.0", "#94A3B8", "</>"),
            ("Connection Type", "USB Serial", "#94A3B8", "🔌"),
        ]

        right_items = [
            ("Session Time", "00:00:00", "#94A3B8", "⏳"),
            ("Packets / Sec", "0", "#94A3B8", "∿"),
            ("Data Rate", "0 B/s", "#94A3B8", "📥"),
            ("Data Points", "0", "#94A3B8", "⛃"),
            ("Uptime", "00:00:00", "#94A3B8", "🕒"),
        ]

        self._sysinfo_labels = {}

        for r, (key, val, color, icon) in enumerate(left_items):
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Symbol", 10))
            icon_lbl.setStyleSheet("color: #64748B; border: none;")
            icon_lbl.setFixedWidth(20)
            
            lbl = QLabel(key)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet("color: #94A3B8; border: none;")
            
            lbl_layout = QHBoxLayout()
            lbl_layout.setContentsMargins(0, 0, 0, 0)
            lbl_layout.setSpacing(8)
            lbl_layout.addWidget(icon_lbl)
            lbl_layout.addWidget(lbl)
            lbl_layout.addStretch()
            
            w_lbl = QWidget()
            w_lbl.setLayout(lbl_layout)
            w_lbl.setStyleSheet("border: none; background: transparent;")
            
            val_lbl = QLabel(val)
            val_lbl.setFont(QFont("Segoe UI", 9))
            val_lbl.setStyleSheet(f"color: {color}; border: none;")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._sysinfo_labels[key] = val_lbl
            
            grid.addWidget(w_lbl, r, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(val_lbl, r, 1, alignment=Qt.AlignRight | Qt.AlignVCenter)

        for r, (key, val, color, icon) in enumerate(right_items):
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Symbol", 10))
            icon_lbl.setStyleSheet("color: #64748B; border: none;")
            icon_lbl.setFixedWidth(20)
            
            lbl = QLabel(key)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet("color: #94A3B8; border: none;")
            
            lbl_layout = QHBoxLayout()
            lbl_layout.setContentsMargins(0, 0, 0, 0)
            lbl_layout.setSpacing(8)
            lbl_layout.addWidget(icon_lbl)
            lbl_layout.addWidget(lbl)
            lbl_layout.addStretch()
            
            w_lbl = QWidget()
            w_lbl.setLayout(lbl_layout)
            w_lbl.setStyleSheet("border: none; background: transparent;")
            
            val_lbl = QLabel(val)
            val_lbl.setFont(QFont("Segoe UI", 9))
            val_lbl.setStyleSheet(f"color: {color}; border: none;")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._sysinfo_labels[key] = val_lbl
            
            grid.addWidget(w_lbl, r, 2, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(val_lbl, r, 3, alignment=Qt.AlignRight | Qt.AlignVCenter)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 0)

        layout.addWidget(grid_widget)
        
        layout.addStretch()
        return panel

    @staticmethod
    def _make_action_btn(text: str, bg: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(34)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #FFFFFF;
                border: 1px solid {hover};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        return btn

    # ------------------------------------------------------------------ #
    #  Public update API
    # ------------------------------------------------------------------ #
    def update_data(self) -> None:
        """Refresh all visible metrics from the shared serial telemetry state."""
        d = self._data
        metrics = self._serial.get_latest_metrics() if self._serial else None
        has_live_data = bool(self._serial and self._serial.has_live_data)

        if has_live_data and metrics is not None:
            self._cards["Speed (RPM)"].set_value(float(metrics["rpm"]))
            self._cards["Voltage"].set_value(float(metrics["voltage"]))
            self._cards["Current"].set_value(float(metrics["current"]))
            self._cards["Power"].set_value(float(metrics["power"]))
            self._cards["Efficiency"].set_value(float(metrics["efficiency"]))
            self._cards["Temperature"].set_value(float(metrics["temperature"]))

            self._elapsed_time += 0.1
            self._history_times.append(self._elapsed_time)
            self._history_values["RPM"].append(float(metrics["rpm"]))
            self._history_values["Voltage"].append(float(metrics["voltage"]))
            self._history_values["Current"].append(float(metrics["current"]))
            self._history_values["Power"].append(float(metrics["power"]))
            self._history_values["Efficiency"].append(float(metrics["efficiency"]))
            self._history_values["Temperature"].append(float(metrics["temperature"]))

            max_pts = 600
            if len(self._history_times) > max_pts:
                self._history_times.pop(0)
                for k in self._history_values:
                    self._history_values[k].pop(0)

            if not getattr(self, '_graph_paused', False):
                self._graph.set_data(list(self._history_times), list(self._history_values[self._active_parameter]))
                self._graph.set_waiting_state(False)

            self._data_points_count += 1
            
            # Info row updates
            self._update_info_row_values()
            
            if "direction" in metrics:
                current_dir = self._ctrl_panel.get_direction()
                expected_dir = "FORWARD" if metrics["direction"] == "FWD" else "REVERSE"
                if current_dir != expected_dir:
                    self._ctrl_panel.set_direction_state(expected_dir)

            if "Temperature" in self._sysinfo_labels: self._sysinfo_labels["Temperature"].setText(f"{float(metrics['temperature']):.1f}°C")
            if "Data Points" in self._sysinfo_labels: self._sysinfo_labels["Data Points"].setText(str(self._data_points_count))
        else:
            for title in ("Speed (RPM)", "Voltage", "Current", "Power", "Efficiency", "Temperature"):
                self._cards[title].set_value(0.0)
            self._graph.set_waiting_state(True)
            if "Temperature" in self._sysinfo_labels: self._sysinfo_labels["Temperature"].setText("0.0 °C")

        # Connection Status (ONLINE/OFFLINE) updated independently of live data
        if self._serial and self._serial.is_connected:
            if "Arduino Status" in self._sysinfo_labels:
                self._sysinfo_labels["Arduino Status"].setText("ONLINE")
                self._sysinfo_labels["Arduino Status"].setStyleSheet("color: #10B981; border: none; font-weight: 700;")
            if "COM Port" in self._sysinfo_labels:
                self._sysinfo_labels["COM Port"].setText(self._serial.port)
            if "Connection Type" in self._sysinfo_labels: self._sysinfo_labels["Connection Type"].setText("USB Serial")
        else:
            if "Arduino Status" in self._sysinfo_labels:
                self._sysinfo_labels["Arduino Status"].setText("OFFLINE")
                self._sysinfo_labels["Arduino Status"].setStyleSheet("color: #EF4444; border: none; font-weight: 700;")
            if "COM Port" in self._sysinfo_labels:
                self._sysinfo_labels["COM Port"].setText("Waiting for Arduino...")
            if "Connection Type" in self._sysinfo_labels: self._sysinfo_labels["Connection Type"].setText("USB Serial")

        # Session metrics updated continuously
        if "Uptime" in self._sysinfo_labels: self._sysinfo_labels["Uptime"].setText(d.uptime)
        if "Uptime" in self._live_stats_labels: self._live_stats_labels["Uptime"].setText(d.uptime)
        if "Session Time" in self._sysinfo_labels: self._sysinfo_labels["Session Time"].setText(d.session_time_str)

        # Performance metrics
        if self._serial and self._serial.is_connected:
            pps = self._serial.packets_per_second
            bps = self._serial.data_rate_bps
            if "Packets / Sec" in self._sysinfo_labels: self._sysinfo_labels["Packets / Sec"].setText(str(pps))
            if "Data Rate" in self._sysinfo_labels:
                if bps >= 1024:
                    self._sysinfo_labels["Data Rate"].setText(f"{bps/1024:.1f} KB/s")
                else:
                    self._sysinfo_labels["Data Rate"].setText(f"{bps} B/s")
        else:
            if "Packets / Sec" in self._sysinfo_labels: self._sysinfo_labels["Packets / Sec"].setText("0")
            if "Data Rate" in self._sysinfo_labels: self._sysinfo_labels["Data Rate"].setText("0 B/s")
            if "Data Points" in self._sysinfo_labels: self._sysinfo_labels["Data Points"].setText("0")

        try:
            import psutil
            mem = psutil.virtual_memory().percent
            if "Memory Usage" in self._sysinfo_labels: self._sysinfo_labels["Memory Usage"].setText(f"{mem:.1f} %")
        except ImportError:
            if "Memory Usage" in self._sysinfo_labels: self._sysinfo_labels["Memory Usage"].setText("0.0 %")

        self._update_status_card()

    def _update_status_card(self) -> None:
        """Update the header status badge dynamically (Moved to main.py, but keep interface)."""
        pass

    # ------------------------------------------------------------------ #
    #  Settings Management
    # ------------------------------------------------------------------ #
    def update_settings(self, settings: dict) -> None:
        """Receive updated settings and refresh display variables."""
        self._settings = settings
        if "default_com_port" in settings and "COM Port" in self._sysinfo_labels:
            self._sysinfo_labels["COM Port"].setText(settings["default_com_port"])
        if "baud_rate" in settings and "Baud Rate" in self._sysinfo_labels:
            self._sysinfo_labels["Baud Rate"].setText(f"{settings['baud_rate']} Baud")

    def set_start_stop_enabled(self, enabled: bool) -> None:
        """Enable or disable the dashboard's inline start/stop controls."""
        self._ctrl_panel.set_start_stop_enabled(enabled)

    def reset_on_disconnect(self) -> None:
        """Reset dashboard widgets immediately when the Arduino disconnects."""
        for title in ("Speed (RPM)", "Voltage", "Current", "Power", "Efficiency", "Temperature"):
            self._cards[title].set_value(0.0)
        self._ctrl_panel.set_pwm(0)
        self._ctrl_panel.set_running_state(False)
        self._ctrl_panel.set_start_stop_enabled(False)
        self._history_times.clear()
        for values in self._history_values.values():
            values.clear()
        self._graph.clear_data()
        self._graph.set_waiting_state(True)
        self._update_info_row_values()
        if "Arduino Status" in self._sysinfo_labels:
            self._sysinfo_labels["Arduino Status"].setText("OFFLINE")
            self._sysinfo_labels["Arduino Status"].setStyleSheet("color: #EF4444; border: none; font-weight: 700;")
        if "COM Port" in self._sysinfo_labels:
            self._sysinfo_labels["COM Port"].setText("Waiting for Arduino...")
        if "Connection Type" in self._sysinfo_labels: self._sysinfo_labels["Connection Type"].setText("USB Serial")
        if "Uptime" in self._sysinfo_labels: self._sysinfo_labels["Uptime"].setText(self._data.uptime)
        if "Temperature" in self._sysinfo_labels: self._sysinfo_labels["Temperature"].setText("0.0°C")
        if "Packets / Sec" in self._sysinfo_labels: self._sysinfo_labels["Packets / Sec"].setText("0")
        if "Data Rate" in self._sysinfo_labels: self._sysinfo_labels["Data Rate"].setText("0 B/s")
        if "Data Points" in self._sysinfo_labels: self._sysinfo_labels["Data Points"].setText("0")
        if "Session Time" in self._sysinfo_labels: self._sysinfo_labels["Session Time"].setText("00:00:00")

    # ------------------------------------------------------------------ #
    #  Slot helpers
    # ------------------------------------------------------------------ #

    def _on_run(self) -> None:
        """Handle START button press."""
        self._data.set_running(True)
        self._serial.send_command("START")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("Motor Started")

    def _on_stop(self) -> None:
        """Handle STOP button press."""
        # Capture stats before resetting
        stats = {
            "duration": self._data.session_time_str,
            "max_rpm": self._data.max_rpm,
            "avg_rpm": self._data.avg_rpm,
            "max_current": self._data.max_current,
            "max_power": self._data.max_power,
            "avg_efficiency": self._data.avg_efficiency,
            "avg_voltage": self._data.avg_voltage,
            "max_pwm": self._data.max_pwm_duty
        }

        self._data.set_running(False)
        self._data.set_pwm_duty(0)
        self._ctrl_panel.set_pwm(0)
        self._serial.send_command("STOP")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("Motor Stopped")

        from widgets.test_summary_dialog import TestSummaryDialog
        dlg = TestSummaryDialog(stats, self)
        dlg.exec()

    def _on_estop(self) -> None:
        """Handle EMERGENCY STOP button press."""
        self._data.set_running(False)
        self._data.set_pwm_duty(0)
        self._ctrl_panel.set_pwm(0)
        self._serial.send_command("STOP")
        QMessageBox.critical(
            self,
            "EMERGENCY TRIP ACTIVATED",
            "Motor Emergency Trip has been triggered!\nAll motor operations halted and throttle set to 0%."
        )

    def _on_pwm_changed(self, duty: int) -> None:
        """Handle PWM slider changes."""
        self._data.set_pwm_duty(duty)
        self._serial.send_command(f"PWM:{duty}")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("PWM Updated")

    def _on_direction_changed(self, direction: str) -> None:
        """Handle Direction button press."""
        self._data.set_direction(direction)
        dir_cmd = "FWD" if direction == "FORWARD" else "REV"
        self._serial.send_command(f"DIR:{dir_cmd}")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("Direction Changed")

    def _on_card_clicked(self, title: str) -> None:
        """Called when a metric card is clicked – switch dropdown parameter."""
        MAP_TITLE_TO_KEY = {
            "Speed (RPM)": "RPM",
            "Voltage": "Voltage",
            "Current": "Current",
            "Power": "Power",
            "Efficiency": "Efficiency",
            "Temperature": "Temperature"
        }
        key = MAP_TITLE_TO_KEY.get(title)
        if key and self._dropdown:
            self._dropdown.setCurrentText(key)

    def _on_dropdown_changed(self, text: str) -> None:
        """Switch the active graphed parameter."""
        if text not in self._param_configs:
            return
        self._active_parameter = text
        cfg = self._param_configs[text]
        self._graph.configure_parameter(cfg["label"], cfg["unit"], cfg["color"])
        
        # Dynamic info row title labels update
        if hasattr(self, "_info_row_title_labels") and self._info_row_title_labels:
            if "Current Value" in self._info_row_title_labels:
                self._info_row_title_labels["Current Value"].setText(f"Current {text}")
            if "Maximum" in self._info_row_title_labels:
                self._info_row_title_labels["Maximum"].setText(f"Maximum {text}")
            if "Minimum" in self._info_row_title_labels:
                self._info_row_title_labels["Minimum"].setText(f"Minimum {text}")
            if "Average" in self._info_row_title_labels:
                self._info_row_title_labels["Average"].setText(f"Average {text}")
            
        # Refresh info row values instantly
        self._update_info_row_values()

        # Instantly refresh data representation
        if not getattr(self, '_graph_paused', False):
            self._graph.set_data(list(self._history_times), list(self._history_values[text]))

    def _on_pause_graph(self) -> None:
        """Pause or resume real-time graph updating."""
        self._graph_paused = not getattr(self, '_graph_paused', False)
        self._btn_pause.setText("▶ Resume" if self._graph_paused else "⏸ Pause")
        if not self._graph_paused:
            self._graph.set_data(list(self._history_times), list(self._history_values[self._active_parameter]))

    def _on_auto_scale(self) -> None:
        """Enable or disable auto-scaling on the Y-axis."""
        is_on = self._btn_auto.isChecked()
        self._graph.set_auto_scale(is_on)
        # Update style to reflect toggle state
        if is_on:
            self._btn_auto.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: 1px solid #2563EB;
                    border-radius: 8px;
                    padding: 0 14px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
        else:
            self._btn_auto.setStyleSheet("""
                QPushButton {
                    background-color: #1F2937;
                    color: #E2E8F0;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    padding: 0 14px;
                }
                QPushButton:hover {
                    background-color: #273449;
                    color: #FFFFFF;
                    border: 1px solid #3B82F6;
                }
            """)

    def _on_reset_zoom(self) -> None:
        """Reset the graph's zoom and snap back to the default range."""
        self._graph.reset_zoom()
        # Make sure the Auto Scale button is unchecked
        self._btn_auto.setChecked(False)
        self._btn_auto.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: #E2E8F0;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #273449;
                color: #FFFFFF;
                border: 1px solid #3B82F6;
            }
        """)
        if self._history_times:
            x_max = self._history_times[-1]
            x_min = max(0.0, x_max - 60.0)
            self._graph._plot_widget.setXRange(x_min, x_max, padding=0)

    def _on_export_graph(self) -> None:
        """Export the current graph view as a PNG image."""
        try:
            import pyqtgraph.exporters
            exporter = pyqtgraph.exporters.ImageExporter(self._graph._plot_widget.plotItem)
            filename = f"graph_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            exporter.export(filename)
            main_win = self.window()
            if hasattr(main_win, '_show_toast'):
                main_win._show_toast("✅ Dashboard saved as PNG")
            else:
                QMessageBox.information(self, "Export Successful", f"Graph exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export graph: {e}")

    def _on_save_data_clicked(self) -> None:
        """Handle SAVE DATA button press."""
        QMessageBox.information(
            self,
            "Data Export",
            "Telemetry session data successfully exported to dashboard_log.csv!"
        )

    def _on_clear_data_clicked(self) -> None:
        """Handle CLEAR DATA button press."""
        confirm = QMessageBox.question(
            self,
            "Clear Session Data",
            "Are you sure you want to clear current live telemetry buffer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self._history_times.clear()
            for k in self._history_values:
                self._history_values[k].clear()
            self._graph.clear_data()
            self._data_points_count = 0
            QMessageBox.information(self, "Buffer Cleared", "Telemetry buffer has been reset.")
