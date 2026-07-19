"""
graph_widget.py
---------------
Real-time PyQtGraph plot widget with premium dark theme, crosshair mouse tracking,
grid lines, legend, and customized font rendering.
"""

from __future__ import annotations

from collections import deque
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QBrush, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect

class RealtimeGraph(QWidget):
    """
    A single real-time scrolling line graph backed by PyQtGraph, supporting mouse hover
    crosshairs, coordinate hud display, auto-scale, grid, and legend.
    """

    MAX_POINTS: int = 600   # ~60 s at 10 Hz

    def __init__(
        self,
        title: str,
        y_label: str,
        y_unit: str,
        line_color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title
        self._y_label = y_label
        self._y_unit = y_unit
        self._line_color = line_color

        self._times: deque[float] = deque(maxlen=self.MAX_POINTS)
        self._values: deque[float] = deque(maxlen=self.MAX_POINTS)
        self._elapsed: float = 0.0
        self._waiting_for_data: bool = True

        self.DEFAULT_RANGES = {
            "RPM": (0.0, 3000.0),
            "Voltage": (0.0, 25.0),
            "Current": (0.0, 5.0),
            "Power": (0.0, 50.0),
            "Temperature": (0.0, 100.0),
            "Efficiency": (0.0, 100.0),
        }
        self._auto_scale = False
        self._current_ymin = 0.0
        self._current_ymax = 3000.0

        self._range_timer = QTimer(self)
        self._range_timer.setInterval(20)
        self._range_timer.timeout.connect(self._step_range_animation)
        self._range_timer.start()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_ui()
        self._setup_crosshair()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # PyQtGraph global options
        pg.setConfigOptions(antialias=True, foreground="#E2E8F0", background="#111827")

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#111827")

        # Title
        self._plot_widget.setTitle(
            f"<span style='color:#E2E8F0; font-family: Segoe UI, Inter; font-size:11pt; font-weight:700;'>{self._title}</span>",
            size="11pt",
        )

        # Axes labels (increased size by 2px, higher contrast)
        self._plot_widget.setLabel(
            "left",
            f"<span style='color:#F1F5F9; font-family: Segoe UI; font-size:12pt; font-weight:600;'>{self._y_label} ({self._y_unit})</span>",
        )
        self._plot_widget.setLabel(
            "bottom",
            "<span style='color:#F1F5F9; font-family: Segoe UI; font-size:12pt; font-weight:600;'>Time (s)</span>",
        )

        # Tick and grid styling (clean dashed grid lines with increased visibility)
        for axis in ("left", "bottom"):
            ax = self._plot_widget.getAxis(axis)
            ax.setTextPen(pg.mkPen(color="#CBD5E1"))
            ax.setPen(pg.mkPen(color="#475569"))
            ax.setTickPen(pg.mkPen(color="#475569", width=1, style=Qt.DashLine))
            ax.setTickFont(QFont("Segoe UI", 11))

        # Grid lines (clean, subtle dashed grid with increased visibility and no clutter)
        self._plot_widget.showGrid(x=True, y=True, alpha=0.35)

        # Legend (increased size to 11pt and brighter text)
        self._legend = self._plot_widget.addLegend(
            offset=(12, 12),
            labelTextSize="11pt",
            labelTextColor="#CBD5E1",
        )
        self._legend.setParentItem(self._plot_widget.getPlotItem())

        # Enable mouse interactions (both panning and zooming)
        self._plot_widget.enableAutoRange(axis="y", enable=True)
        self._plot_widget.setMouseEnabled(x=True, y=True)

        # The data curve
        pen = pg.mkPen(color=self._line_color, width=2.5)
        self._curve = self._plot_widget.plot(
            pen=pen,
            name=self._y_label,
            antialias=True,
        )
        # Gradient fill under curve: from line color to transparent
        try:
            grad = QLinearGradient(0, 0, 0, 1)
            grad.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
            c = QColor(self._line_color)
            c.setAlpha(200)
            grad.setColorAt(0.0, c)
            c2 = QColor(self._line_color)
            c2.setAlpha(20)
            grad.setColorAt(1.0, c2)
            brush = QBrush(grad)
            self._curve.setBrush(brush)
        except Exception:
            self._curve.setBrush(pg.mkBrush((16, 24, 39, 40)))
        self._curve.setFillLevel(0)

        self._point_marker = pg.ScatterPlotItem(
            size=8,
            brush=pg.mkBrush(color=self._line_color),
            pen=pg.mkPen(color="#F8FAFC", width=1),
        )
        self._plot_widget.addItem(self._point_marker)

        self._placeholder = pg.TextItem(
            html=(
                "<div style='text-align: center; padding: 12px 18px;'>"
                "<div style='font-size: 20pt; margin-bottom: 6px;'>🔌</div>"
                "<div style='color: #F8FAFC; font-family: Segoe UI, sans-serif; font-size: 11pt; font-weight: bold; margin-bottom: 3px;'>No Live Data</div>"
                "<div style='color: #94A3B8; font-family: Segoe UI, sans-serif; font-size: 9pt;'>Connect Arduino to Start Monitoring</div>"
                "</div>"
            ),
            anchor=(0.5, 0.5),
            fill=pg.mkBrush(17, 24, 39, 230),
            border=pg.mkPen("#334155", width=1),
        )
        self._latest_value_lbl = pg.TextItem(
            "",
            anchor=(0, 0.5),
            fill=pg.mkBrush(self._line_color),
            border=pg.mkPen(self._line_color, width=1),
        )
        self._latest_value_lbl.setVisible(False)
        self._plot_widget.addItem(self._latest_value_lbl, ignoreBounds=True)
        self._plot_widget.addItem(self._placeholder, ignoreBounds=True)
        self._placeholder.setVisible(False)

        layout.addWidget(self._plot_widget)

        # Stylesheet for custom container border
        self.setStyleSheet("""
            RealtimeGraph {
                background-color: transparent;
                border: none;
            }
        """)

    def _setup_crosshair(self) -> None:
        """Create the tracking crosshairs and HUD label."""
        # Crosshair lines
        self._v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color="#475569", width=1, style=Qt.DashLine))
        self._h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color="#475569", width=1, style=Qt.DashLine))
        
        self._plot_widget.addItem(self._v_line, ignoreBounds=True)
        self._plot_widget.addItem(self._h_line, ignoreBounds=True)
        
        self._v_line.hide()
        self._h_line.hide()

        # HUD coordinate label (tracks coordinates)
        self._hud = pg.TextItem(anchor=(0, 1), fill=pg.mkBrush(17, 24, 39, 220), border=pg.mkPen("#3B82F6", width=1))
        self._plot_widget.addItem(self._hud, ignoreBounds=True)
        self._hud.hide()

        # Connect mouse moved signal
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _on_mouse_moved(self, pos) -> None:
        """Handle mouse movement to update crosshair tracking and HUD text."""
        plot_item = self._plot_widget.plotItem
        view_box = plot_item.vb

        if plot_item.sceneBoundingRect().contains(pos):
            mouse_point = view_box.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()

            # Align lines to cursor
            self._v_line.setPos(x)
            self._h_line.setPos(y)

            # Update HUD HTML display
            hud_html = (
                f"<div style='padding: 6px; color: #E2E8F0; font-family: Segoe UI, sans-serif; font-size: 8pt;'>"
                f"<b style='color: #60A5FA;'>Time:</b> {x:.2f} s<br/>"
                f"<b style='color: {self._line_color};'>{self._y_label}:</b> {y:.2f} {self._y_unit}"
                f"</div>"
            )
            self._hud.setHtml(hud_html)

            # Calculate suitable offsets so HUD text is placed slightly to the right/above cursor
            self._hud.setPos(x, y)

            self._v_line.show()
            self._h_line.show()
            self._hud.show()
        else:
            self._v_line.hide()
            self._h_line.hide()
            self._hud.hide()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def _get_param_key(self, label: str) -> str:
        if label == "Speed":
            return "RPM"
        return label # Voltage, Current, Power, Temperature, Efficiency

    def _snap_to_target_range(self) -> None:
        key = self._get_param_key(self._y_label)
        if self._auto_scale and self._values:
            v_min = min(self._values)
            v_max = max(self._values)
            diff = v_max - v_min
            if diff == 0.0:
                diff = 1.0
            margin = 0.125 * diff
            self._current_ymin = v_min - margin
            self._current_ymax = v_max + margin
        else:
            default_range = self.DEFAULT_RANGES.get(key, (0.0, 100.0))
            default_min, default_max = default_range
            if self._values:
                v_min = min(self._values)
                v_max = max(self._values)
                target_ymin = min(default_min, v_min)
                target_ymax = max(default_max, v_max)
                if v_min < default_min:
                    target_ymin -= 0.05 * (default_min - v_min)
                if v_max > default_max:
                    target_ymax += 0.05 * (v_max - default_max)
                self._current_ymin, self._current_ymax = target_ymin, target_ymax
            else:
                self._current_ymin, self._current_ymax = default_range

        if self._times:
            self._current_xmax = self._elapsed
            self._current_xmin = max(0.0, self._current_xmax - 60.0)
            self._plot_widget.setXRange(self._current_xmin, self._current_xmax, padding=0)

        self._plot_widget.setYRange(self._current_ymin, self._current_ymax, padding=0)

    def _step_range_animation(self) -> None:
        if self._waiting_for_data:
            return

        # 1. Smooth X-axis scrolling animation
        if self._times:
            target_xmax = self._elapsed
            target_xmin = max(0.0, target_xmax - 60.0)

            if not hasattr(self, '_current_xmin') or self._current_xmin is None:
                self._current_xmin = target_xmin
                self._current_xmax = target_xmax
            else:
                x_factor = 0.20
                if abs(self._current_xmax - target_xmax) > 0.001:
                    self._current_xmin += (target_xmin - self._current_xmin) * x_factor
                    self._current_xmax += (target_xmax - self._current_xmax) * x_factor
                    self._plot_widget.setXRange(self._current_xmin, self._current_xmax, padding=0)

        # 2. Smooth Y-axis range scaling animation
        key = self._get_param_key(self._y_label)
        if self._auto_scale:
            if self._values:
                v_min = min(self._values)
                v_max = max(self._values)
                diff = v_max - v_min
                if diff == 0.0:
                    if v_min == 0.0:
                        diff = 10.0
                    else:
                        diff = abs(v_min) * 0.2
                margin = 0.125 * diff
                target_ymin = v_min - margin
                target_ymax = v_max + margin
            else:
                default_range = self.DEFAULT_RANGES.get(key, (0.0, 100.0))
                target_ymin, target_ymax = default_range
        else:
            default_range = self.DEFAULT_RANGES.get(key, (0.0, 100.0))
            default_min, default_max = default_range
            if self._values:
                v_min = min(self._values)
                v_max = max(self._values)
                target_ymin = min(default_min, v_min)
                target_ymax = max(default_max, v_max)
                if v_min < default_min:
                    target_ymin -= 0.05 * (default_min - v_min)
                if v_max > default_max:
                    target_ymax += 0.05 * (v_max - default_max)
            else:
                target_ymin, target_ymax = default_min, default_max

        factor = 0.15
        if abs(self._current_ymin - target_ymin) < 0.01 and abs(self._current_ymax - target_ymax) < 0.01:
            self._current_ymin = target_ymin
            self._current_ymax = target_ymax
        else:
            self._current_ymin += (target_ymin - self._current_ymin) * factor
            self._current_ymax += (target_ymax - self._current_ymax) * factor

        self._plot_widget.setYRange(self._current_ymin, self._current_ymax, padding=0)

    def set_auto_scale(self, enable: bool) -> None:
        """Enable or disable auto-scaling of the Y-axis."""
        self._auto_scale = enable
        if enable:
            self._snap_to_target_range()

    def reset_zoom(self) -> None:
        """Reset the zoom and return graph ranges to default fixed bounds."""
        self._auto_scale = False
        key = self._get_param_key(self._y_label)
        default_range = self.DEFAULT_RANGES.get(key, (0.0, 100.0))
        default_min, default_max = default_range
        if self._values:
            v_min = min(self._values)
            v_max = max(self._values)
            target_ymin = min(default_min, v_min)
            target_ymax = max(default_max, v_max)
            if v_min < default_min:
                target_ymin -= 0.05 * (default_min - v_min)
            if v_max > default_max:
                target_ymax += 0.05 * (v_max - default_max)
            self._current_ymin, self._current_ymax = target_ymin, target_ymax
        else:
            self._current_ymin, self._current_ymax = default_range
        self._plot_widget.setYRange(self._current_ymin, self._current_ymax, padding=0)
        self._plot_widget.enableAutoRange(axis='x', enable=True)

    def append_value(self, value: float) -> None:
        """Append a new data sample to the graph."""
        is_first = not self._times
        self._waiting_for_data = False
        self._set_waiting_state(False)
        self._elapsed += 0.1
        self._times.append(self._elapsed)
        self._values.append(value)

        if self._times:
            self._curve.setData(list(self._times), list(self._values))
            if self._values:
                self._point_marker.setData([self._times[-1]], [self._values[-1]])
                self._latest_value_lbl.setHtml(
                    f"<div style='padding: 1px 3px; color: #FFFFFF; font-family: Segoe UI, sans-serif; font-size: 8pt; font-weight: bold;'>{self._values[-1]:.1f}</div>"
                )
                self._latest_value_lbl.setPos(self._times[-1], self._values[-1])
                self._latest_value_lbl.setVisible(True)

            if is_first:
                self._snap_to_target_range()

    def clear_data(self) -> None:
        """Clear all stored data and reset the graph."""
        self._times.clear()
        self._values.clear()
        self._elapsed = 0.0
        self._curve.setData([], [])
        self._point_marker.clear()
        self._latest_value_lbl.setVisible(False)
        self._v_line.hide()
        self._h_line.hide()
        self._hud.hide()
        self._set_waiting_state(True)

    def set_data(self, times: list[float], values: list[float]) -> None:
        """Set the entire data curve."""
        self._times = deque(times, maxlen=self.MAX_POINTS)
        self._values = deque(values, maxlen=self.MAX_POINTS)
        if times:
            self._waiting_for_data = False
            self._set_waiting_state(False)
            self._elapsed = times[-1]
            self._curve.setData(list(self._times), list(self._values))
            if self._values:
                self._point_marker.setData([self._times[-1]], [self._values[-1]])
                self._latest_value_lbl.setHtml(
                    f"<div style='padding: 1px 3px; color: #FFFFFF; font-family: Segoe UI, sans-serif; font-size: 8pt; font-weight: bold;'>{self._values[-1]:.1f}</div>"
                )
                self._latest_value_lbl.setPos(self._times[-1], self._values[-1])
                self._latest_value_lbl.setVisible(True)
            self._snap_to_target_range()
        else:
            self._elapsed = 0.0
            self._curve.setData([], [])
            self._point_marker.clear()
            self._latest_value_lbl.setVisible(False)
            self._set_waiting_state(True)

    def configure_parameter(self, label: str, unit: str, color: str) -> None:
        """Dynamically update the parameter displayed by this graph and its axis ranges."""
        self._y_label = label
        self._y_unit = unit
        self._line_color = color

        # Build axis text:
        key = label if label != "Speed" else "RPM"
        if key == "RPM":
            axis_text = "RPM"
        else:
            axis_text = f"{key} ({unit})"

        # Update left axis label (12pt high contrast)
        self._plot_widget.setLabel(
            "left",
            f"<span style='color:#F1F5F9; font-family: Segoe UI; font-size:12pt; font-weight:600;'>{axis_text}</span>",
        )

        # Dynamic graph title mapping
        title_map = {
            "Speed": "Speed (RPM) vs Time",
            "RPM": "Speed (RPM) vs Time",
            "Voltage": "Voltage (V) vs Time",
            "Current": "Current (A) vs Time",
            "Power": "Power (W) vs Time",
            "Temperature": "Temperature (°C) vs Time",
            "Efficiency": "Efficiency (%) vs Time",
        }
        title_text = title_map.get(label, title_map.get(key, f"{label} ({unit}) vs Time"))

        self._plot_widget.setTitle(
            f"<span style='color:#E2E8F0; font-family: Segoe UI, Inter; font-size:11pt; font-weight:700;'>{title_text}</span>",
            size="11pt",
        )
        
        # Update curve pen and legend
        pen = pg.mkPen(color=color, width=2.5)
        self._curve.setPen(pen)
        self._curve.opts['antialias'] = True
        self._curve.opts['name'] = key
        self._legend.clear()
        self._legend.addItem(self._curve, key)

        # Update gradient fill
        try:
            grad = QLinearGradient(0, 0, 0, 1)
            grad.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
            c = QColor(color)
            c.setAlpha(200)
            grad.setColorAt(0.0, c)
            c2 = QColor(color)
            c2.setAlpha(20)
            grad.setColorAt(1.0, c2)
            brush = QBrush(grad)
            self._curve.setBrush(brush)
        except Exception:
            self._curve.setBrush(pg.mkBrush((16, 24, 39, 40)))

        # Update point marker and value label colors
        self._point_marker.setBrush(pg.mkBrush(color))
        self._latest_value_lbl.fill = pg.mkBrush(color)
        self._latest_value_lbl.border = pg.mkPen(color, width=1)
        
        # Snap immediately on parameter/graph switch
        self._snap_to_target_range()

    def set_waiting_state(self, active: bool) -> None:
        """Show or hide the waiting-for-data placeholder."""
        self._waiting_for_data = active
        self._placeholder.setVisible(active)
        if active:
            self._plot_widget.setXRange(0.0, 1.0)

    def _set_waiting_state(self, active: bool) -> None:
        self._placeholder.setVisible(active)
        if active:
            self._plot_widget.setXRange(0.0, 1.0)
