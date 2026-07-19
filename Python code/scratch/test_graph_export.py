import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from widgets.graph_widget import RealtimeGraph
import tempfile

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

graph = RealtimeGraph("Speed (RPM) vs Time", "RPM", "rpm", "#10B981")
times = [i * 0.1 for i in range(50)]
values = [1200.0 + i * 5 for i in range(50)]

# Manually test the marker update logic
graph.set_data(times, values)
if graph._values:
    graph._point_marker.setData([graph._times[-1]], [graph._values[-1]])
    graph._latest_value_lbl.setHtml(
        f"<div style='padding: 1px 3px; color: #FFFFFF; font-family: Segoe UI, sans-serif; font-size: 8pt; font-weight: bold;'>{graph._values[-1]:.1f}</div>"
    )
    graph._latest_value_lbl.setPos(graph._times[-1], graph._values[-1])
    graph._latest_value_lbl.setVisible(True)

print("Latest value label visible now?", graph._latest_value_lbl.isVisible())

graph.setFixedSize(1200, 600)
graph.show()
graph.repaint()
graph._plot_widget.repaint()
app.processEvents()

pix = graph._plot_widget.grab()
temp_dir = tempfile.gettempdir()
out_path = os.path.join(temp_dir, "test_plot_canvas_marker.png")
pix.save(out_path, "PNG")
print("Saved canvas grab to:", out_path, "Size:", os.path.getsize(out_path))

app.quit()
