"""
custom_dialog.py
----------------
A premium dark-themed custom modal dialog with subtle scale and fade-in entry animations.
Designed for alerts such as 'Feature Under Development'.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGraphicsOpacityEffect, QFrame
)

class ModernDialog(QDialog):
    """
    A custom dialog with a premium dark theme, rounded corners, and entry animation.
    """
    def __init__(
        self,
        title: str,
        message: str,
        icon_char: str = "⚙",
        icon_color: str = "#3B82F6",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.title_text = title
        self.message_text = message
        self.icon_char = icon_char
        self.icon_color = icon_color
        
        self._build_ui()
        self._setup_animation()

    def _build_ui(self) -> None:
        # Outer layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        
        # Dialog body container
        self.body = QFrame()
        self.body.setObjectName("DialogBody")
        self.body.setFixedSize(360, 240)
        self.body.setStyleSheet(f"""
            QFrame#DialogBody {{
                background-color: #111827;
                border: 1px solid #2D3748;
                border-radius: 16px;
            }}
        """)
        
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(24, 24, 24, 20)
        body_layout.setSpacing(14)
        
        # Header block (Icon + Title)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        
        icon_lbl = QLabel(self.icon_char)
        icon_lbl.setFont(QFont("Segoe UI", 24))
        icon_lbl.setStyleSheet(f"color: {self.icon_color};")
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        title_lbl = QLabel(self.title_text)
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_lbl.setStyleSheet("color: #F1F5F9;")
        title_lbl.setWordWrap(True)
        
        header_row.addWidget(icon_lbl)
        header_row.addWidget(title_lbl, stretch=1)
        body_layout.addLayout(header_row)
        
        # Separator line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1E293B; border: none; max-height: 1px;")
        body_layout.addWidget(divider)
        
        # Message description
        msg_lbl = QLabel(self.message_text)
        msg_lbl.setFont(QFont("Segoe UI", 11))
        msg_lbl.setStyleSheet("color: #94A3B8; line-height: 1.4;")
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        body_layout.addWidget(msg_lbl, stretch=1)
        
        # Buttons area
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(90)
        ok_btn.setFixedHeight(34)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1D4ED8;
                color: #FFFFFF;
                border: 1px solid #3B82F6;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2563EB;
                border-color: #60A5FA;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(ok_btn)
        body_layout.addLayout(btn_layout)
        
        root_layout.addWidget(self.body, alignment=Qt.AlignCenter)

    def _setup_animation(self) -> None:
        # Opacity Fade-in
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(180)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def showEvent(self, event) -> None:
        self.anim.start()
        super().showEvent(event)

    @classmethod
    def show_feature_under_development(cls, parent: QWidget | None = None) -> None:
        """Helper to show the default 'Feature Under Development' dialog."""
        dlg = cls(
            title="Feature Under Development",
            message="This module is currently under development and will be available in a future update.",
            icon_char="⚙",
            icon_color="#EAB308", # Yellow amber
            parent=parent
        )
        dlg.exec()
