"""
settings_page.py
----------------
Dedicated Settings page for the Smart Motor Test Bench.
Provides user configuration controls (toggles, dropdowns, line edits)
and handles saving/loading settings via JSON serialization to 'settings.json'.
"""

from __future__ import annotations

import json
import os
import pathlib
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QCheckBox, QLineEdit,
    QMessageBox, QScrollArea, QGridLayout, QSizePolicy
)

# Default configuration path
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
SETTINGS_FILE = ROOT_DIR / "settings.json"

class SettingsPage(QWidget):
    """
    Dedicated Settings Page.
    Emits settings_saved signal when changes are committed to JSON,
    allowing the MainWindow to dynamically alter the timer speed or theme.
    """
    settings_saved = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._load_settings()
        self._build_ui()
        self._apply_settings_to_ui()

    def _load_settings(self) -> None:
        """Load settings from JSON, fallback to defaults if not found."""
        self.defaults = {
            "theme": "Industrial Dark",
            "dark_mode": True,
            "refresh_rate_ms": 100,
            "baud_rate": 115200,
            "default_com_port": "COM3",
            "auto_connect": True
        }
        self.settings = dict(self.defaults)

        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Verify types match default dictionary keys
                    for key in self.defaults:
                        if key in loaded:
                            self.settings[key] = loaded[key]
            except Exception as e:
                print(f"Error loading settings: {e}")

    def _save_settings_to_file(self) -> None:
        """Commit current settings dict to JSON."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not write configuration:\n{str(e)}")

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title_lbl = QLabel("APPLICATION CONFIGURATION")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        root_layout.addWidget(title_lbl)

        # ── Settings Forms ─────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(18)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. UI Appearance Settings Group
        ui_card = self._make_card_base()
        ui_layout = QVBoxLayout(ui_card)
        ui_layout.setContentsMargins(20, 20, 20, 20)
        ui_layout.setSpacing(14)

        ui_title = QLabel("Appearance Settings")
        ui_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        ui_title.setStyleSheet("color: #007ACC; border: none; font-weight: 700;")
        ui_layout.addWidget(ui_title)

        grid_ui = QGridLayout()
        grid_ui.setSpacing(12)

        # Theme combobox
        lbl_theme = QLabel("Application Styling Palette")
        lbl_theme.setStyleSheet("color: #94A3B8; border: none;")
        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["Industrial Dark", "Siemens Teal", "Schneider Green", "ABB Red"])
        self._combo_theme.setStyleSheet(self._combo_style())
        grid_ui.addWidget(lbl_theme, 0, 0)
        grid_ui.addWidget(self._combo_theme, 0, 1)

        # Dark Mode checkbox
        lbl_dark = QLabel("Enable Premium Dark Mode Backdrop")
        lbl_dark.setStyleSheet("color: #94A3B8; border: none;")
        self._chk_dark = QCheckBox()
        self._chk_dark.setCursor(Qt.PointingHandCursor)
        self._chk_dark.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 2px;
                border: 1px solid #333333;
                background-color: #252526;
            }
            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border-color: #007ACC;
                image: url(icons/check.png); /* Fallback to drawn dot if image missing */
            }
        """)
        grid_ui.addWidget(lbl_dark, 1, 0)
        grid_ui.addWidget(self._chk_dark, 1, 1)

        ui_layout.addLayout(grid_ui)
        layout.addWidget(ui_card)

        # 2. Performance / Refresh Rate Group
        perf_card = self._make_card_base()
        perf_layout = QVBoxLayout(perf_card)
        perf_layout.setContentsMargins(20, 20, 20, 20)
        perf_layout.setSpacing(14)

        perf_title = QLabel("Telemetry Refresh Performance")
        perf_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        perf_title.setStyleSheet("color: #007ACC; border: none; font-weight: 700;")
        perf_layout.addWidget(perf_title)

        grid_perf = QGridLayout()
        grid_perf.setSpacing(12)

        lbl_refresh = QLabel("Graph Waveform Update Interval")
        lbl_refresh.setStyleSheet("color: #94A3B8; border: none;")
        self._combo_refresh = QComboBox()
        self._combo_refresh.addItem("Fast Performance (50 ms / 20 Hz)", 50)
        self._combo_refresh.addItem("Standard Dashboard (100 ms / 10 Hz)", 100)
        self._combo_refresh.addItem("Eco Diagnostic (200 ms / 5 Hz)", 200)
        self._combo_refresh.addItem("Idle Logging (500 ms / 2 Hz)", 500)
        self._combo_refresh.setStyleSheet(self._combo_style())
        grid_perf.addWidget(lbl_refresh, 0, 0)
        grid_perf.addWidget(self._combo_refresh, 0, 1)

        perf_layout.addLayout(grid_perf)
        layout.addWidget(perf_card)

        # 3. Connection / Serial Port Group
        conn_card = self._make_card_base()
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(20, 20, 20, 20)
        conn_layout.setSpacing(14)

        conn_title = QLabel("Hardware Interface Configurations")
        conn_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        conn_title.setStyleSheet("color: #007ACC; border: none; font-weight: 700;")
        conn_layout.addWidget(conn_title)

        grid_conn = QGridLayout()
        grid_conn.setSpacing(12)

        # Baud Rate
        lbl_baud = QLabel("Serial Link Baud Rate")
        lbl_baud.setStyleSheet("color: #94A3B8; border: none;")
        self._combo_baud = QComboBox()
        for baud in [9600, 19200, 38400, 57600, 115200]:
            self._combo_baud.addItem(f"{baud} bps", baud)
            self._combo_baud.setStyleSheet(self._combo_style())
        grid_conn.addWidget(lbl_baud, 0, 0)
        grid_conn.addWidget(self._combo_baud, 0, 1)

        # COM Port
        lbl_com = QLabel("Default Communication COM Port")
        lbl_com.setStyleSheet("color: #94A3B8; border: none;")
        self._txt_com = QLineEdit()
        self._txt_com.setFixedHeight(34)
        self._txt_com.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 0 8px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #007ACC;
            }
        """)
        grid_conn.addWidget(lbl_com, 1, 0)
        grid_conn.addWidget(self._txt_com, 1, 1)

        # Auto Connect
        lbl_autoconnect = QLabel("Auto Connect at Startup")
        lbl_autoconnect.setStyleSheet("color: #94A3B8; border: none;")
        self._chk_autoconnect = QCheckBox()
        self._chk_autoconnect.setCursor(Qt.PointingHandCursor)
        self._chk_autoconnect.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 2px;
                border: 1px solid #333333;
                background-color: #252526;
            }
            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border-color: #007ACC;
            }
        """)
        grid_conn.addWidget(lbl_autoconnect, 2, 0)
        grid_conn.addWidget(self._chk_autoconnect, 2, 1)

        conn_layout.addLayout(grid_conn)
        layout.addWidget(conn_card)

        # 4. Buttons Row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_reset = QPushButton("↺  RESET TO DEFAULTS")
        self._btn_reset.setFixedHeight(40)
        self._btn_reset.setFixedWidth(180)
        self._btn_reset.setCursor(Qt.PointingHandCursor)
        self._btn_reset.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn_reset.setStyleSheet("""
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
        self._btn_reset.clicked.connect(self._on_reset_clicked)

        self._btn_save = QPushButton("💾  SAVE SETTINGS")
        self._btn_save.setFixedHeight(40)
        self._btn_save.setFixedWidth(160)
        self._btn_save.setCursor(Qt.PointingHandCursor)
        self._btn_save.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn_save.setStyleSheet("""
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
        self._btn_save.clicked.connect(self._on_save_clicked)

        btn_row.addWidget(self._btn_reset)
        btn_row.addWidget(self._btn_save)
        layout.addLayout(btn_row)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

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
    def _combo_style() -> str:
        return """
            QComboBox {
                background-color: #252526;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 4px 10px;
                min-width: 220px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:focus {
                border-color: #007ACC;
            }
        """

    # ------------------------------------------------------------------ #
    #  State management
    # ------------------------------------------------------------------ #
    def _apply_settings_to_ui(self) -> None:
        """Bind settings dict state variables to active GUI options."""
        s = self.settings

        # Theme combobox
        idx_theme = self._combo_theme.findText(s["theme"])
        if idx_theme != -1:
            self._combo_theme.setCurrentIndex(idx_theme)

        # Dark mode checkbox
        self._chk_dark.setChecked(s["dark_mode"])

        # Refresh rate
        idx_refresh = self._combo_refresh.findData(s["refresh_rate_ms"])
        if idx_refresh != -1:
            self._combo_refresh.setCurrentIndex(idx_refresh)

        # Baud Rate
        idx_baud = self._combo_baud.findData(s["baud_rate"])
        if idx_baud != -1:
            self._combo_baud.setCurrentIndex(idx_baud)

        # COM Port
        self._txt_com.setText(s["default_com_port"])

        # Auto Connect
        self._chk_autoconnect.setChecked(s.get("auto_connect", True))

    def _on_save_clicked(self) -> None:
        """Pull settings from UI controls, save to JSON, emit settings_saved."""
        self.settings["theme"] = self._combo_theme.currentText()
        self.settings["dark_mode"] = self._chk_dark.isChecked()
        self.settings["refresh_rate_ms"] = self._combo_refresh.currentData()
        self.settings["baud_rate"] = self._combo_baud.currentData()
        self.settings["default_com_port"] = self._txt_com.text()
        self.settings["auto_connect"] = self._chk_autoconnect.isChecked()

        self._save_settings_to_file()
        self.settings_saved.emit(self.settings)

        QMessageBox.information(
            self, "Configuration Saved",
            "Application parameters successfully saved to settings.json."
        )

    def _on_reset_clicked(self) -> None:
        """Revert settings back to defaults and update GUI inputs."""
        confirm = QMessageBox.question(
            self, "Reset Application Settings",
            "Are you sure you want to revert settings back to default parameters?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.settings = dict(self.defaults)
            self._apply_settings_to_ui()
            self._save_settings_to_file()
            self.settings_saved.emit(self.settings)
            QMessageBox.information(self, "Reset Complete", "Settings reverted to defaults.")
