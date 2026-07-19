"""
main.py
-------
Smart Motor Test Bench – Application entry point.

Responsibilities:
  1. Bootstrap PySide6 and load the global QSS stylesheet.
  2. Load user preferences from settings.json at startup.
  3. Instantiate the shared DataGenerator and SerialManager.
  4. Create and show the MainWindow with cross-fade page transitions.
  5. Start the configurable-interval data-update QTimer.
  6. Enter the Qt event loop.

Run with::

    python main.py
"""

from __future__ import annotations

import sys
import os
import json
import pathlib
import datetime
import csv


# ── Ensure project root is on sys.path ──────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QPoint, QParallelAnimationGroup
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QFrame, QSizePolicy, QGraphicsOpacityEffect, QPushButton,
    QGraphicsDropShadowEffect, QFileDialog,
)

from backend.data_generator import DataGenerator
from backend.serial_manager import SerialManager
from widgets.sidebar import Sidebar
from widgets.toast import ToastNotification
from pages.dashboard import Dashboard
from pages.live_graphs import LiveGraphsPage
from pages.data_log import DataLogPage
from pages.control_panel_page import ControlPanelPage
from pages.calibration import CalibrationPage
from pages.settings_page import SettingsPage
from pages.about import AboutPage
from widgets.splash_screen import SplashScreen

# Path to the settings file
SETTINGS_FILE = ROOT / "settings.json"


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _connection_status_text(connected: bool, port: str | None = None) -> str:
    """Return the compact status text shown in the bottom-left connection label."""
    if connected and port:
        return f"CONNECTED ({port})"
    return "NOT CONNECTED"


def _load_settings() -> dict:
    """Load application settings from JSON; fall back to built-in defaults."""
    defaults = {
        "theme": "Industrial Dark",
        "dark_mode": True,
        "refresh_rate_ms": 100,
        "baud_rate": 115200,
        "default_com_port": "COM3",
    }
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for key in defaults:
                if key in loaded:
                    defaults[key] = loaded[key]
        except Exception as e:
            print(f"[settings] Could not load settings.json – using defaults. ({e})")
    return defaults


# ──────────────────────────────────────────────────────────────────────────────
#  Fade-transition helper
# ──────────────────────────────────────────────────────────────────────────────

