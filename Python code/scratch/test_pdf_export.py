import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from main import MainWindow, DataGenerator, _load_settings

def run_pdf_export_test():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    settings = _load_settings()
    data_gen = DataGenerator()
    window = MainWindow(data_gen, settings)
    
    # Populate history data on dashboard
    window._dashboard._history_times = [i * 0.1 for i in range(100)]
    window._dashboard._history_values = {
        "RPM": [1000 + i * 5 for i in range(100)],
        "Voltage": [12.0 + (i % 10) * 0.1 for i in range(100)],
        "Current": [2.0 + (i % 5) * 0.05 for i in range(100)],
        "Power": [24.0 + i * 0.1 for i in range(100)],
        "Temperature": [35.0 + i * 0.2 for i in range(100)],
        "Efficiency": [85.0 + (i % 8) * 0.5 for i in range(100)],
    }

    temp_pdf = os.path.join(tempfile.gettempdir(), "test_export_report_output.pdf")
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)

    # Monkeypatch getSaveFileName to return our temp_pdf path automatically
    from PySide6.QtWidgets import QFileDialog
    QFileDialog.getSaveFileName = lambda *args, **kwargs: (temp_pdf, "PDF Files (*.pdf)")

    # Execute PDF Export
    window._export_report_pdf()

    assert os.path.exists(temp_pdf), "PDF file was not created!"
    file_size = os.path.getsize(temp_pdf)
    print(f"SUCCESS: PDF export generated! File: {temp_pdf}, Size: {file_size} bytes")
    assert file_size > 10000, f"PDF file size is too small: {file_size} bytes"

    # Clean up test output
    os.remove(temp_pdf)
    print("SUCCESS: Temporary test PDF cleaned up.")

if __name__ == "__main__":
    run_pdf_export_test()
