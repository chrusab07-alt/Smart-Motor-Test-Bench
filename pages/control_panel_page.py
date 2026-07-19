"""
control_panel_page.py
---------------------
Dedicated full-screen Control Panel page for the Smart Motor Test Bench.
Includes an industrial layout with a massive PWM duty cycle controls slider,
status light indicators, Start/Stop action buttons, and a glowing Emergency Stop.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QSlider, QSizePolicy,
    QMessageBox,
)

from backend.data_generator import DataGenerator
from widgets.control_panel import AnimatedSlider

from backend.serial_manager import SerialManager

class ControlPanelPage(QWidget):
    """
    Dedicated Control Panel Page.
    Features detailed dial-in controls and safety controls like Emergency Stop.
    """
    def __init__(self, data_gen: DataGenerator, serial_mgr: SerialManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = data_gen
        self._serial = serial_mgr
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        # ── Page Header ────────────────────────────────────────────────
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        title_lbl = QLabel("🎮  SYSTEM CONTROL PANEL")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #F1F5F9; letter-spacing: 0.5px; font-weight: 800;")

        desc_lbl = QLabel("Configure motor speed, adjust parameters, and override safety systems.")
        desc_lbl.setFont(QFont("Segoe UI", 10))
        desc_lbl.setStyleSheet("color: #64748B;")

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(desc_lbl)
        root_layout.addLayout(header_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        root_layout.addWidget(divider)

        # ── Main Content Area ──────────────────────────────────────────
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Column: PWM Speed Controller
        pwm_card = QFrame()
        pwm_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 14px;
            }
        """)
        pwm_layout = QVBoxLayout(pwm_card)
        pwm_layout.setContentsMargins(24, 24, 24, 24)
        pwm_layout.setSpacing(18)

        pwm_title = QLabel("⚡  SPEED CONTROL (PWM)")
        pwm_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        pwm_title.setStyleSheet("color: #E2E8F0; letter-spacing: 1px; border: none;")
        pwm_layout.addWidget(pwm_title)

        # Large speed readout display
        self._speed_readout = QLabel("72 %")
        self._speed_readout.setFont(QFont("Segoe UI", 46, QFont.Bold))
        self._speed_readout.setStyleSheet("color: #F97316; font-weight: 800; border: none;")
        self._speed_readout.setAlignment(Qt.AlignCenter)
        pwm_layout.addWidget(self._speed_readout)

        # Slider (vertical for a cool throttle look)
        self._slider = AnimatedSlider(Qt.Vertical)
        self._slider.setRange(0, 100)
        self._slider.setValue(72)
        self._slider.setMinimumHeight(260)
        self._slider.setMinimumWidth(62)
        self._slider.setCursor(Qt.PointingHandCursor)
        self._slider.valueChanged.connect(self._on_slider_changed)
        pwm_layout.addWidget(self._slider, alignment=Qt.AlignHCenter)

        pwm_desc = QLabel("Throttle Slider (0 - 100 % Duty)")
        pwm_desc.setFont(QFont("Segoe UI", 10, QFont.Bold))
        pwm_desc.setStyleSheet("color: #475569; border: none;")
        pwm_desc.setAlignment(Qt.AlignCenter)
        pwm_layout.addWidget(pwm_desc)

        main_layout.addWidget(pwm_card, stretch=4)

        # Right Column: Controls and Emergency Stop
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)

        # State Indicator & Controls Card
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 14px;
            }
        """)
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(24, 24, 24, 24)
        ctrl_layout.setSpacing(16)

        ctrl_title = QLabel("⚙  OPERATION PARAMETERS")
        ctrl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ctrl_title.setStyleSheet("color: #E2E8F0; letter-spacing: 1px; border: none;")
        ctrl_layout.addWidget(ctrl_title)

        # Toggle Direction
        dir_title = QLabel("Motor Direction Switch")
        dir_title.setFont(QFont("Segoe UI", 10))
        dir_title.setStyleSheet("color: #94A3B8; border: none;")
        ctrl_layout.addWidget(dir_title)

        dir_btn_row = QHBoxLayout()
        dir_btn_row.setSpacing(10)
        self._fwd_btn = self._make_mode_button("⟳  FORWARD", "#1D4ED8", "#2563EB", active=True)
        self._rev_btn = self._make_mode_button("⟲  REVERSE", "#334155", "#475569", active=False)
        self._fwd_btn.clicked.connect(lambda: self._on_direction_changed("FORWARD"))
        self._rev_btn.clicked.connect(lambda: self._on_direction_changed("REVERSE"))
        dir_btn_row.addWidget(self._fwd_btn)
        dir_btn_row.addWidget(self._rev_btn)
        ctrl_layout.addLayout(dir_btn_row)

        # Operations row
        ops_title = QLabel("Sequencer Controls")
        ops_title.setFont(QFont("Segoe UI", 10))
        ops_title.setStyleSheet("color: #94A3B8; border: none;")
        ctrl_layout.addWidget(ops_title)

        ops_btn_row = QHBoxLayout()
        ops_btn_row.setSpacing(10)
        self._start_btn = self._make_action_button("▶  START MOTOR", "#15803D", "#16A34A")
        self._stop_btn  = self._make_action_button("■  STOP MOTOR", "#DC2626", "#B91C1C")
        self._reset_btn = self._make_action_button("↺  RESET STATS", "#475569", "#64748B")

        self._start_btn.clicked.connect(self._on_start_clicked)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._reset_btn.clicked.connect(self._on_reset_clicked)

        ops_btn_row.addWidget(self._start_btn)
        ops_btn_row.addWidget(self._stop_btn)
        ops_btn_row.addWidget(self._reset_btn)
        ctrl_layout.addLayout(ops_btn_row)

        right_panel.addWidget(ctrl_card, stretch=6)

        # Safety / Emergency Stop Card
        safety_card = QFrame()
        safety_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 14px;
            }
        """)
        safety_layout = QVBoxLayout(safety_card)
        safety_layout.setContentsMargins(24, 20, 24, 20)
        safety_layout.setSpacing(14)

        safety_title = QLabel("⚠️  SAFETY AND TRIP SYSTEMS")
        safety_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        safety_title.setStyleSheet("color: #EF4444; letter-spacing: 1px; border: none;")
        safety_layout.addWidget(safety_title)

        # Big emergency stop button
        self._estop_btn = QPushButton("🚨  EMERGENCY STOP")
        self._estop_btn.setFixedHeight(54)
        self._estop_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._estop_btn.setCursor(Qt.PointingHandCursor)
        self._estop_btn.setStyleSheet("""
            QPushButton {
                background-color: #991B1B;
                color: #FFFFFF;
                border: 2px solid #EF4444;
                border-radius: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #EF4444;
                border-color: #F87171;
            }
            QPushButton:pressed {
                background-color: #7F1D1D;
            }
        """)
        self._estop_btn.clicked.connect(self._on_estop_clicked)
        safety_layout.addWidget(self._estop_btn)

        right_panel.addWidget(safety_card, stretch=4)

        main_layout.addLayout(right_panel, stretch=6)
        root_layout.addLayout(main_layout)

    def _make_mode_button(self, text: str, bg: str, hover: str, *, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg if active else '#1E293B'};
                color: {'#FFFFFF' if active else '#94A3B8'};
                border: 1px solid {hover if active else '#2D3748'};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover};
                color: #FFFFFF;
                border-color: {hover};
            }}
        """)
        return btn

    def _make_action_button(self, text: str, bg: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(40)
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
    #  Slots & Callback Actions
    # ------------------------------------------------------------------ #
    def _on_slider_changed(self, value: int) -> None:
        self._speed_readout.setText(f"{value} %")
        self._data.set_pwm_duty(value)
        if self._serial:
            self._serial.send_command(f"PWM:{value}")

    def _on_direction_changed(self, direction: str) -> None:
        self._data.set_direction(direction)
        is_fwd = direction == "FORWARD"
        if self._serial:
            dir_cmd = "FWD" if is_fwd else "REV"
            self._serial.send_command(f"DIR:{dir_cmd}")
        self._fwd_btn.setStyleSheet(self._make_mode_button("⟳  FORWARD", "#1D4ED8", "#2563EB", active=is_fwd).styleSheet())
        self._rev_btn.setStyleSheet(self._make_mode_button("⟲  REVERSE", "#334155", "#475569", active=not is_fwd).styleSheet())

    def _on_start_clicked(self) -> None:
        self._data.set_running(True)
        if self._serial:
            self._serial.send_command("START")
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._speed_readout.setText("Running")
        self._speed_readout.setStyleSheet("color: #10B981; font-weight: 800; border: none;")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("Motor Started")

    def _on_stop_clicked(self) -> None:
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
        self._slider.animate_to(0)
        if self._serial:
            self._serial.send_command("STOP")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._speed_readout.setText("Stopped")
        self._speed_readout.setStyleSheet("color: #F97316; font-weight: 800; border: none;")
        if hasattr(self.window(), "_show_toast"):
            self.window()._show_toast("Motor Stopped")

        from widgets.test_summary_dialog import TestSummaryDialog
        dlg = TestSummaryDialog(stats, self)
        dlg.exec()

    def _on_reset_clicked(self) -> None:
        # Reset data generator stats
        self._data.max_rpm = 0.0
        self._data.min_rpm = float("inf")
        self._data.max_voltage = 0.0
        self._data.min_voltage = float("inf")
        self._data.max_current = 0.0
        self._data.min_current = float("inf")
        self._data.max_power = 0.0
        self._data.min_power = float("inf")
        self._data.max_efficiency = 0.0
        self._data.min_efficiency = float("inf")
        self._data.max_temperature = 0.0
        self._data.min_temperature = float("inf")
        # Reset slider
        self._slider.animate_to(72)

    def _on_estop_clicked(self) -> None:
        """Emergency stop: immmediately stops motor and drops PWM duty to 0%."""
        self._data.set_running(False)
        self._slider.animate_to(0)
        if self._serial:
            self._serial.send_command("STOP")
        # Give visual flashing indicators (optional/nice touch)
        self._speed_readout.setText("TRIPPED")
        self._speed_readout.setStyleSheet("color: #EF4444; font-weight: 800; border: none;") # Flash red
        # Trigger popup alert box
        QMessageBox.critical(self, "EMERGENCY TRIP ACTIVATED", "Motor Emergency Trip has been triggered!\nAll motor operations halted and throttle set to 0%.")
        
        # Reset layout style back to orange after prompt close
        self._speed_readout.setStyleSheet("color: #F97316; font-weight: 800; border: none;")
        self._speed_readout.setText("0 %")

    def set_start_stop_enabled(self, enabled: bool) -> None:
        """Enable or disable the start/stop action buttons."""
        if hasattr(self, '_start_btn') and hasattr(self, '_stop_btn'):
            self._start_btn.setEnabled(enabled)
            self._stop_btn.setEnabled(enabled)

    def update_data(self) -> None:
        """Syncs GUI buttons/slider state to the backend generator state."""
        # Sync direction from data generator
        current_dir = "FORWARD" if self._fwd_btn.styleSheet() == self._make_mode_button("⟳  FORWARD", "#1D4ED8", "#2563EB", active=True).styleSheet() else "REVERSE"
        expected_dir = self._data.direction
        if current_dir != expected_dir:
            is_fwd = expected_dir == "FORWARD"
            self._fwd_btn.setStyleSheet(self._make_mode_button("⟳  FORWARD", "#1D4ED8", "#2563EB", active=is_fwd).styleSheet())
            self._rev_btn.setStyleSheet(self._make_mode_button("⟲  REVERSE", "#334155", "#475569", active=not is_fwd).styleSheet())