class _FadingStack(QStackedWidget):
    """
    QStackedWidget with a 180 ms fade-in animation each time the current
    widget is changed.  Call setCurrentIndex() or setCurrentWidget() as normal.
    """
    _FADE_MS = 180

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802 (Qt override)
        super().setCurrentIndex(index)
        widget = self.currentWidget()
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(self._FADE_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start()


# ──────────────────────────────────────────────────────────────────────────────
#  Header Status Cards
# ──────────────────────────────────────────────────────────────────────────────

class TopBarCard(QFrame):
    """Base style for the new top bar cards."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setStyleSheet("""
            TopBarCard {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

class LiveStatusCard(TopBarCard):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(130)
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        
        self.live_lbl = QLabel("● LIVE")
        self.live_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.live_lbl.setStyleSheet("color: #10B981; border: none; background: transparent;")
        self.live_lbl.setAlignment(Qt.AlignCenter)
        
        self.text_lbl = QLabel("System Online")
        self.text_lbl.setFont(QFont("Segoe UI", 8))
        self.text_lbl.setStyleSheet("color: #E2E8F0; border: none; background: transparent;")
        self.text_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.live_lbl)
        layout.addWidget(self.text_lbl)

    def set_status(self, title: str, value: str, accent_color: str) -> None:
        self.live_lbl.setText(f"● {title.upper()}")
        self.live_lbl.setStyleSheet(f"color: {accent_color}; border: none; background: transparent;")
        self.text_lbl.setText(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class ComPortCard(TopBarCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        
        title_lbl = QLabel("COM PORT")
        title_lbl.setFont(QFont("Segoe UI", 7, QFont.Bold))
        title_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        title_lbl.setAlignment(Qt.AlignCenter)
        
        self.value_lbl = QLabel("COM3")
        self.value_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.value_lbl.setStyleSheet("color: #3B82F6; border: none; background: transparent;")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_lbl)
        layout.addWidget(self.value_lbl)

    def set_value(self, value: str) -> None:
        self.value_lbl.setText(value)

class TimeCard(TopBarCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(150)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        time_icon = QLabel()
        time_icon.setFixedSize(24, 24)
        time_icon.setPixmap(QPixmap(str(ROOT / "assets" / "clock.svg")).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        time_icon.setStyleSheet("border: none; background: transparent;")
        
        time_text_layout = QVBoxLayout()
        time_text_layout.setAlignment(Qt.AlignVCenter)
        time_text_layout.setSpacing(0)
        t_title = QLabel("TIME")
        t_title.setFont(QFont("Segoe UI", 7, QFont.Bold))
        t_title.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        self.time_val = QLabel("00:00:00")
        self.time_val.setMinimumWidth(85)
        self.time_val.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.time_val.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        time_text_layout.addWidget(t_title)
        time_text_layout.addWidget(self.time_val)
        
        layout.addWidget(time_icon)
        layout.addLayout(time_text_layout)

class FirmwareCard(TopBarCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(130)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        fw_icon = QLabel()
        fw_icon.setFixedSize(24, 24)
        fw_icon.setPixmap(QPixmap(str(ROOT / "assets" / "cpu.svg")).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        fw_icon.setStyleSheet("border: none; background: transparent;")
        
        fw_text_layout = QVBoxLayout()
        fw_text_layout.setAlignment(Qt.AlignVCenter)
        fw_text_layout.setSpacing(0)
        f_title = QLabel("FIRMWARE")
        f_title.setFont(QFont("Segoe UI", 7, QFont.Bold))
        f_title.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        self.fw_val = QLabel("v1.0.0")
        self.fw_val.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.fw_val.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        fw_text_layout.addWidget(f_title)
        fw_text_layout.addWidget(self.fw_val)
        
        layout.addWidget(fw_icon)
        layout.addLayout(fw_text_layout)


class ExportCard(TopBarCard):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # Icon
        self.icon_lbl = QLabel("📤")
        self.icon_lbl.setFont(QFont("Segoe UI Symbol", 13))
        self.icon_lbl.setStyleSheet("border: none; background: transparent; color: #3B82F6;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedWidth(24)
        
        # Text layout
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignVCenter)
        text_layout.setSpacing(0)
        
        self.sub_lbl = QLabel("Export")
        self.sub_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.sub_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        
        text_layout.addWidget(self.sub_lbl)
        
        # Arrow
        arrow_lbl = QLabel("▼")
        arrow_lbl.setFont(QFont("Segoe UI", 7))
        arrow_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        arrow_lbl.setFixedWidth(10)
        arrow_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.icon_lbl)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(arrow_lbl)
        
        self._update_style(hovered=False)
        
    def _update_style(self, hovered: bool):
        bg = "#1A2234" if hovered else "#111827"
        border_color = "#3B82F6" if hovered else "rgba(255, 255, 255, 0.08)"
        self.setStyleSheet(f"""
            ExportCard {{
                background-color: {bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        
    def enterEvent(self, event):
        self._update_style(hovered=True)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._update_style(hovered=False)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DropdownMenuItem(QWidget):
    clicked = Signal()

    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(54)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Symbol", 14))
        icon_lbl.setStyleSheet("color: #3B82F6; border: none; background: transparent;")
        icon_lbl.setFixedWidth(24)
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setAlignment(Qt.AlignVCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #F1F5F9; border: none; background: transparent;")
        
        desc_lbl = QLabel(description)
        desc_lbl.setFont(QFont("Segoe UI", 7))
        desc_lbl.setStyleSheet("color: #64748B; border: none; background: transparent;")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)
        
        layout.addWidget(icon_lbl)
        layout.addLayout(text_layout, stretch=1)
        
        self._update_style(hovered=False)
        
    def _update_style(self, hovered: bool):
        bg = "rgba(255, 255, 255, 0.06)" if hovered else "transparent"
        self.setStyleSheet(f"""
            DropdownMenuItem {{
                background-color: {bg};
                border-radius: 6px;
            }}
        """)
        
    def enterEvent(self, event):
        self._update_style(hovered=True)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._update_style(hovered=False)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ExportDropdownMenu(QWidget):
    item_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedWidth(270) # 250 menu width + 20 shadow margins
        
        # Container frame manually sized
        self.container = QFrame(self)
        self.container.setObjectName("menuContainer")
        self.container.resize(250, 170)
        self.container.setStyleSheet("""
            #menuContainer {
                background-color: #0F172A;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
        """)
        
        # Layout inside container
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(6, 6, 6, 6)
        self.container_layout.setSpacing(2)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        # Menu items
        items = [
            ("📄", "Export Report (PDF)", "Generate complete performance report."),
            ("📊", "Export Data (CSV)", "Export all sensor readings."),
            ("🖼", "Export Dashboard (PNG)", "Save dashboard as high-resolution image."),
        ]
        
        for icon, title, desc in items:
            item_widget = DropdownMenuItem(icon, title, desc, self)
            item_widget.clicked.connect(lambda t=title: self._on_item_clicked(t))
            self.container_layout.addWidget(item_widget)
            
        self.setFixedHeight(170 + 20)
        
    def _on_item_clicked(self, title: str):
        self.close()
        self.item_selected.emit(title)
        
    def show_menu(self, global_pos: QPoint):
        self.move(global_pos.x() - 10, global_pos.y())
        
        # Start animations
        self.setWindowOpacity(0.0)
        self.container.move(10, 0)
        
        self.show()
        
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(150)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        
        self.slide_anim = QPropertyAnimation(self.container, b"pos")
        self.slide_anim.setDuration(150)
        self.slide_anim.setStartValue(QPoint(10, 0))
        self.slide_anim.setEndValue(QPoint(10, 10))
        self.slide_anim.setEasingCurve(QEasingCurve.OutQuad)
        
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.fade_anim)
        self.anim_group.addAnimation(self.slide_anim)
        self.anim_group.start()


# ──────────────────────────────────────────────────────────────────────────────
#  Main Application Window
# ──────────────────────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """
    Top-level application window.

    Hosts the sidebar, page stack, and status bar.
    All data updates are driven by a single configurable-interval QTimer.
    """

    def __init__(
        self,
        data_gen: DataGenerator,
        settings: dict,
    ) -> None:
        super().__init__()
        self._data = data_gen
        self._serial = None # Instantiated after splash screen finishes
        self._settings = settings
        self._conn_dot: QLabel | None = None
        self._conn_lbl: QLabel | None = None
        self._last_connection_state: bool = False
        self._start_time = datetime.datetime.now()

        self.setWindowTitle("Smart Motor Test Bench")
        self.setMinimumSize(1280, 720)
        self.showMaximized()

        self._build_ui()
        self._apply_stylesheet()

    def initialize_serial_connection(self) -> None:
        """Create the SerialManager, link it to pages, and start monitoring timers."""
        from backend.serial_manager import SerialManager
        self._serial = SerialManager()
        
        # Link serial manager to data generator
        self._data.set_serial_manager(self._serial)
        
        # Propagate the shared SerialManager to pages
        self._dashboard._serial = self._serial
        self._live_graphs._serial = self._serial
        self._ctrl_page._serial = self._serial
        
        # Start application updates and polling
        self.start_application_timers()

    def start_application_timers(self) -> None:
        """Start periodic telemetry, serial polling, and connection timers."""
        self._start_data_timer()
        self._start_serial_poll_timer()
        self._start_connection_timer()

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        """Assemble the main window layout."""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        # Root layout spans vertically to hold full-width header at the top
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top Header (Premium SCADA Header spanning entire width) ─────
        self.header = QWidget()
        self.header.setFixedHeight(92)
        self.header.setObjectName("appHeader")
        self.header.setStyleSheet("""
            #appHeader {
                background-color: #08101F;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(22, 10, 22, 10)
        header_layout.setSpacing(14)

        # Toggle Sidebar Button
        self._toggle_sidebar_btn = QPushButton("≡")
        self._toggle_sidebar_btn.setFixedSize(40, 40)
        self._toggle_sidebar_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_sidebar_btn.setFont(QFont("Segoe UI Symbol", 20))
        self._toggle_sidebar_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        self._toggle_sidebar_btn.clicked.connect(self._toggle_sidebar)
        header_layout.addWidget(self._toggle_sidebar_btn)

        # Logo (left)
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(64, 64)
        logo_lbl.setStyleSheet("border: none; background: transparent;")
        logo_path = ROOT / "assets" / "motor_logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaledToHeight(56, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("⚙️")
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setFont(QFont("Segoe UI", 24))
        header_layout.addWidget(logo_lbl)

        # Title Block next to Logo
        title_block = QWidget()
        title_block.setStyleSheet("background: transparent; border: none;")
        tb_layout = QVBoxLayout(title_block)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(4)
        
        title_lbl = QLabel("SMART MOTOR TEST BENCH")
        title_lbl.setFont(QFont("Segoe UI", 18, QFont.Black))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px; border: none; background: transparent;")
        
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(56, 189, 248, 255))
        glow.setOffset(0, 0)
        title_lbl.setGraphicsEffect(glow)
        
        subtitle_lbl = QLabel("Real-Time Motor Performance Monitoring System")
        subtitle_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        subtitle_lbl.setStyleSheet("""
            QLabel {
                color: #7DD3FC; 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(56, 189, 248, 0.25), stop:1 rgba(14, 165, 233, 0.1));
                border: 1px solid rgba(56, 189, 248, 0.5);
                border-radius: 4px;
                padding: 3px 10px;
            }
        """)
        
        tb_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)
        tb_layout.addWidget(subtitle_lbl, alignment=Qt.AlignLeft)
        header_layout.addWidget(title_block)

        header_layout.addStretch()

        # Right status cluster
        status_cluster = QWidget()
        status_cluster.setStyleSheet("background: transparent; border: none;")
        sc_layout = QHBoxLayout(status_cluster)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(12)

        # Export Card
        self._export_card = ExportCard()
        self._export_card.clicked.connect(self._show_export_menu)
        sc_layout.addWidget(self._export_card)

        # Connection Status Card
        self._conn_card = LiveStatusCard()
        self._conn_card.clicked.connect(self._on_conn_card_clicked)
        sc_layout.addWidget(self._conn_card)

        # COM Port Card
        self._com_card = ComPortCard()
        self._com_card.set_value(self._settings.get("default_com_port", "COM3"))
        sc_layout.addWidget(self._com_card)

        # Time Card
        self._time_card = TimeCard()
        self._header_clock_lbl = self._time_card.time_val
        sc_layout.addWidget(self._time_card)
        
        # Firmware Card
        self._fw_card = FirmwareCard()
        self._fw_card.fw_val.setText("v1.1.2")
        sc_layout.addWidget(self._fw_card)

        # Settings button
        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(52, 52)
        self._settings_btn.setFont(QFont("Segoe UI Symbol", 28, QFont.Black))
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #94A3B8;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1A2030;
                color: #FFFFFF;
            }
        """)
        self._settings_btn.clicked.connect(lambda: (self._sidebar.set_active_page(5), self._switch_page(5)))
        sc_layout.addWidget(self._settings_btn)

        header_layout.addWidget(status_cluster)
        root_layout.addWidget(self.header)

        # ── Main Content Area (Sidebar + Pages stack side-by-side) ──────
        content_container = QWidget()
        content_container.setStyleSheet("background-color: transparent;")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)
        content_layout.addWidget(self._sidebar)

        # Page stack (fading transitions)
        self._pages = _FadingStack()
        self._pages.setStyleSheet("QStackedWidget { background-color: transparent; }")

        # Instantiate all pages – pass data_gen where needed
        self._splash        = SplashScreen(ROOT / "assets")
        self._dashboard     = Dashboard(self._data, self._serial, self._settings)
        self._live_graphs   = LiveGraphsPage(self._serial)
        self._data_log      = DataLogPage()
        self._ctrl_page     = ControlPanelPage(self._data, self._serial)
        self._calibration   = CalibrationPage()
        self._settings_page = SettingsPage()
        self._about         = AboutPage()

        # Connect settings_saved signal so refresh interval can be updated live
        self._settings_page.settings_saved.connect(self._on_settings_saved)

        # First page is splash screen
        for page in (
            self._splash,
            self._dashboard,
            self._live_graphs,
            self._data_log,
            self._ctrl_page,
            self._calibration,
            self._settings_page,
            self._about,
        ):
            self._pages.addWidget(page)

        content_layout.addWidget(self._pages, stretch=1)
        root_layout.addWidget(content_container, stretch=1)

        # Hide header and sidebar during the splash screen
        self.header.hide()
        self._sidebar.hide()
        self._pages.setCurrentIndex(0)
        
        # Connect splash finished signal to handle transition
        self._splash.loading_finished.connect(self._on_splash_finished)

        # ── Status bar ─────────────────────────────────────────────────
        self._build_status_bar()

    # ------------------------------------------------------------------ #
    #  Status bar
    # ------------------------------------------------------------------ #
    def _build_status_bar(self) -> None:
        """Construct the bottom status bar with SCADA details."""
        bar = self.statusBar()
        bar.setStyleSheet("QStatusBar::item { border: none; }")

        # Connection status label
        self._sb_conn_lbl = self._status_label("● DISCONNECTED", "#EF4444")
        self._sb_conn_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        bar.addWidget(self._sb_conn_lbl)

        bar.addWidget(self._status_sep())

        # COM Port
        self._sb_port_lbl = self._status_label(f"💻 {self._settings.get('default_com_port', 'COM3')}")
        bar.addWidget(self._sb_port_lbl)

        bar.addWidget(self._status_sep())

        # Baud Rate
        self._sb_baud_lbl = self._status_label(f"⚡ {self._settings.get('baud_rate', 115200)} bps")
        bar.addWidget(self._sb_baud_lbl)

        bar.addWidget(self._status_sep())

        # Device
        self._sb_device_lbl = self._status_label("🔌 Arduino UNO")
        bar.addWidget(self._sb_device_lbl)

        # Right side permanent widgets (from right to left)
        self._sb_time_lbl = self._status_label("🕒 --:--:--")
        bar.addPermanentWidget(self._sb_time_lbl)

        bar.addPermanentWidget(self._status_sep())

        self._sb_date_lbl = self._status_label("📅 -- --- ----")
        bar.addPermanentWidget(self._sb_date_lbl)

        bar.addPermanentWidget(self._status_sep())

        self._sb_uptime_lbl = self._status_label("⏱ Uptime: 00:00:00")
        bar.addPermanentWidget(self._sb_uptime_lbl)

        bar.addPermanentWidget(self._status_sep())

        bar.addPermanentWidget(self._status_label("Built with ♥ by EE Student", "#007ACC"))

        # Tick the header clock every second
        sb_clock = QTimer(self)
        sb_clock.setInterval(1000)
        sb_clock.timeout.connect(self._update_sb_clock)
        sb_clock.start()
        self._update_sb_clock()

    @staticmethod
    def _status_label(text: str, color: str = "#475569") -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 11px; padding: 0 6px; font-weight: 500;")
        return lbl

    @staticmethod
    def _status_sep() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #1E293B; border: none;")
        return sep

    # ------------------------------------------------------------------ #
    #  Stylesheet
    # ------------------------------------------------------------------ #
    def _apply_stylesheet(self) -> None:
        """Load and apply the global QSS theme."""
        qss_path = ROOT / "styles" / "dark.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as fh:
                self.setStyleSheet(fh.read())

    # ------------------------------------------------------------------ #
    #  Data timer
    # ------------------------------------------------------------------ #
    def _start_data_timer(self) -> None:
        """Start the periodic data-update timer using the loaded refresh rate."""
        interval = self._settings.get("refresh_rate_ms", 100)
        self._timer = QTimer(self)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def _start_serial_poll_timer(self) -> None:
        """Poll the serial port every 50 ms without blocking the UI thread."""
        self._serial_poll_timer = QTimer(self)
        self._serial_poll_timer.setInterval(50)
        self._serial_poll_timer.timeout.connect(self._poll_serial_data)
        self._serial_poll_timer.start()

    def _start_connection_timer(self) -> None:
        """Start the background timer that keeps attempting Arduino reconnects."""
        self._connection_timer = QTimer(self)
        self._connection_timer.setInterval(2500) # Retry every 2.5 seconds
        self._connection_timer.timeout.connect(self._on_connection_timer)
        self._connection_timer.start()
        self._on_connection_timer()

    def _on_splash_finished(self) -> None:
        """Called when the splash screen loading finishes to transition to Dashboard."""
        # Fade-in effect for the header
        h_effect = QGraphicsOpacityEffect(self.header)
        self.header.setGraphicsEffect(h_effect)
        self.header.show()
        self._header_anim = QPropertyAnimation(h_effect, b"opacity", self)
        self._header_anim.setDuration(300)
        self._header_anim.setStartValue(0.0)
        self._header_anim.setEndValue(1.0)
        self._header_anim.start()

        # Fade-in effect for the sidebar
        s_effect = QGraphicsOpacityEffect(self._sidebar)
        self._sidebar.setGraphicsEffect(s_effect)
        self._sidebar.show()
        self._sidebar_anim = QPropertyAnimation(s_effect, b"opacity", self)
        self._sidebar_anim.setDuration(300)
        self._sidebar_anim.setStartValue(0.0)
        self._sidebar_anim.setEndValue(1.0)
        self._sidebar_anim.start()

        # Switch stacked widget index to Dashboard (index 1) with cross-fade
        self._pages.setCurrentIndex(1)
        
        # Initialize serial manager and start timers after the dashboard opens
        self.initialize_serial_connection()

    def _on_tick(self) -> None:
        """Called every timer interval to update the active page with the latest data."""
        self._data.update()
        idx = self._pages.currentIndex()
        if idx == 1: # Index 1 is Dashboard
            self._dashboard.update_data()
        elif idx == 2: # Index 2 is LiveGraphsPage
            self._live_graphs.update_data()

        if hasattr(self, '_sb_uptime_lbl') and self._sb_uptime_lbl:
            self._sb_uptime_lbl.setText(f"⏱ Uptime: {self._data.uptime}")

    def _poll_serial_data(self) -> None:
        """Read any pending serial bytes without blocking the UI thread."""
        if self._serial and self._serial.is_connected:
            self._serial.consume_serial_data()

    def _on_connection_timer(self) -> None:
        """Periodic connection health check and reconnect scheduler."""
        if not self._serial:
            self._update_connection_status(False)
            return
        is_connected = self._serial.is_connected

        if is_connected:
            if self._serial.check_connection():
                if self._last_connection_state is False:
                    self._on_serial_connected()
                self._last_connection_state = True
                return

            self._on_serial_disconnected()
            self._last_connection_state = False
            return

        # Disconnected path: attempt to reconnect only if auto_connect setting is enabled
        if not self._settings.get("auto_connect", True):
            self._update_connection_status(False)
            return

        desired_port = self._settings.get("default_com_port", "COM3")
        available_ports = SerialManager.list_available_ports()

        if desired_port not in available_ports:
            self._update_connection_status(False)
            return

        if self._serial.connect(desired_port, self._settings.get("baud_rate", 115200)):
            self._on_serial_connected()
            self._last_connection_state = True
        else:
            self._update_connection_status(False)
            self._last_connection_state = False

    # ------------------------------------------------------------------ #
    #  Connection management
    # ------------------------------------------------------------------ #
    def _on_serial_connected(self) -> None:
        """Handle a newly established serial connection."""
        self._update_connection_status(True)
        self._dashboard.set_start_stop_enabled(True)
        self._ctrl_page.set_start_stop_enabled(True)
        # Toast disabled as requested: connection status is visible in headers/status bar
        # self._show_toast("Arduino Connected")

    def _on_serial_disconnected(self) -> None:
        """Handle a serial disconnection event and reset UI state."""
        if self._serial:
            self._serial.disconnect()
        self._update_connection_status(False)
        self._dashboard.reset_on_disconnect()
        self._live_graphs.clear_all_graphs()
        self._ctrl_page.set_start_stop_enabled(False)
        self._dashboard.set_start_stop_enabled(False)
        # Toast disabled as requested: connection status is visible in headers/status bar
        # self._show_toast("Arduino Disconnected - Controls Disabled")

    def _on_conn_card_clicked(self) -> None:
        """Manually toggle the serial connection when clicking the status card."""
        if not self._serial:
            return
        
        if self._serial.is_connected:
            self._on_serial_disconnected()
        else:
            self._show_toast("Attempting to connect...")
            port = self._settings.get("default_com_port", "COM3")
            baud = self._settings.get("baud_rate", 115200)
            if self._serial.connect(port, baud):
                self._on_serial_connected()
                self._last_connection_state = True
            else:
                self._update_connection_status(False)
                self._last_connection_state = False
                err = self._serial._last_error or "Unknown error"
                self._show_toast(f"Connection Failed: {err}")

    def _check_and_update_connection_status(self) -> None:
        """
        Deprecated compatibility hook; connection management is handled by the
        background reconnect timer.
        """
        pass
    
    def _update_connection_status(self, connected: bool) -> None:
        """Update the status bar connection indicators."""
        port = self._settings.get("default_com_port", "COM3")
        baud = self._settings.get("baud_rate", 115200)

        # Update Header Cards
        if hasattr(self, '_conn_card') and self._conn_card:
            if connected:
                self._conn_card.set_status("LIVE", "System Online", "#10B981")
            else:
                self._conn_card.set_status("OFFLINE", "Waiting for Arduino...", "#EF4444")

        if hasattr(self, '_com_card') and self._com_card:
            self._com_card.set_value(port if connected else "None")

        # Update Status Bar widgets
        if hasattr(self, '_sb_conn_lbl') and self._sb_conn_lbl:
            if connected:
                self._sb_conn_lbl.setText("● CONNECTED")
                self._sb_conn_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
            else:
                self._sb_conn_lbl.setText("● OFFLINE (Waiting for Arduino...)")
                self._sb_conn_lbl.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;")

        if hasattr(self, '_sb_port_lbl') and self._sb_port_lbl:
            self._sb_port_lbl.setText(f"💻 {port if connected else 'None'}")

        if hasattr(self, '_sb_baud_lbl') and self._sb_baud_lbl:
            self._sb_baud_lbl.setText(f"⚡ {baud} bps")

    def _show_toast(self, message: str) -> None:
        toast = ToastNotification(self, message)
        toast.show_toast()

    # ------------------------------------------------------------------ #
    #  Slot helpers
    # ------------------------------------------------------------------ #
    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        if self._sidebar.isVisible():
            self._sidebar.hide()
        else:
            self._sidebar.show()

    def _switch_page(self, index: int) -> None:
        """Switch the visible page in the stacked widget."""
        self._pages.setCurrentIndex(index + 1)

    def _on_settings_saved(self, settings: dict) -> None:
        """React to settings changes emitted by the SettingsPage."""
        new_interval = settings.get("refresh_rate_ms", 100)
        if self._timer.interval() != new_interval:
            self._timer.setInterval(new_interval)
        self._settings = settings
        self._dashboard.update_settings(settings)

    def _update_sb_clock(self) -> None:
        """Update the header clock and status bar permanent widgets every second."""
        now = datetime.datetime.now()
        if hasattr(self, '_header_clock_lbl') and self._header_clock_lbl:
            self._header_clock_lbl.setText(now.strftime("%I:%M:%S %p"))
        if hasattr(self, '_sb_date_lbl') and self._sb_date_lbl:
            self._sb_date_lbl.setText(f"📅 {now.strftime('%d %b %Y')}")
        if hasattr(self, '_sb_time_lbl') and self._sb_time_lbl:
            self._sb_time_lbl.setText(f"🕒 {now.strftime('%I:%M:%S %p')}")
        if hasattr(self, '_start_time') and hasattr(self, '_sb_uptime_lbl') and self._sb_uptime_lbl:
            delta = now - self._start_time
            seconds = int(delta.total_seconds())
            hours, remainder = divmod(seconds, 3600)
            minutes, secs = divmod(remainder, 60)
            self._sb_uptime_lbl.setText(f"⏱ Uptime: {hours:02d}:{minutes:02d}:{secs:02d}")

    def _show_export_menu(self) -> None:
        """Position and show the export dropdown menu right under the Export card."""
        if not hasattr(self, "_export_menu") or self._export_menu is None:
            self._export_menu = ExportDropdownMenu(self)
            self._export_menu.item_selected.connect(self._on_export_item_selected)
            
        gp = self._export_card.mapToGlobal(self._export_card.rect().bottomLeft())
        self._export_menu.show_menu(QPoint(gp.x(), gp.y() + 4))

    def _on_export_item_selected(self, item_title: str) -> None:
        if item_title == "Export Report (PDF)":
            self._export_report_pdf()
        elif item_title == "Export Data (CSV)":
            self._export_data_csv()
        elif item_title == "Export Dashboard (PNG)":
            self._export_dashboard_png()
        elif item_title == "Capture Screenshot":
            self._capture_screenshot()
        elif item_title == "Export Settings":
            self._export_settings_info()

    def _export_report_pdf(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report to PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return
            
        temp_files_to_clean: list[str] = []

        try:
            import os
            import tempfile
            import datetime
            from PySide6.QtGui import QPdfWriter, QPainter, QPageLayout, QPageSize, QPen, QBrush, QPixmap, QColor, QFont
            from PySide6.QtCore import Qt
            from PySide6.QtWidgets import QApplication, QMessageBox
            from widgets.graph_widget import RealtimeGraph
            
            # 1. Gather historical plotting data from dashboard or live graphs
            times: list[float] = []
            history_values: dict[str, list[float]] = {}
            if hasattr(self, "_dashboard") and self._dashboard and self._dashboard._history_times:
                times = list(self._dashboard._history_times)
                history_values = {k: list(v) for k, v in self._dashboard._history_values.items()}
            elif hasattr(self, "_live_graphs") and self._live_graphs and self._live_graphs._graph_rpm._times:
                times = list(self._live_graphs._graph_rpm._times)
                history_values = {
                    "RPM": list(self._live_graphs._graph_rpm._values),
                    "Voltage": list(self._live_graphs._graph_volt._values),
                    "Current": list(self._live_graphs._graph_curr._values),
                    "Power": list(self._live_graphs._graph_pwr._values),
                    "Efficiency": list(self._live_graphs._graph_eff._values),
                    "Temperature": list(self._live_graphs._graph_temp._values),
                }

            # 2. Export every graph as a high-resolution PNG image
            graph_specs = [
                ("RPM", "Speed (RPM) vs Time", "RPM", "rpm", "#10B981"),
                ("Voltage", "Voltage vs Time", "Voltage", "V", "#3B82F6"),
                ("Current", "Current vs Time", "Current", "A", "#F59E0B"),
                ("Power", "Power vs Time", "Power", "W", "#8B5CF6"),
                ("Temperature", "Temperature vs Time", "Temperature", "°C", "#F97316"),
                ("Efficiency", "Efficiency vs Time", "Efficiency", "%", "#06B6D4"),
            ]

            temp_png_paths: dict[str, str] = {}

            for key, title, y_label, y_unit, line_color in graph_specs:
                # Create dedicated graph widget for high-res capture
                export_graph = RealtimeGraph(title, y_label, y_unit, line_color)
                export_graph.setFixedSize(1400, 700)

                # Populate with plotted data currently visible on screen
                vals = history_values.get(key, [])
                export_graph.set_data(times, vals)

                # Ensure fully rendered and force canvas repaint
                export_graph.show()
                export_graph.ensurePolished()
                export_graph.repaint()
                export_graph._plot_widget.repaint()
                QApplication.processEvents()

                # Capture actual plotting canvas (_plot_widget), not parent container
                pixmap = export_graph._plot_widget.grab()

                # Save to temporary PNG file
                temp_file = tempfile.NamedTemporaryFile(suffix=f"_{key}.png", delete=False)
                temp_path = temp_file.name
                temp_file.close()

                pixmap.save(temp_path, "PNG")
                temp_png_paths[key] = temp_path
                temp_files_to_clean.append(temp_path)

                export_graph.close()
                export_graph.deleteLater()

            # 3. Create PDF Writer
            writer = QPdfWriter(file_path)
            writer.setResolution(150)
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            writer.setPageOrientation(QPageLayout.Orientation.Portrait)
            
            page_width = writer.width()
            page_height = writer.height()
            margin = 60
            
            painter = QPainter(writer)
            painter.setRenderHint(QPainter.Antialiasing)
            
            def draw_page_decorations(painter, page_num, total_pages):
                if page_num > 1:
                    painter.setPen(QColor("#64748B"))
                    painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    painter.drawText(margin, 50, "SMART MOTOR TEST BENCH - TELEMETRY REPORT")
                    
                    painter.setPen(QPen(QColor("#CBD5E1"), 0.5))
                    painter.drawLine(margin, 60, page_width - margin, 60)
                
                painter.setPen(QPen(QColor("#CBD5E1"), 0.5))
                painter.drawLine(margin, page_height - 60, page_width - margin, page_height - 60)
                
                painter.setFont(QFont("Segoe UI", 8))
                painter.setPen(QColor("#64748B"))
                painter.drawText(margin, page_height - 40, "Generated by Smart Motor Test Bench")
                
                page_str = f"Page {page_num} of {total_pages}"
                painter.drawText(page_width - margin - 100, page_height - 40, page_str)
                
            # ── Variables needed across pages ───────────────────────────────
            now           = datetime.datetime.now()
            fw_version    = self._fw_card.fw_val.text()     if hasattr(self, "_fw_card")   else "v1.0.0"
            com_port      = self._com_card.value_lbl.text() if hasattr(self, "_com_card")  else "N/A"
            system_status = self._conn_card.text_lbl.text() if hasattr(self, "_conn_card") else "Unknown"

            # ── Shared graph/table dimensions ───────────────────────────────
            graph_width  = page_width - 2 * margin
            # Each parameter page: table ~430px + gap 20px + graph label 28px + graph
            # Leave ~100px for header/footer. Graph fills the rest.
            graph_height = int(graph_width * 0.42)   # ~470px — fits nicely below table

            # ── Pages 2–7: one page per parameter (table then graph) ─────────
            # param_pages = (key, page_num, section_icon, section_title, graph_title, line_color, unit, decimals)
            param_pages = [
                ("RPM",         2, "①", "Speed (RPM) – Performance Analysis",
                 "Speed (RPM) vs Time",     "#10B981", "rpm", 1),
                ("Voltage",     3, "②", "Voltage – Performance Analysis",
                 "Voltage vs Time",         "#3B82F6", "V",   2),
                ("Current",     4, "③", "Current – Performance Analysis",
                 "Current vs Time",         "#F59E0B", "A",   2),
                ("Power",       5, "④", "Power – Performance Analysis",
                 "Power vs Time",           "#8B5CF6", "W",   2),
                ("Temperature", 6, "⑤", "Temperature – Performance Analysis",
                 "Temperature vs Time",     "#F97316", "°C",  1),
                ("Efficiency",  7, "⑥", "Efficiency – Performance Analysis",
                 "Efficiency vs Time",      "#06B6D4", "%",   1),
            ]

            # ══════════════════════════════════════════════════════════════════
            #  Stats, design constants, and helpers for pages 2-8
            # ══════════════════════════════════════════════════════════════════

            import statistics as _stats_mod

            def _compute_stats(values, times_):
                if not values:
                    return dict(max=0.0, min=0.0, avg=0.0, range=0.0,
                                std=0.0, initial=0.0, final=0.0,
                                samples=0, duration=0.0)
                n   = len(values)
                avg = sum(values) / n
                std = _stats_mod.stdev(values) if n > 1 else 0.0
                dur = times_[-1] - times_[0] if len(times_) > 1 else 0.0
                return dict(max=max(values), min=min(values), avg=avg,
                            range=max(values) - min(values), std=std,
                            initial=values[0], final=values[-1],
                            samples=n, duration=dur)

            def _fmt_dur(seconds):
                h = int(seconds) // 3600
                m = (int(seconds) % 3600) // 60
                s = int(seconds) % 60
                if h > 0: return f"{h}h {m:02d}m {s:02d}s"
                if m > 0: return f"{m}m {s:02d}s"
                return f"{s}s"

            _hv       = history_values
            st_rpm    = _compute_stats(_hv.get("RPM",         []), times)
            st_volt   = _compute_stats(_hv.get("Voltage",     []), times)
            st_curr   = _compute_stats(_hv.get("Current",     []), times)
            st_pwr    = _compute_stats(_hv.get("Power",       []), times)
            st_temp   = _compute_stats(_hv.get("Temperature", []), times)
            st_eff    = _compute_stats(_hv.get("Efficiency",  []), times)

            total_dur   = times[-1] - times[0] if len(times) > 1 else 0.0
            total_samps = len(times)
            samp_rate   = total_samps / total_dur if total_dur > 0 else 0.0

            # Map key → stats dict for easy lookup in loop
            _stats_map = {
                "RPM": st_rpm, "Voltage": st_volt, "Current": st_curr,
                "Power": st_pwr, "Temperature": st_temp, "Efficiency": st_eff,
            }

            # Design palette
            C_HDR_BG = QColor("#1E293B")
            C_HDR_FG = QColor("#FFFFFF")
            C_ROW_A  = QColor("#F1F5F9")
            C_ROW_B  = QColor("#FFFFFF")
            C_ACCENT = QColor("#3B82F6")
            C_SEP_   = QColor("#CBD5E1")
            C_LBL_   = QColor("#334155")
            C_VAL_   = QColor("#0F172A")
            C_SEC_FG = QColor("#1E293B")

            tbl_w     = page_width - 2 * margin
            col_lbl_w = int(tbl_w * 0.60)
            row_h_    = 38
            hdr_h_    = 42

            def _new_page(page_num):
                writer.newPage()
                draw_page_decorations(painter, page_num, 7)

            def _section_header(icon, title, y):
                painter.setPen(Qt.NoPen)
                painter.setBrush(C_ACCENT)
                painter.drawRect(margin, y, 5, 30)
                painter.setPen(C_SEC_FG)
                painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                painter.drawText(margin + 16, y + 22, f"{icon}  {title}")
                return y + 44

            def _draw_table(rows, y):
                painter.setPen(Qt.NoPen)
                painter.setBrush(C_HDR_BG)
                painter.drawRect(margin, y, tbl_w, hdr_h_)
                painter.setPen(C_HDR_FG)
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(margin + 14,             y + 28, "PARAMETER")
                painter.drawText(margin + col_lbl_w + 14, y + 28, "VALUE")
                y += hdr_h_
                for i, (label, value) in enumerate(rows):
                    bg = C_ROW_A if i % 2 == 0 else C_ROW_B
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(bg)
                    painter.drawRect(margin, y, tbl_w, row_h_)
                    painter.setPen(QPen(C_SEP_, 0.5))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawLine(margin, y + row_h_, margin + tbl_w, y + row_h_)
                    painter.drawLine(margin + col_lbl_w, y, margin + col_lbl_w, y + row_h_)
                    painter.setPen(C_LBL_)
                    painter.setFont(QFont("Segoe UI", 9))
                    painter.drawText(margin + 14, y + 25, label)
                    painter.setPen(C_VAL_)
                    painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    painter.drawText(margin + col_lbl_w + 14, y + 25, value)
                    y += row_h_
                painter.setPen(QPen(C_ACCENT, 1.5))
                painter.drawLine(margin, y, margin + tbl_w, y)
                painter.setPen(QPen(C_SEP_, 1))
                painter.setBrush(Qt.NoBrush)
                return y + 22

            def _page_heading(title, y, meta=False):
                painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                painter.setPen(C_SEC_FG)
                painter.drawText(margin, y, title)
                if meta:
                    painter.setFont(QFont("Segoe UI", 9))
                    painter.setPen(QColor("#64748B"))
                    painter.drawText(margin, y + 22,
                        f"Generated: {now.strftime('%Y-%m-%d  %I:%M:%S %p')}"
                        f"   |   Total Samples: {total_samps:,}")
                    line_y = y + 34
                else:
                    line_y = y + 24
                painter.setPen(QPen(C_SEP_, 1))
                painter.drawLine(margin, line_y, page_width - margin, line_y)
                return line_y + 22

            # Health helpers
            def _h_rpm(v):
                if v >= 2950: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v >= 2800: return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return               ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))
            def _h_volt(v):
                if v < 10.0 or v > 24.0: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v < 11.0 or v > 23.0: return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return                   ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))
            def _h_curr(v):
                if v > 2.5: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v > 2.0: return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return             ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))
            def _h_pwr(v):
                if v > 10.0: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v > 9.0:  return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return              ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))
            def _h_temp(v):
                if v >= 80.0: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v >= 60.0: return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return               ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))
            def _h_eff(v):
                if v < 50.0: return ("WARNING", QColor("#EF4444"), QColor("#FEE2E2"))
                if v < 70.0: return ("CAUTION", QColor("#F59E0B"), QColor("#FEF3C7"))
                return              ("NORMAL",  QColor("#10B981"), QColor("#D1FAE5"))

            # Unit-aware row builder
            def _build_rows(key, unit, dec):
                st = _stats_map[key]
                name = {
                    "RPM": "Speed", "Voltage": "Voltage", "Current": "Current",
                    "Power": "Power", "Temperature": "Temperature", "Efficiency": "Efficiency",
                }[key]
                fmt = f".{dec}f"
                u = f" {unit}" if unit else ""
                return [
                    (f"Maximum {name}",    f"{st['max']:{fmt}}{u}"),
                    (f"Minimum {name}",    f"{st['min']:{fmt}}{u}"),
                    (f"Average {name}",    f"{st['avg']:{fmt}}{u}"),
                    (f"{name} Range",      f"{st['range']:{fmt}}{u}"),
                    ("Standard Deviation", f"{st['std']:.{max(dec,2)}f}{u}"),
                    (f"Initial {name}",    f"{st['initial']:{fmt}}{u}"),
                    (f"Final {name}",      f"{st['final']:{fmt}}{u}"),
                    ("Total Samples",      f"{st['samples']:,}"),
                    ("Test Duration",      _fmt_dur(st['duration'])),
                ]

            # -- PAGE 1: Summary + Health (drawn on the auto-created first page) --

            draw_page_decorations(painter, 1, 7)
            y = 90
            y = _page_heading("Test Summary & Health Assessment", y)

            y = _section_header("①", "Overall Test Information", y)
            y = _draw_table([
                ("Export Date",               now.strftime("%Y-%m-%d")),
                ("Export Time",               now.strftime("%I:%M:%S %p")),
                ("Total Test Duration",        _fmt_dur(total_dur)),
                ("Total Samples Recorded",     f"{total_samps:,}"),
                ("Average Sampling Rate",      f"{samp_rate:.2f} Hz"),
                ("Firmware Version",           fw_version),
                ("COM Port",                   com_port),
                ("System Status",              system_status),
                ("Software Version",           "v1.1.2"),
                ("Report Version",             "2.0"),
                ("Test Status",                "COMPLETED" if total_samps > 0 else "NO DATA"),
            ], y)
            y += 28

            y = _section_header("②", "Performance Health Indicators", y)

            health_entries = [
                ("Speed (RPM)",
                 f"Avg {st_rpm['avg']:.1f} RPM   |   Max {st_rpm['max']:.1f} RPM",
                 _h_rpm(st_rpm['max'])),
                ("Voltage",
                 f"Avg {st_volt['avg']:.2f} V   |   Range {st_volt['range']:.2f} V",
                 _h_volt(st_volt['avg'])),
                ("Current",
                 f"Avg {st_curr['avg']:.2f} A   |   Max {st_curr['max']:.2f} A",
                 _h_curr(st_curr['max'])),
                ("Power",
                 f"Avg {st_pwr['avg']:.2f} W   |   Max {st_pwr['max']:.2f} W",
                 _h_pwr(st_pwr['max'])),
                ("Temperature",
                 f"Avg {st_temp['avg']:.1f} °C   |   Max {st_temp['max']:.1f} °C",
                 _h_temp(st_temp['max'])),
                ("Efficiency",
                 f"Avg {st_eff['avg']:.1f} %   |   Min {st_eff['min']:.1f} %",
                 _h_eff(st_eff['min'])),
            ]

            hi_row_h = 52
            badge_w  = 110

            painter.setPen(Qt.NoPen)
            painter.setBrush(C_HDR_BG)
            painter.drawRect(margin, y, tbl_w, hdr_h_)
            painter.setPen(C_HDR_FG)
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(margin + 14,                    y + 28, "PARAMETER")
            painter.drawText(margin + 240,                   y + 28, "MEASURED VALUES")
            painter.drawText(margin + tbl_w - badge_w - 14, y + 28, "STATUS")
            y += hdr_h_

            for idx, (param, detail, (status_str, fg_c, bg_c)) in enumerate(health_entries):
                row_bg = C_ROW_A if idx % 2 == 0 else C_ROW_B
                painter.setPen(Qt.NoPen)
                painter.setBrush(row_bg)
                painter.drawRect(margin, y, tbl_w, hi_row_h)
                painter.setPen(QPen(C_SEP_, 0.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(margin, y + hi_row_h, margin + tbl_w, y + hi_row_h)
                painter.setPen(C_LBL_)
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(margin + 14, y + 20, param)
                painter.setPen(QColor("#475569"))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(margin + 14, y + 38, detail)
                bx = margin + tbl_w - badge_w - 18
                by = y + (hi_row_h - 28) // 2
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_c)
                painter.drawRoundedRect(bx, by, badge_w, 28, 6, 6)
                painter.setPen(fg_c)
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                fm = painter.fontMetrics()
                tx = bx + (badge_w - fm.horizontalAdvance(status_str)) // 2
                painter.drawText(tx, by + 19, status_str)
                y += hi_row_h

            painter.setPen(QPen(C_ACCENT, 1.5))
            painter.drawLine(margin, y, margin + tbl_w, y)

            # ── PAGES 2-7: Analysis table + graph per parameter ───────────────
            for (key, pg_num, icon, sec_title, g_title, _, unit, dec) in param_pages:
                _new_page(pg_num)
                y = 90
                y = _page_heading("Performance Analysis Report", y)
                y = _section_header(icon, sec_title, y)
                y = _draw_table(_build_rows(key, unit, dec), y)
                y += 18
                painter.setPen(QColor("#0F172A"))
                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                painter.drawText(margin, y, g_title)
                y += 22
                available_h = page_height - y - 90
                g_h = min(graph_height, available_h)
                if g_h > 100 and key in temp_png_paths:
                    pix = QPixmap(temp_png_paths[key])
                    scaled = pix.scaled(graph_width, g_h,
                                        Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    painter.drawPixmap(margin, y, scaled)

            painter.end()
            self._show_toast("✅ PDF exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to generate PDF report: {e}")
        finally:
            # Clean up temporary PNG files
            for p in temp_files_to_clean:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    def _export_data_csv(self) -> None:
        if not hasattr(self, "_dashboard") or not self._dashboard:
            return
            
        if not self._dashboard._history_times:
            QMessageBox.warning(self, "No Telemetry Data", "There is no recorded telemetry data in the active session buffer to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Telemetry Data to CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Time (s)", "Speed (RPM)", "Voltage (V)", "Current (A)", "Power (W)", "Efficiency (%)", "Temperature (°C)"])
                for i in range(len(self._dashboard._history_times)):
                    t = self._dashboard._history_times[i]
                    rpm = self._dashboard._history_values["RPM"][i]
                    volt = self._dashboard._history_values["Voltage"][i]
                    curr = self._dashboard._history_values["Current"][i]
                    pwr = self._dashboard._history_values["Power"][i]
                    eff = self._dashboard._history_values["Efficiency"][i]
                    temp = self._dashboard._history_values["Temperature"][i]
                    writer.writerow([t, rpm, volt, curr, pwr, eff, temp])
            self._show_toast("✅ CSV exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export data: {e}")

    def _export_dashboard_png(self) -> None:
        if not hasattr(self, "_dashboard") or not self._dashboard:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Dashboard Screenshot", "", "PNG Files (*.png)"
        )
        if not file_path:
            return
            
        try:
            pixmap = self._dashboard.grab()
            pixmap.save(file_path, "PNG")
            self._show_toast("✅ Dashboard saved as PNG")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to save screenshot: {e}")

    def _capture_screenshot(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Capture App Screenshot", "", "PNG Files (*.png)"
        )
        if not file_path:
            return
            
        try:
            pixmap = self.grab()
            pixmap.save(file_path, "PNG")
            self._show_toast("✅ Dashboard saved as PNG")
        except Exception as e:
            QMessageBox.critical(self, "Capture Failed", f"Failed to capture screenshot: {e}")

    def _export_settings_info(self) -> None:
        QMessageBox.information(
            self,
            "Export Settings",
            "Export Settings configuration will be available in a future update."
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Handle application close event to clean up resources."""
        print("[MainWindow] Closing application...")
        if self._serial:
            try:
                self._serial.disconnect()
            except Exception as e:
                print(f"[MainWindow] Error disconnecting serial on exit: {e}")
        event.accept()


def _cleanup_other_instances() -> None:
    """Find and terminate other python processes running main.py to prevent COM port conflicts."""
    import subprocess
    import os
    try:
        current_pid = os.getpid()
        if os.name == 'nt':
            # Use PowerShell to find other python processes running main.py and terminate them
            # This is fast and works natively on Windows without external dependencies
            script = (
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Where-Object { $_.CommandLine -like '*main.py*' -and $_.ProcessId -ne " + str(current_pid) + " } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    except Exception as e:
        print(f"[Startup] Error cleaning up other main.py instances: {e}")


# ──────────────────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Create and run the PySide6 application."""
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    
    # Single instance lock removed to prevent startup issues
    pass

    app.setApplicationName("Smart Motor Test Bench")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("EE Student Lab")

    # App-wide font: Segoe UI on Windows, fallback to Inter or sans-serif
    app.setFont(QFont("Segoe UI", 11))

    # Load persisted user settings
    settings = _load_settings()

    # Instantiate backend objects (SerialManager is created inside MainWindow after splash finishes)
    data_gen = DataGenerator()

    # Keep a reference to windows to prevent garbage collection
    main_window_ref = []

    # Create and show the MainWindow maximized
    window = MainWindow(data_gen, settings)
    window.showMaximized()

    main_window_ref.extend([window])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
