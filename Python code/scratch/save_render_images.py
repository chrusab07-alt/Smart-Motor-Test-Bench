import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
from widgets.graph_widget import RealtimeGraph

def save_images():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    times = [i * 0.1 for i in range(100)]
    vals = [1000 + i * 5 for i in range(100)]
    
    target_dir = r"C:\Users\Coder\.gemini\antigravity-ide\brain\61a801ad-db27-4428-ba2f-42d19607be95\scratch"
    os.makedirs(target_dir, exist_ok=True)

    # 1. Grab no show
    export_graph1 = RealtimeGraph("Offscreen Test 1", "RPM", "rpm", "#10B981")
    export_graph1.setFixedSize(1400, 700)
    export_graph1.set_data(times, vals)
    export_graph1.ensurePolished()
    export_graph1.adjustSize()
    pixmap1 = export_graph1._plot_widget.grab()
    p1 = os.path.join(target_dir, "test_grab_no_show.png")
    pixmap1.save(p1, "PNG")
    print(f"p1 saved: {p1}, size={os.path.getsize(p1)}")
    export_graph1.close()

    # 2. WA_DontShowOnScreen
    export_graph2 = RealtimeGraph("Offscreen Test 2", "RPM", "rpm", "#10B981")
    export_graph2.setFixedSize(1400, 700)
    export_graph2.set_data(times, vals)
    export_graph2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    export_graph2.show()
    export_graph2.ensurePolished()
    QApplication.processEvents()
    pixmap2 = export_graph2._plot_widget.grab()
    p2 = os.path.join(target_dir, "test_dont_show_on_screen.png")
    pixmap2.save(p2, "PNG")
    print(f"p2 saved: {p2}, size={os.path.getsize(p2)}")
    export_graph2.close()

    # 3. Render pixmap
    export_graph3 = RealtimeGraph("Offscreen Test 3", "RPM", "rpm", "#10B981")
    export_graph3.setFixedSize(1400, 700)
    export_graph3.set_data(times, vals)
    export_graph3.ensurePolished()
    export_graph3.adjustSize()
    pixmap3 = QPixmap(1400, 700)
    pixmap3.fill(Qt.transparent)
    painter = QPainter(pixmap3)
    export_graph3._plot_widget.render(painter)
    painter.end()
    p3 = os.path.join(target_dir, "test_render_pixmap.png")
    pixmap3.save(p3, "PNG")
    print(f"p3 saved: {p3}, size={os.path.getsize(p3)}")
    export_graph3.close()

if __name__ == "__main__":
    save_images()
