import sys
import base64
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt

app = QApplication(sys.argv)
w = QWidget()
w.setStyleSheet("background-color: #0B1120;")
layout = QVBoxLayout(w)

svg_str = """<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30">
  <path d="M-10 10L10 -10M0 30L30 0M20 40L40 20" stroke="rgba(255,255,255,0.15)" stroke-width="8"/>
</svg>"""
encoded = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
svg_url = f"data:image/svg+xml;base64,{encoded}"

pb = QProgressBar()
pb.setFixedHeight(24)
pb.setValue(75)
pb.setTextVisible(False)
pb.setStyleSheet(f"""
    QProgressBar {{
        background-color: #0F172A;
        border: 1.5px solid #1E293B;
        border-radius: 12px;
    }}
    QProgressBar::chunk {{
        background-color: #2563EB;
        background-image: url("{svg_url}");
        border-radius: 11px;
    }}
""")

layout.addWidget(pb)
w.resize(600, 100)
w.show()
QTimer.singleShot(2000, app.quit)
app.exec()
