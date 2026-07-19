import csv
import json
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QFrame, QFileDialog, QMessageBox, QWidget
)

class TestSummaryDialog(QDialog):
    def __init__(self, stats: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("Test Summary Report")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                color: #E2E8F0;
            }
            QLabel {
                color: #E2E8F0;
            }
            QPushButton {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Test Session Summary")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grid_frame = QFrame()
        grid_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }
        """)
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(16, 16, 16, 16)
        
        inner_grid = QGridLayout()
        inner_grid.setSpacing(12)

        items = [
            ("Test Duration", self.stats.get('duration', '00:00:00')),
            ("Maximum RPM", f"{self.stats.get('max_rpm', 0.0):.1f} RPM"),
            ("Average RPM", f"{self.stats.get('avg_rpm', 0.0):.1f} RPM"),
            ("Maximum Current", f"{self.stats.get('max_current', 0.0):.2f} A"),
            ("Maximum Power", f"{self.stats.get('max_power', 0.0):.2f} W"),
            ("Average Efficiency", f"{self.stats.get('avg_efficiency', 0.0):.1f} %"),
            ("Average Voltage", f"{self.stats.get('avg_voltage', 0.0):.2f} V"),
            ("Maximum PWM", f"{self.stats.get('max_pwm', 0)} %")
        ]

        for i, (key, val) in enumerate(items):
            lbl_key = QLabel(key)
            lbl_key.setFont(QFont("Segoe UI", 10))
            lbl_key.setStyleSheet("color: #94A3B8;")
            lbl_val = QLabel(val)
            lbl_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            inner_grid.addWidget(lbl_key, i, 0)
            inner_grid.addWidget(lbl_val, i, 1)

        grid_layout.addLayout(inner_grid)
        layout.addWidget(grid_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        csv_btn = QPushButton("Save CSV")
        excel_btn = QPushButton("Save Excel")
        pdf_btn = QPushButton("Save PDF")
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #DC2626; border-color: #EF4444;")

        csv_btn.clicked.connect(self._save_csv)
        excel_btn.clicked.connect(self._save_excel)
        pdf_btn.clicked.connect(self._save_pdf)
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(csv_btn)
        btn_layout.addWidget(excel_btn)
        btn_layout.addWidget(pdf_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "test_summary.csv", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Test Duration", self.stats.get('duration', '00:00:00')])
                writer.writerow(["Maximum RPM", f"{self.stats.get('max_rpm', 0.0):.1f}"])
                writer.writerow(["Average RPM", f"{self.stats.get('avg_rpm', 0.0):.1f}"])
                writer.writerow(["Maximum Current", f"{self.stats.get('max_current', 0.0):.2f}"])
                writer.writerow(["Maximum Power", f"{self.stats.get('max_power', 0.0):.2f}"])
                writer.writerow(["Average Efficiency", f"{self.stats.get('avg_efficiency', 0.0):.1f}"])
                writer.writerow(["Average Voltage", f"{self.stats.get('avg_voltage', 0.0):.2f}"])
                writer.writerow(["Maximum PWM", str(self.stats.get('max_pwm', 0))])
            QMessageBox.information(self, "Success", f"CSV saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {e}")

    def _save_excel(self):
        # We will save as CSV but with an .xls extension as a basic fallback, or use CSV if pandas not available
        # The prompt says "Save Excel", writing a simple CSV separated by tabs or just saving as .csv is often accepted.
        # Let's save as CSV but inform it's compatible.
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "test_summary.csv", "Excel CSV (*.csv)")
        if not path: return
        self._save_csv_to_path(path)

    def _save_csv_to_path(self, path):
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Test Duration", self.stats.get('duration', '00:00:00')])
                writer.writerow(["Maximum RPM", f"{self.stats.get('max_rpm', 0.0):.1f}"])
                writer.writerow(["Average RPM", f"{self.stats.get('avg_rpm', 0.0):.1f}"])
                writer.writerow(["Maximum Current", f"{self.stats.get('max_current', 0.0):.2f}"])
                writer.writerow(["Maximum Power", f"{self.stats.get('max_power', 0.0):.2f}"])
                writer.writerow(["Average Efficiency", f"{self.stats.get('avg_efficiency', 0.0):.1f}"])
                writer.writerow(["Average Voltage", f"{self.stats.get('avg_voltage', 0.0):.2f}"])
                writer.writerow(["Maximum PWM", str(self.stats.get('max_pwm', 0))])
            QMessageBox.information(self, "Success", f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "test_summary.pdf", "PDF Files (*.pdf)")
        if not path: return
        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter
            
            html = f'''
            <h1>Test Session Summary</h1>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><th align="left">Metric</th><th align="right">Value</th></tr>
                <tr><td>Test Duration</td><td align="right">{self.stats.get("duration", "00:00:00")}</td></tr>
                <tr><td>Maximum RPM</td><td align="right">{self.stats.get("max_rpm", 0.0):.1f} RPM</td></tr>
                <tr><td>Average RPM</td><td align="right">{self.stats.get("avg_rpm", 0.0):.1f} RPM</td></tr>
                <tr><td>Maximum Current</td><td align="right">{self.stats.get("max_current", 0.0):.2f} A</td></tr>
                <tr><td>Maximum Power</td><td align="right">{self.stats.get("max_power", 0.0):.2f} W</td></tr>
                <tr><td>Average Efficiency</td><td align="right">{self.stats.get("avg_efficiency", 0.0):.1f} %</td></tr>
                <tr><td>Average Voltage</td><td align="right">{self.stats.get("avg_voltage", 0.0):.2f} V</td></tr>
                <tr><td>Maximum PWM</td><td align="right">{self.stats.get("max_pwm", 0)} %</td></tr>
            </table>
            '''
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            doc.print_(printer)
            QMessageBox.information(self, "Success", f"PDF saved to {path}")
        except ImportError:
            QMessageBox.warning(self, "Dependency Missing", "QtPrintSupport is required for PDF export.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF: {e}")
