"""
toast.py
--------
A modern, auto-dismissing toast notification overlay.
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect

class ToastNotification(QWidget):
    """A floating toast notification widget."""
    def __init__(self, parent: QWidget, message: str, duration: int = 3000):
        super().__init__(parent)
        self.message = message
        self.duration = duration

        # It's an overlay widget, not a separate window, so we don't use Window flags
        # if we want it to stay inside the parent window properly without stealing focus
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.label = QLabel(self.message)
        self.label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)

        # Setup fade effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(300)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self.close)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.duration)
        self.timer.timeout.connect(self.hide_toast)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(15, 23, 42, 230))
        painter.setPen(QColor(59, 130, 246)) # Accent blue border
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
        super().paintEvent(event)

    def show_toast(self):
        self.adjustSize()
        # Position at bottom-right of parent
        parent_rect = self.parentWidget().rect()
        x = parent_rect.width() - self.width() - 24
        y = parent_rect.height() - self.height() - 24
        self.move(x, y)
        self.raise_()
        self.show()
        self.anim_in.start()
        self.timer.start()

    def hide_toast(self):
        self.anim_out.start()
