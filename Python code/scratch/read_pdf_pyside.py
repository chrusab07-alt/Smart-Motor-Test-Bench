import os
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtPdf import QPdfDocument
from scratch.test_pdf_export import run_pdf_export_test

def inspect_pdf():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    temp_pdf = os.path.join(tempfile.gettempdir(), "test_export_report_output.pdf")
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
        
    # Monkeypatch cleanup to keep the file
    import scratch.test_pdf_export
    # Modify run_pdf_export_test to not remove the pdf
    # Let's just run it manually here
    from main import MainWindow, _load_settings, DataGenerator
    from PySide6.QtWidgets import QFileDialog
    
    settings = _load_settings()
    data_gen = DataGenerator()
    window = MainWindow(data_gen, settings)
    
    window._dashboard._history_times = [i * 0.1 for i in range(100)]
    window._dashboard._history_values = {
        "RPM": [1000 + i * 5 for i in range(100)],
        "Voltage": [12.0 + (i % 10) * 0.1 for i in range(100)],
        "Current": [2.0 + (i % 5) * 0.05 for i in range(100)],
        "Power": [24.0 + i * 0.1 for i in range(100)],
        "Temperature": [35.0 + i * 0.2 for i in range(100)],
        "Efficiency": [85.0 + (i % 8) * 0.5 for i in range(100)],
    }
    
    QFileDialog.getSaveFileName = lambda *args, **kwargs: (temp_pdf, "PDF Files (*.pdf)")
    window._export_report_pdf()
    
    if not os.path.exists(temp_pdf):
        print("PDF was not created.")
        return
        
    doc = QPdfDocument()
    status = doc.load(temp_pdf)
    if status != QPdfDocument.Error.None_:
        print(f"Error loading PDF: {status}")
        return
        
    print(f"PDF Page Count: {doc.pageCount()}")
    for i in range(doc.pageCount()):
        size = doc.pageSize(i)
        print(f"Page {i+1}: Size = {size.width()}x{size.height()}")
        
    doc.close()
    
    # Clean up after we printed
    os.remove(temp_pdf)

if __name__ == "__main__":
    inspect_pdf()
