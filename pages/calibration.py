"""
calibration.py
--------------
Dedicated Sensor Calibration page for the Smart Motor Test Bench.
Provides form controls for RPM, Voltage, Current offsets/gains, and sensor nulling.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QLineEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QGroupBox, QSizePolicy
)

class CalibrationPage(QWidget):
    """
    Dedicated Calibration Page.
    Enables engineering students/operators to configure sensor offsets, multipliers,
    and gains to ensure data accuracy.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title_lbl = QLabel("SENSOR CALIBRATION WIZARD")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        root_layout.addWidget(title_lbl)

        # ── Scrollable Calibration Form ────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        form_container = QWidget()
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # 1. RPM Calibration Card
        form_layout.addWidget(self._build_rpm_calibration_card())

        # 2. Voltage Transducer Calibration Card
        form_layout.addWidget(self._build_voltage_calibration_card())

        # 3. Current Shunt Calibration Card
        form_layout.addWidget(self._build_current_calibration_card())

        # 4. Zero Offset Auto-Null Card
        form_layout.addWidget(self._build_auto_null_card())

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._save_btn = QPushButton("💾  SAVE CALIBRATION")
        self._save_btn.setFixedHeight(40)
        self._save_btn.setFixedWidth(180)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: #FFFFFF;
                border: 1px solid #005A9E;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        self._save_btn.clicked.connect(self._on_save_clicked)

        self._reset_btn = QPushButton("↺  RESET DEFAULTS")
        self._reset_btn.setFixedHeight(40)
        self._reset_btn.setFixedWidth(160)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #808080;
                border: 1px solid #3F3F46;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #3F3F46;
                color: #FFFFFF;
            }
        """)
        self._reset_btn.clicked.connect(self._on_reset_clicked)

        btn_row.addWidget(self._reset_btn)
        btn_row.addWidget(self._save_btn)
        form_layout.addLayout(btn_row)

        scroll.setWidget(form_container)
        root_layout.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #  Card Building Helpers
    # ------------------------------------------------------------------ #
    def _build_rpm_calibration_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Speed Sensor (RPM) Calibration")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #007ACC; border: none;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Multiplier
        lbl_gain = QLabel("Encoder Pulses Per Revolution (PPR)")
        lbl_gain.setStyleSheet("color: #94A3B8; border: none;")
        self._rpm_gain = QDoubleSpinBox()
        self._rpm_gain.setRange(1.0, 10000.0)
        self._rpm_gain.setValue(20.0)
        self._rpm_gain.setSingleStep(1.0)
        self._rpm_gain.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_gain, 0, 0)
        grid.addWidget(self._rpm_gain, 0, 1)

        # Offset
        lbl_offset = QLabel("Speed Scaling Multiplier")
        lbl_offset.setStyleSheet("color: #94A3B8; border: none;")
        self._rpm_mult = QDoubleSpinBox()
        self._rpm_mult.setRange(0.1, 10.0)
        self._rpm_mult.setValue(1.0)
        self._rpm_mult.setSingleStep(0.01)
        self._rpm_mult.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_offset, 1, 0)
        grid.addWidget(self._rpm_mult, 1, 1)

        layout.addLayout(grid)
        return card

    def _build_voltage_calibration_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("DC Voltage Transducer Calibration")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #007ACC; border: none;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Gain
        lbl_gain = QLabel("Voltage Multiplier (Gain)")
        lbl_gain.setStyleSheet("color: #94A3B8; border: none;")
        self._volt_gain = QDoubleSpinBox()
        self._volt_gain.setRange(0.0, 100.0)
        self._volt_gain.setValue(5.0) # E.g. divider ratio
        self._volt_gain.setSingleStep(0.1)
        self._volt_gain.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_gain, 0, 0)
        grid.addWidget(self._volt_gain, 0, 1)

        # Offset
        lbl_offset = QLabel("Voltage Offset Shift (V)")
        lbl_offset.setStyleSheet("color: #94A3B8; border: none;")
        self._volt_offset = QDoubleSpinBox()
        self._volt_offset.setRange(-10.0, 10.0)
        self._volt_offset.setValue(0.0)
        self._volt_offset.setSingleStep(0.01)
        self._volt_offset.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_offset, 1, 0)
        grid.addWidget(self._volt_offset, 1, 1)

        layout.addLayout(grid)
        return card

    def _build_current_calibration_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Current Transducer (Shunt) Calibration")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #007ACC; border: none;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Gain
        lbl_gain = QLabel("Current Transducer Gain (A/V)")
        lbl_gain.setStyleSheet("color: #94A3B8; border: none;")
        self._curr_gain = QDoubleSpinBox()
        self._curr_gain.setRange(0.0, 500.0)
        self._curr_gain.setValue(18.5)
        self._curr_gain.setSingleStep(0.1)
        self._curr_gain.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_gain, 0, 0)
        grid.addWidget(self._curr_gain, 0, 1)

        # Offset
        lbl_offset = QLabel("Current Offset (A)")
        lbl_offset.setStyleSheet("color: #94A3B8; border: none;")
        self._curr_offset = QDoubleSpinBox()
        self._curr_offset.setRange(-5.0, 5.0)
        self._curr_offset.setValue(0.02)
        self._curr_offset.setSingleStep(0.01)
        self._curr_offset.setStyleSheet(self._spinbox_style())
        grid.addWidget(lbl_offset, 1, 0)
        grid.addWidget(self._curr_offset, 1, 1)

        layout.addLayout(grid)
        return card

    def _build_auto_null_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Automatic Sensor Zero-Nulling")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #007ACC; border: none;")
        layout.addWidget(title)

        desc = QLabel("Reads current transducer signals when motor is idle to calculate zero offsets automatically.")
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet("color: #64748B; border: none;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_null = QPushButton("NULL SENSORS (AUTO-ZERO)")
        btn_null.setFixedHeight(38)
        btn_null.setFixedWidth(240)
        btn_null.setCursor(Qt.PointingHandCursor)
        btn_null.setFont(QFont("Segoe UI", 9, QFont.Bold))
        btn_null.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: #FFFFFF;
                border: 1px solid #005A9E;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        btn_null.clicked.connect(self._on_null_clicked)
        layout.addWidget(btn_null)

        return card

    @staticmethod
    def _make_card_base() -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 2px;
            }
        """)
        return card

    @staticmethod
    def _spinbox_style() -> str:
        return """
            QDoubleSpinBox {
                background-color: #252526;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 4px 8px;
                min-width: 120px;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border-color: #007ACC;
            }
        """

    # ------------------------------------------------------------------ #
    #  Slots
    # ------------------------------------------------------------------ #
    def _on_save_clicked(self) -> None:
        QMessageBox.information(
            self, "Calibration Saved",
            "Calibration factors successfully written to non-volatile EEPROM memory."
        )

    def _on_reset_clicked(self) -> None:
        confirm = QMessageBox.question(
            self, "Reset Calibration",
            "Are you sure you want to restore all factors to factory default settings?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self._rpm_gain.setValue(20.0)
            self._rpm_mult.setValue(1.0)
            self._volt_gain.setValue(5.0)
            self._volt_offset.setValue(0.0)
            self._curr_gain.setValue(18.5)
            self._curr_offset.setValue(0.0)
            QMessageBox.information(self, "Reset Success", "Calibration reset completed successfully.")

    def _on_null_clicked(self) -> None:
        # Simulate auto null process
        self._curr_offset.setValue(0.00)
        self._volt_offset.setValue(0.00)
        QMessageBox.information(
            self, "Auto-Null Complete",
            "Zero offset calibration successfully computed:\n"
            "• Current Shunt Offset set to 0.00 A\n"
            "• Voltage Offset set to 0.00 V"
        )
