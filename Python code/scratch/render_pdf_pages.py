import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtPdf import QPdfDocument
from PySide6.QtGui import QImage
from PySide6.QtCore import QSize

def render_pages():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    temp_pdf = os.path.join(tempfile.gettempdir(), "test_export_report_output.pdf")
    
    # Generate the PDF first if not exists
    if not os.path.exists(temp_pdf):
        print("Generating PDF...")
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

    doc = QPdfDocument()
    status = doc.load(temp_pdf)
    if status != QPdfDocument.Error.None_:
        print(f"Error loading PDF: {status}")
        return

    print(f"Total pages: {doc.pageCount()}")
    
    target_dir = r"C:\Users\Coder\.gemini\antigravity-ide\brain\61a801ad-db27-4428-ba2f-42d19607be95\scratch"
    os.makedirs(target_dir, exist_ok=True)
    
    for page_num in range(doc.pageCount()):
        try:
            pt_size = doc.pagePointSize(page_num)
            w = int(pt_size.width())
            h = int(pt_size.height())
            size = QSize(w * 2, h * 2)  # High res render
        except Exception as e:
            print(f"Failed to get pagePointSize: {e}")
            size = QSize(1600, 2200)
        
        img = doc.render(page_num, size)
        p = os.path.join(target_dir, f"rendered_page_{page_num + 1}.png")
        img.save(p, "PNG")
        print(f"Page {page_num + 1} saved to {p}")

    doc.close()

if __name__ == "__main__":
    render_pages()
