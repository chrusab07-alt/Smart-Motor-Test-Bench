import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
from widgets.graph_widget import RealtimeGraph

def test_offscreen():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    times = [i * 0.1 for i in range(100)]
    vals = [1000 + i * 5 for i in range(100)]

    export_graph = RealtimeGraph("Offscreen Test", "RPM", "rpm", "#10B981")
    export_graph.setFixedSize(1400, 700)
    export_graph.set_data(times, vals)

    # Let's try grabbing without show()
    export_graph.ensurePolished()
    # We must trigger layouts and updates
    export_graph.adjustSize()
    
    # Render method 1: grab directly without show
    pixmap1 = export_graph._plot_widget.grab()
    
    # Save to temp
    p1 = os.path.join(tempfile.gettempdir(), "test_grab_no_show.png")
    pixmap1.save(p1, "PNG")
    print(f"Grab no show: exists={os.path.exists(p1)}, size={os.path.getsize(p1) if os.path.exists(p1) else 0}")
    if os.path.exists(p1): os.remove(p1)

    # Render method 2: use WA_DontShowOnScreen
    export_graph2 = RealtimeGraph("Offscreen Test 2", "RPM", "rpm", "#10B981")
    export_graph2.setFixedSize(1400, 700)
    export_graph2.set_data(times, vals)
    export_graph2.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    export_graph2.show()
    export_graph2.ensurePolished()
    
    # Process events to let Qt paint/layout
    QApplication.processEvents()
    
    pixmap2 = export_graph2._plot_widget.grab()
    p2 = os.path.join(tempfile.gettempdir(), "test_dont_show_on_screen.png")
    pixmap2.save(p2, "PNG")
    print(f"WA_DontShowOnScreen: exists={os.path.exists(p2)}, size={os.path.getsize(p2) if os.path.exists(p2) else 0}")
    if os.path.exists(p2): os.remove(p2)
    export_graph2.close()
    
    # Render method 3: render onto pixmap directly
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
    
    p3 = os.path.join(tempfile.gettempdir(), "test_render_pixmap.png")
    pixmap3.save(p3, "PNG")
    print(f"Render pixmap: exists={os.path.exists(p3)}, size={os.path.getsize(p3) if os.path.exists(p3) else 0}")
    if os.path.exists(p3): os.remove(p3)

if __name__ == "__main__":
    test_offscreen()
