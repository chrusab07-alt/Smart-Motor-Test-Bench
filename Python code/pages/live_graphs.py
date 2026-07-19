"""
live_graphs.py
--------------
Dedicated full-screen Live Graphs page for the Smart Motor Test Bench.
Displays 6 scrolling real-time graphs with crosshair mouse tracking.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path when running live_graphs.py directly
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QSizePolicy
)

from widgets.graph_widget import RealtimeGraph
from backend.serial_manager import SerialManager

class LiveGraphsPage(QWidget):
    """
    Dedicated full-screen Live Graphs page.
    Manages and displays detailed real-time charts for RPM, Voltage, Current, Power, Efficiency, and PWM Duty.
    """
    def __init__(self, serial_mgr: SerialManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._serial = serial_mgr
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title_lbl = QLabel("LIVE GRAPHS TELEMETRY")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        root_layout.addWidget(title_lbl)

        # ── Scrollable Graphs Container ────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        
        # Grid layout for graphs
        grid = QGridLayout(scroll_widget)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)

        # Instantiate graphs
        self._graph_rpm  = RealtimeGraph("Speed (RPM) vs Time",  "RPM",      "rpm",  "#10B981")
        self._graph_volt = RealtimeGraph("Voltage vs Time",      "Voltage",  "V",    "#3B82F6")
        self._graph_curr = RealtimeGraph("Current vs Time",      "Current",  "A",    "#F59E0B")
        self._graph_pwr  = RealtimeGraph("Power vs Time",        "Power",    "W",    "#8B5CF6")
        self._graph_eff  = RealtimeGraph("Efficiency vs Time",   "Efficiency","%",   "#06B6D4")
        self._graph_temp = RealtimeGraph("Temperature vs Time",  "Temperature","°C", "#F97316")

        # Set heights to make them spacious and large
        for graph in (self._graph_rpm, self._graph_volt, self._graph_curr, self._graph_pwr, self._graph_eff, self._graph_temp):
            graph.setMinimumHeight(280)

        # Add to grid: 2x3 responsive layout (rows x cols)
        grid.addWidget(self._graph_rpm,  0, 0)
        grid.addWidget(self._graph_volt, 0, 1)
        grid.addWidget(self._graph_curr, 0, 2)
        grid.addWidget(self._graph_pwr,  1, 0)
        grid.addWidget(self._graph_eff,  1, 1)
        grid.addWidget(self._graph_temp,  1, 2)

        scroll.setWidget(scroll_widget)
        root_layout.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #  Public Update API
    # ------------------------------------------------------------------ #
    def update_data(self) -> None:
        """Called periodically by main.py timer ticks to update active plots."""
        if not self._serial or not self._serial.has_live_data:
            for graph in (self._graph_rpm, self._graph_volt, self._graph_curr, self._graph_pwr, self._graph_eff, self._graph_temp):
                graph.set_waiting_state(True)
            return

        metrics = self._serial.get_latest_metrics()
        self._graph_rpm.append_value(float(metrics["rpm"]))
        self._graph_volt.append_value(float(metrics["voltage"]))
        self._graph_curr.append_value(float(metrics["current"]))
        self._graph_pwr.append_value(float(metrics["power"]))
        self._graph_eff.append_value(float(metrics["efficiency"]))
        self._graph_temp.append_value(float(metrics["temperature"]))

    def clear_all_graphs(self) -> None:
        """Reset and wipe history from all graph displays."""
        for graph in (self._graph_rpm, self._graph_volt, self._graph_curr, self._graph_pwr, self._graph_eff, self._graph_temp):
            graph.clear_data()
            graph.set_waiting_state(True)
