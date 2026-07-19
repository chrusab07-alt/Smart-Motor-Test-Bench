"""
about.py
--------
Dedicated About page for the Smart Motor Test Bench.
Presents project credentials, university context, description, and technologies.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QScrollArea, QSizePolicy
)

class AboutPage(QWidget):
    """
    Dedicated About Page.
    Lists the application metadata, developers, and university info in a clean layout.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title_lbl = QLabel("ABOUT SYSTEM")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        root_layout.addWidget(title_lbl)

        # ── Main Content Scroll ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Main Branding Card
        layout.addWidget(self._build_branding_card())

        # 2. Details Grid (Developer, University, License)
        layout.addWidget(self._build_details_card())

        # 3. Technologies Used Grid
        layout.addWidget(self._build_techs_card())

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

    def _build_branding_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Large icon
        icon_lbl = QLabel("⚙")
        icon_lbl.setFont(QFont("Segoe UI Symbol", 64))
        icon_lbl.setStyleSheet("color: #3B82F6; border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Branding text
        txt_layout = QVBoxLayout()
        txt_layout.setSpacing(4)
        
        lbl_app = QLabel("Smart Motor Test Bench")
        lbl_app.setFont(QFont("Segoe UI", 20, QFont.Bold))
        lbl_app.setStyleSheet("color: #F1F5F9; border: none; font-weight: 800; background: transparent;")
        
        lbl_sub = QLabel("Real-Time Motor Performance Monitoring System")
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setStyleSheet("color: #94A3B8; border: none; background: transparent;")

        lbl_desc = QLabel(
            "This software serves as a real-time command-and-control dashboard for mechanical motor test rigs. "
            "Engineered to log current, speed, voltage, power, efficiency, and temperature telemetry, "
            "providing visual transient recordings and safety limit monitoring."
        )
        lbl_desc.setFont(QFont("Segoe UI", 10))
        lbl_desc.setStyleSheet("color: #64748B; border: none; line-height: 1.5; background: transparent;")
        lbl_desc.setWordWrap(True)

        txt_layout.addWidget(lbl_app)
        txt_layout.addWidget(lbl_sub)
        txt_layout.addSpacing(6)
        txt_layout.addWidget(lbl_desc)

        layout.addLayout(txt_layout, stretch=1)
        return card

    def _build_details_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("System Details & Credentials")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #3B82F6; border: none; background: transparent;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        details = [
            ("Application Title", "Smart Motor Test Bench"),
            ("Application Version", "Version 1.0"),
            ("System Description", "Real-Time Motor Performance Monitoring System"),
            ("Developed By", "Engineer SB"),
            ("Department", "Electrical Engineering"),
            ("Host University", "UET Lahore"),
        ]

        for idx, (key, val) in enumerate(details):
            lbl_key = QLabel(key)
            lbl_key.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl_key.setStyleSheet("color: #64748B; border: none; background: transparent;")
            
            lbl_val = QLabel(val)
            lbl_val.setFont(QFont("Segoe UI", 10))
            lbl_val.setStyleSheet("color: #E2E8F0; border: none; background: transparent;")
                
            grid.addWidget(lbl_key, idx, 0)
            grid.addWidget(lbl_val, idx, 1)

        layout.addLayout(grid)
        return card

    def _build_techs_card(self) -> QFrame:
        card = self._make_card_base()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Built Using")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #3B82F6; border: none; background: transparent;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        techs = [
            ("🔌  Arduino UNO", "Microcontroller hardware interface for sensor signal acquisition."),
            ("🐍  Python", "Programming Language, async tasking & data parsing backend."),
            ("🖼  PyQt6", "Cross-platform Qt6 binding for Python for UI widget renders."),
            ("📈  Matplotlib", "Fast plotting utility for data visualization and graphing."),
            ("📥  Serial Communication", "Standard USB Serial communication protocol with Arduino UNO."),
        ]

        for idx, (tech, desc) in enumerate(techs):
            lbl_tech = QLabel(tech)
            lbl_tech.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl_tech.setStyleSheet("color: #FFFFFF; background-color: #1E293B; border-radius: 6px; padding: 4px 8px; border: 1px solid rgba(255,255,255,0.06);")
            
            lbl_desc = QLabel(desc)
            lbl_desc.setFont(QFont("Segoe UI", 10))
            lbl_desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
            
            grid.addWidget(lbl_tech, idx, 0)
            grid.addWidget(lbl_desc, idx, 1)

        layout.addLayout(grid)
        return card

    @staticmethod
    def _make_card_base() -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
            }
        """)
        return card
