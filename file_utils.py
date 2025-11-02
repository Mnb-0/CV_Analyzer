# file_utils.py
# Contains utility functions for extracting text from files.

import docx
import pdfplumber

def extract_text_from_pdf(pdf_file_path):
    """Extracts all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

def extract_text_from_docx(docx_file_path):
    """Extracts all text from a DOCX file."""
    text = ""
    try:
        doc = docx.Document(docx_file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"DOCX Error: {e}")
        return None