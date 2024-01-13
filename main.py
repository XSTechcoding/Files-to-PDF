import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from docx2pdf import convert
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import PyPDF2 as pdf

class FileConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowTitle("Advanced File to PDF Converter")
        self.setGeometry(100, 100, 600, 250)

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        self.input_label = QLabel("Select file(s) to convert/merge:", self)
        layout.addWidget(self.input_label)

        self.input_files = []
        self.input_list = QLabel("", self)
        layout.addWidget(self.input_list)

        browse_button = QPushButton("Browse", self)
        browse_button.clicked.connect(self.browse_files)
        layout.addWidget(browse_button)

        self.output_label = QLabel("Select output folder:", self)
        layout.addWidget(self.output_label)

        self.output_folder = ""
        self.output_folder_label = QLabel("", self)
        layout.addWidget(self.output_folder_label)

        output_button = QPushButton("Select Folder", self)
        output_button.clicked.connect(self.select_output_folder)
        layout.addWidget(output_button)

        convert_button = QPushButton("Convert/Merge to PDF", self)
        convert_button.clicked.connect(self.convert_to_pdf)
        layout.addWidget(convert_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("", self)
        layout.addWidget(self.result_label)

        layout.setAlignment(Qt.AlignTop)
        self.central_widget.setLayout(layout)

    def browse_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Supported files (*.docx *.txt *.jpg *.jpeg *.png *.pdf)")
        if file_dialog.exec_():
            self.input_files = file_dialog.selectedFiles()
            self.input_list.setText("\n".join(self.input_files))

    def select_output_folder(self):
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.Directory)
        if folder_dialog.exec_():
            self.output_folder = folder_dialog.selectedFiles()[0]
            self.output_folder_label.setText(self.output_folder)

    def convert_to_pdf(self):
        if not self.input_files:
            self.result_label.setText("Please select file(s) to convert/merge.")
            return

        if not self.output_folder:
            self.result_label.setText("Please select an output folder.")
            return

        self.converter_thread = ConverterThread(self.input_files, self.output_folder)
        self.converter_thread.progress_signal.connect(self.update_progress)
        self.converter_thread.finished_signal.connect(self.on_conversion_finished)
        self.converter_thread.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def on_conversion_finished(self):
        self.result_label.setText(f"Conversion/Merging complete. PDF(s) saved to {self.output_folder}")

class ConverterThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, input_files, output_folder):
        super().__init__()
        self.input_files = input_files
        self.output_folder = output_folder

    def run(self):
        pdf_files = []
        total_files = len(self.input_files)
        for i, input_file in enumerate(self.input_files):
            file_extension = os.path.splitext(input_file)[-1].lower()
            if file_extension == ".docx":
                try:
                    convert(input_file, os.path.join(self.output_folder, f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf"))
                    pdf_files.append(f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf")
                except Exception as e:
                    print(f"Error converting {input_file} to PDF: {str(e)}")
            elif file_extension == ".txt":
                try:
                    self.text_to_pdf(input_file)
                    pdf_files.append(f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf")
                except Exception as e:
                    print(f"Error converting {input_file} to PDF: {str(e)}")
            elif file_extension in (".jpg", ".jpeg", ".png"):
                try:
                    self.image_to_pdf(input_file)
                    pdf_files.append(f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf")
                except Exception as e:
                    print(f"Error converting {input_file} to PDF: {str(e)}")
            elif file_extension == ".pdf":
                pdf_files.append(input_file)

            progress = int((i + 1) / total_files * 100)
            self.progress_signal.emit(progress)

        if pdf_files:
            self.merge_pdfs(pdf_files)
        self.finished_signal.emit()

    def text_to_pdf(self, input_file):
        output_file = os.path.join(self.output_folder, f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf")
        c = canvas.Canvas(output_file, pagesize=letter)
        with open(input_file, 'r') as text_file:
            text_content = text_file.read()
        c.drawString(100, 750, text_content)
        c.save()

    def image_to_pdf(self, input_file):
        output_file = os.path.join(self.output_folder, f"{os.path.splitext(os.path.basename(input_file))[0]}.pdf")
        img = Image.open(input_file)
        img = img.convert("RGB")
        img.save(output_file, "PDF", resolution=100.0)

    def merge_pdfs(self, pdf_files):
        output_file = os.path.join(self.output_folder, "merged.pdf")
        pdf_merger = pdf.PdfMerger()

        for pdf_file in pdf_files:
            pdf_merger.append(pdf_file)

        pdf_merger.write(output_file)
        pdf_merger.close()

def main():
    app = QApplication(sys.argv)
    converter = FileConverter()
    converter.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
