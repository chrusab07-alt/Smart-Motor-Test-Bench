"""
data_log.py
-----------
Dedicated Data Logger page for the Smart Motor Test Bench.
Includes a table view populated with realistic historical telemetry data,
live keyword search filtering, and fully functional Import/Export CSV actions.
"""

from __future__ import annotations

import csv
import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView, QSizePolicy
)

class DataLogPage(QWidget):
    """
    Dedicated Data Logger page.
    Allows viewing, filtering, clearing, importing, and exporting telemetry records.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._generate_dummy_data()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────
        title_lbl = QLabel("DATA LOGGER & TELEMETRY LOG")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")
        root_layout.addWidget(title_lbl)

        # ── Toolbar Row (Search + Buttons) ─────────────────────────────
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        # Search box
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Search logs (e.g. FWD, Running, RPM)...")
        self._search_input.setFixedHeight(38)
        self._search_input.setFont(QFont("Segoe UI", 10))
        self._search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 0 12px;
            }
            QLineEdit:focus {
                border-color: #0F62FE;
            }
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self._search_input, stretch=2)

        # Action Buttons
        self._import_btn = self._make_tool_button("Import CSV", "#333333", "#3F3F46")
        self._export_btn = self._make_tool_button("Export CSV", "#007ACC", "#005A9E")
        self._clear_btn  = self._make_tool_button("Clear Log", "#D32F2F", "#B71C1C")

        self._import_btn.clicked.connect(self._on_import_clicked)
        self._export_btn.clicked.connect(self._on_export_clicked)
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        toolbar_layout.addWidget(self._import_btn)
        toolbar_layout.addWidget(self._export_btn)
        toolbar_layout.addWidget(self._clear_btn)
        root_layout.addLayout(toolbar_layout)

        # ── Table Widget ───────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Timestamp", "Speed (RPM)", "Voltage (V)", "Current (A)", "Power (W)", "Efficiency (%)", "Status"
        ])
        
        # Style table headers and cells
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #0F172A;
                color: #CCCCCC;
                gridline-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 14px;
                font-size: 13px;
                alternate-background-color: #131E35;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item:selected {
                background-color: #0F62FE;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #A8B3C5;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                font-size: 12px;
            }
        """)
        
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setShowGrid(True)
        self._table.setAlternatingRowColors(True)

        # Header stretch sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Timestamp column fit

        root_layout.addWidget(self._table)

    def _make_tool_button(self, text: str, bg: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #FFFFFF;
                border: 1px solid {hover};
                border-radius: 8px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        return btn

    def _generate_dummy_data(self) -> None:
        """Prefill the table with realistic telemetry data records."""
        now = datetime.datetime.now()
        dummy_runs = [
            (now - datetime.timedelta(seconds=180), 0, 11.95, 0.0, 0.0, 0.0, "Stopped"),
            (now - datetime.timedelta(seconds=170), 200, 11.85, 0.45, 5.33, 52.0, "Starting FWD"),
            (now - datetime.timedelta(seconds=160), 850, 11.75, 1.10, 12.92, 74.5, "Running FWD"),
            (now - datetime.timedelta(seconds=150), 1082, 11.72, 1.48, 17.34, 82.1, "Running FWD"),
            (now - datetime.timedelta(seconds=140), 1095, 11.71, 1.50, 17.56, 83.2, "Running FWD"),
            (now - datetime.timedelta(seconds=130), 1102, 11.72, 1.49, 17.46, 83.4, "Running FWD"),
            (now - datetime.timedelta(seconds=120), 1100, 11.71, 1.50, 17.56, 83.3, "Running FWD"),
            (now - datetime.timedelta(seconds=110), 800, 11.78, 1.05, 12.37, 72.8, "Decelerating"),
            (now - datetime.timedelta(seconds=100), 0, 11.96, 0.0, 0.0, 0.0, "Stopped"),
            (now - datetime.timedelta(seconds=90), -150, 11.90, 0.38, 4.52, 48.0, "Starting REV"),
            (now - datetime.timedelta(seconds=80), -720, 11.80, 0.98, 11.56, 71.0, "Running REV"),
            (now - datetime.timedelta(seconds=70), -1050, 11.74, 1.42, 16.67, 81.5, "Running REV"),
            (now - datetime.timedelta(seconds=60), -1075, 11.72, 1.46, 17.11, 82.8, "Running REV"),
            (now - datetime.timedelta(seconds=50), -1080, 11.73, 1.45, 17.01, 82.9, "Running REV"),
            (now - datetime.timedelta(seconds=40), -450, 11.84, 0.62, 7.34, 62.0, "Decelerating"),
            (now - datetime.timedelta(seconds=30), 0, 11.97, 0.0, 0.0, 0.0, "Stopped"),
        ]

        self._table.setRowCount(0)
        for ts, rpm, volt, curr, pwr, eff, status in dummy_runs:
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)
            
            # Populate row cells
            self._table.setItem(row_idx, 0, QTableWidgetItem(ts.strftime("%Y-%m-%d %H:%M:%S")))
            self._table.setItem(row_idx, 1, QTableWidgetItem(f"{rpm}"))
            self._table.setItem(row_idx, 2, QTableWidgetItem(f"{volt:.2f}"))
            self._table.setItem(row_idx, 3, QTableWidgetItem(f"{curr:.2f}"))
            self._table.setItem(row_idx, 4, QTableWidgetItem(f"{pwr:.2f}"))
            self._table.setItem(row_idx, 5, QTableWidgetItem(f"{eff:.1f}"))
            
            status_item = QTableWidgetItem(status)
            if "Stopped" in status:
                status_item.setForeground(QColor("#EF4444")) # Muted Red
            elif "Running" in status:
                status_item.setForeground(QColor("#10B981")) # Green
            elif "Starting" in status:
                status_item.setForeground(QColor("#3B82F6")) # Blue
            else:
                status_item.setForeground(QColor("#F59E0B")) # Orange
            self._table.setItem(row_idx, 6, status_item)

    # ------------------------------------------------------------------ #
    #  Actions & Slots
    # ------------------------------------------------------------------ #
    def add_log_entry(self, rpm: float, volt: float, curr: float, pwr: float, eff: float, status: str) -> None:
        """Appends a new real-time log record to the table."""
        row_idx = 0 # Insert at top
        self._table.insertRow(row_idx)
        
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._table.setItem(row_idx, 0, QTableWidgetItem(ts))
        self._table.setItem(row_idx, 1, QTableWidgetItem(f"{rpm:.0f}"))
        self._table.setItem(row_idx, 2, QTableWidgetItem(f"{volt:.2f}"))
        self._table.setItem(row_idx, 3, QTableWidgetItem(f"{curr:.2f}"))
        self._table.setItem(row_idx, 4, QTableWidgetItem(f"{pwr:.2f}"))
        self._table.setItem(row_idx, 5, QTableWidgetItem(f"{eff:.1f}"))
        
        status_item = QTableWidgetItem(status)
        if "Stopped" in status:
            status_item.setForeground(QColor("#EF4444"))
        elif "Running" in status:
            status_item.setForeground(QColor("#10B981"))
        else:
            status_item.setForeground(QColor("#F59E0B"))
        self._table.setItem(row_idx, 6, status_item)

    def _on_search_changed(self, text: str) -> None:
        """Filter table rows dynamically based on the search query."""
        query = text.lower().strip()
        for row in range(self._table.rowCount()):
            match = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self._table.setRowHidden(row, not match)

    def _on_clear_clicked(self) -> None:
        """Wipes all rows in the log table."""
        confirm = QMessageBox.question(
            self, "Clear Log History",
            "Are you sure you want to permanently clear all telemetry logs?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self._table.setRowCount(0)

    def _on_export_clicked(self) -> None:
        """Saves current table contents to a user-specified CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Log to CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header row
                headers = [self._table.horizontalHeaderItem(c).text() for c in range(self._table.columnCount())]
                writer.writerow(headers)
                
                # Data rows
                for r in range(self._table.rowCount()):
                    row_data = []
                    for c in range(self._table.columnCount()):
                        item = self._table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            main_win = self.window()
            if hasattr(main_win, '_show_toast'):
                main_win._show_toast("✅ CSV exported successfully")
            else:
                QMessageBox.information(self, "Export Successful", f"Log successfully exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during CSV write:\n{str(e)}")

    def _on_import_clicked(self) -> None:
        """Loads log rows from a selected CSV file into the table view."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Log from CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers or len(headers) < 7:
                    raise ValueError("Invalid CSV format. Expected at least 7 columns.")
                
                self._table.setRowCount(0)
                for row_data in reader:
                    if len(row_data) < 7:
                        continue
                    row_idx = self._table.rowCount()
                    self._table.insertRow(row_idx)
                    for col_idx, cell in enumerate(row_data[:7]):
                        item = QTableWidgetItem(cell)
                        # Re-apply color coding to imported status
                        if col_idx == 6:
                            if "Stopped" in cell:
                                item.setForeground(QColor("#EF4444"))
                            elif "Running" in cell:
                                item.setForeground(QColor("#10B981"))
                            else:
                                item.setForeground(QColor("#F59E0B"))
                        self._table.setItem(row_idx, col_idx, item)
            QMessageBox.information(self, "Import Successful", "Log history loaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"An error occurred during CSV read:\n{str(e)}")
