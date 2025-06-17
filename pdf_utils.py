import PyPDF2
from pdf2image import convert_from_path
import pytesseract

def extract_text(pdf_path, is_scanned=False):
    if is_scanned:
        images = convert_from_path(pdf_path)
        return " ".join(pytesseract.image_to_string(img) for img in images)
    else:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            return " ".join(page.extract_text() for page in pdf.pages)