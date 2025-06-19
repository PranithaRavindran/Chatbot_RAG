import PyPDF2
from pdf2image import convert_from_path
import pytesseract

def extract_text(pdf_path):  # Remove is_scanned parameter completely
    """Text-only PDF extraction"""
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        return " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
