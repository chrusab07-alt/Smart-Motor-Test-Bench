"""
control_panel.py
----------------
Motor control panel widget — industrial-grade UI.
Provides: PWM slider, direction switch, start/stop, and a prominent
EMERGENCY STOP button with live motor state readout.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSlider,
    QLabel, QPushButton, QFrame, QSizePolicy, QMessageBox,
)


class AnimatedSlider(QSlider):
    """QSlider that animates its value changes smoothly when set programmatically."""
    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None) -> None:
        super().__init__(orientation, parent)
        self._anim = QPropertyAnimation(self, b"value")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def animate_to(self, target_val: int) -> None:
        self._anim.stop()
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(target_val)
        self._anim.start()


class ControlPanel(QFrame):
    """
    Motor control panel widget.

    Signals:
        pwm_changed(int)        – new PWM duty cycle 0–100
        direction_changed(str)  – "FORWARD" or "REVERSE"
        run_requested()         – START pressed
        stop_requested()        – STOP pressed
        estop_requested()       – EMERGENCY STOP pressed
    """

    pwm_changed       = Signal(int)
    direction_changed = Signal(str)
    run_requested     = Signal()
    stop_requested    = Signal()
    estop_requested   = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._running: bool = True
        self._direction: str = "FORWARD"
        self._build_ui()

        # Blink timer for E-STOP indicator when active
        self._estop_blink_timer = QTimer(self)
        self._estop_blink_timer.setInterval(500)
        self._estop_blink_timer.timeout.connect(self._blink_estop)
        self._estop_blink = False

    # ------------------------------------------------------------------ #
    #  Build UI
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(18)

        self.setStyleSheet("""
            ControlPanel {
                background-color: #111827;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 18px;
            }
        """)

        # ── Header ───────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        icon = QLabel("🎮")
        icon.setFont(QFont("Segoe UI Symbol", 12))
        icon.setStyleSheet("color: #10B981; border: none;")
        
        title = QLabel("CONTROL PANEL")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title.setStyleSheet("color: #E2E8F0; letter-spacing: 1px; border: none; font-weight: 700;")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        root.addLayout(header_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        root.addWidget(divider)

        # ── Columns ──────────────────────────────────────────────────────
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(24)

        # ── Col 1: PWM Duty Cycle
        col1 = QVBoxLayout()
        col1.setSpacing(10)
        lbl1 = QLabel("PWM DUTY CYCLE")
        lbl1.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl1.setStyleSheet("color: #94A3B8; border: none;")
        col1.addWidget(lbl1)

        pwm_val_layout = QHBoxLayout()
        pwm_val_layout.setSpacing(10)
        self._pwm_pct_lbl = QLabel("50")
        self._pwm_pct_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._pwm_pct_lbl.setAlignment(Qt.AlignCenter)
        self._pwm_pct_lbl.setStyleSheet("""
            QLabel {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        self._pwm_pct_lbl.setFixedHeight(36)
        
        pct_sign = QLabel("%")
        pct_sign.setFont(QFont("Segoe UI", 10, QFont.Bold))
        pct_sign.setStyleSheet("color: #94A3B8; border: none;")
        
        pwm_val_layout.addWidget(self._pwm_pct_lbl)
        pwm_val_layout.addWidget(pct_sign)
        pwm_val_layout.addStretch()
        col1.addLayout(pwm_val_layout)

        self._pwm_slider = AnimatedSlider(Qt.Horizontal)
        self._pwm_slider.setRange(0, 100)
        self._pwm_slider.setValue(50)
        self._pwm_slider.setCursor(Qt.PointingHandCursor)
        self._pwm_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #1E293B;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #F59E0B;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #10B981;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.12);
            }
        """)
        self._pwm_slider.valueChanged.connect(self._on_pwm_changed)
        self._pwm_slider.sliderReleased.connect(self._show_coming_soon)
        col1.addWidget(self._pwm_slider)

        minmax_layout = QHBoxLayout()
        min_lbl = QLabel("0")
        max_lbl = QLabel("100")
        for l in (min_lbl, max_lbl):
            l.setFont(QFont("Segoe UI", 8))
            l.setStyleSheet("color: #64748B; border: none;")
        minmax_layout.addWidget(min_lbl)
        minmax_layout.addStretch()
        minmax_layout.addWidget(max_lbl)
        col1.addLayout(minmax_layout)
        col1.addStretch()
        
        cols_layout.addLayout(col1, stretch=1)
        
        vdiv1 = self._make_divider(vertical=True)
        cols_layout.addWidget(vdiv1)

        # ── Col 2: Direction
        col2 = QVBoxLayout()
        col2.setSpacing(10)
        lbl2 = QLabel("DIRECTION")
        lbl2.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl2.setStyleSheet("color: #94A3B8; border: none;")
        col2.addWidget(lbl2)

        dir_grid = QGridLayout()
        dir_grid.setSpacing(8)
        self._fwd_btn = self._make_dir_button("↑ Forward", "#10B981", "#059669", active=True)
        self._rev_btn = self._make_dir_button("↺ Reverse", "#1E293B", "#334155", active=False)
        self._fwd_btn.clicked.connect(lambda: self._on_direction("FORWARD"))
        self._rev_btn.clicked.connect(lambda: self._on_direction("REVERSE"))
        
        firmware_btn = QPushButton("🔄\nFirmware")
        firmware_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
        firmware_btn.setCursor(Qt.PointingHandCursor)
        firmware_btn.setFixedHeight(34)
        firmware_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #3B82F6;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #273449;
            }
        """)
        firmware_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        firmware_btn.clicked.connect(self._show_coming_soon)

        dir_grid.addWidget(self._fwd_btn, 0, 0)
        dir_grid.addWidget(self._rev_btn, 1, 0)
        dir_grid.addWidget(firmware_btn, 0, 1, 2, 1)
        dir_grid.setColumnStretch(0, 2)
        dir_grid.setColumnStretch(1, 1)

        col2.addLayout(dir_grid)
        col2.addStretch()
        
        cols_layout.addLayout(col2, stretch=1)

        vdiv2 = self._make_divider(vertical=True)
        cols_layout.addWidget(vdiv2)

        # ── Col 3: Motor Control
        col3 = QVBoxLayout()
        col3.setSpacing(10)
        lbl3 = QLabel("MOTOR CONTROL")
        lbl3.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl3.setStyleSheet("color: #94A3B8; border: none;")
        col3.addWidget(lbl3)

        rs_row = QHBoxLayout()
        rs_row.setSpacing(8)
        
        self._start_btn = QPushButton("▶ Start")
        self._start_btn.setFixedHeight(34)
        self._start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: #EAB308;
                color: #FFFFFF;
                border: 1px solid #CA8A04;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #CA8A04; }
            QPushButton:disabled { background-color: #334155; color: #94A3B8; border: none; }
        """)

        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.setFixedHeight(34)
        self._stop_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #EAB308;
                border: 1px solid #EAB308;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; }
            QPushButton:disabled { border-color: #475569; color: #475569; }
        """)

        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn.clicked.connect(self._on_stop)
        rs_row.addWidget(self._start_btn)
        rs_row.addWidget(self._stop_btn)
        col3.addLayout(rs_row)

        self._estop_btn = QPushButton("◉ EMERGENCY STOP")
        self._estop_btn.setFixedHeight(40)
        self._estop_btn.setCursor(Qt.PointingHandCursor)
        self._estop_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._estop_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: 2px solid rgba(239,68,68,0.85);
                border-radius: 10px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        self._estop_btn.clicked.connect(self._on_estop)
        col3.addWidget(self._estop_btn)
        col3.addStretch()
        
        cols_layout.addLayout(col3, stretch=1)

        root.addLayout(cols_layout)

    # ------------------------------------------------------------------ #
    #  Static Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _make_divider(vertical: bool = False) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
        style = f"background-color: rgba(255,255,255,0.03); border: none; {'max-width: 1px;' if vertical else 'max-height: 1px;'}"
        line.setStyleSheet(style)
        return line

    @staticmethod
    def _make_dir_button(text: str, bg: str, hover: str, *, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(34)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg if active else '#1E293B'};
                color: {'#FFFFFF' if active else '#A8B3C5'};
                border: 1px solid rgba(255,255,255,0.02);
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: {bg};
            }}
        """)
        return btn

    @staticmethod
    def _make_action_button(text: str, bg: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(34)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {'#111827' if bg == '#EAB308' else '#FFFFFF'};
                border: 1px solid rgba(255,255,255,0.02);
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {bg};
            }}
        """)
        return btn

    # ------------------------------------------------------------------ #
    #  Slot handlers
    # ------------------------------------------------------------------ #
    def _on_pwm_changed(self, value: int) -> None:
        self._pwm_pct_lbl.setText(str(value))
        self.pwm_changed.emit(value)
        self._refresh_state_display()

    def _on_direction(self, direction: str) -> None:
        self._show_coming_soon()
        self._direction = direction
        is_fwd = direction == "FORWARD"
        self._fwd_btn.setStyleSheet(self._make_dir_button(
            "↑ Forward", "#10B981", "#059669", active=is_fwd
        ).styleSheet())
        self._rev_btn.setStyleSheet(self._make_dir_button(
            "↺ Reverse", "#475569", "#334155", active=not is_fwd
        ).styleSheet())
        self.direction_changed.emit(direction)
        self._refresh_state_display()

    def _on_start(self) -> None:
        self._show_coming_soon()
        self.set_running_state(True)
        self._estop_blink_timer.stop()
        self._estop_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        self.run_requested.emit()

    def _on_stop(self) -> None:
        self._show_coming_soon()
        self.set_running_state(False)
        self.stop_requested.emit()

    def _on_estop(self) -> None:
        self._show_coming_soon()
        self._running = False
        self._pwm_slider.animate_to(0)
        self.estop_requested.emit()
        self._refresh_state_display()
        # Blink E-STOP button after activation
        self._estop_blink_timer.start()

    def _blink_estop(self) -> None:
        self._estop_blink = not self._estop_blink
        color = "#EF4444" if self._estop_blink else "#B91C1C"
        self._estop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }}
        """)

    def _show_coming_soon(self) -> None:
        QMessageBox.information(self, "Coming Soon", "This feature is coming soon")

    def _refresh_state_display(self) -> None:
        """Update the state readout bar at top of the control panel (now handled by other UI)."""
        pass

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def get_pwm(self) -> int:
        return self._pwm_slider.value()

    def set_pwm(self, val: int) -> None:
        self._pwm_slider.animate_to(val)
        self._refresh_state_display()

    def get_direction(self) -> str:
        return self._direction

    def set_start_stop_enabled(self, enabled: bool) -> None:
        self._start_btn.setEnabled(enabled)
        self._stop_btn.setEnabled(enabled)

    def set_running_state(self, running: bool) -> None:
        self._running = running
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)

    def set_direction_state(self, direction: str) -> None:
        self._direction = direction
        is_fwd = direction == "FORWARD"
        self._fwd_btn.setStyleSheet(self._make_dir_button(
            "↑ Forward", "#10B981", "#059669", active=is_fwd
        ).styleSheet())
        self._rev_btn.setStyleSheet(self._make_dir_button(
            "↺ Reverse", "#475569", "#334155", active=not is_fwd
        ).styleSheet())
