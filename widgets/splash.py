"""
splash.py
---------
Professional splash screen with a vector logo and simulated loading animation.
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, version: str):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 300)

        self._version = version
        self._progress = 0

        self._build_ui()

        # Simulated loading
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(30) # 100 steps * 30ms = 3000ms (3 seconds)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Smart Motor Test Bench")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        title.setAlignment(Qt.AlignCenter)

        # Subtitle
        version_lbl = QLabel(f"Version {self._version}")
        version_lbl.setFont(QFont("Segoe UI", 12))
        version_lbl.setStyleSheet("color: #94A3B8;")
        version_lbl.setAlignment(Qt.AlignCenter)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 3px;
            }
        """)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(version_lbl)
        layout.addSpacing(40)
        layout.addWidget(self._bar)

    def _update_progress(self):
        self._progress += 1
        self._bar.setValue(self._progress)
        if self._progress >= 100:
            self._timer.stop()
            self.finished.emit()
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.setBrush(QColor(15, 23, 42, 240))
        painter.setPen(QColor(59, 130, 246)) # Blue border
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 16, 16)

        # Draw a subtle vector logo (a motor/cog shape) in the background
        painter.setPen(QPen(QColor(59, 130, 246, 50), 4))
        painter.setBrush(Qt.NoBrush)
        center = self.rect().center()
        
        # A simple stylized motor or concentric circles
        painter.drawEllipse(center, 80, 80)
        painter.drawEllipse(center, 100, 100)
        painter.drawLine(center.x() - 110, center.y(), center.x() + 110, center.y())
        painter.drawLine(center.x(), center.y() - 110, center.x(), center.y() + 110)

        super().paintEvent(event)
