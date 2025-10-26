import os
import re
import warnings
import unicodedata
from docx import Document
from pypdf import PdfReader

# ---------------------- Extraction ----------------------
def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        print(f"Error reading DOCX: {path} -> {e}")
        return ""

def extract_text_from_pdf(path):
    text = ""
    try:
        # Custom warning handler for pypdf
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            reader = PdfReader(path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        # If pypdf complained about malformed objects, report it
        for w in caught_warnings:
            if "Ignoring wrong pointing object" in str(w.message):
                print(f"[Warning] {os.path.basename(path)} -> {w.message}")

    except Exception as e:
        print(f"[Error] Failed reading PDF: {path} -> {e}")

    return text.strip()

def normalize_name(filename):
    base = os.path.splitext(filename)[0]
    base = re.sub(r'\(\d+\)', '', base)
    base = re.sub(r'\s+', '_', base.strip())
    return base.lower()

def read_cvs(dataset_folder="DataSet"):
    cvs = {}
    for root, _, files in os.walk(dataset_folder):
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower().endswith(".pdf"):
                name = normalize_name(file)
                text = extract_text_from_pdf(file_path)
                cvs.setdefault(name, {})["pdf"] = text
            elif file.lower().endswith(".docx"):
                name = normalize_name(file)
                text = extract_text_from_docx(file_path)
                cvs.setdefault(name, {})["docx"] = text
    return cvs

# ---------------------- Cleaning ----------------------
def clean_and_preprocess(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r'[\(\[\{]\d+[\)\]\}]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-z0-9+\.\#_ ]+', '', text)

    tokens = text.split()
    whitelist = {'c', 'c++', 'cv', 'ml', 'ai', 'r', 'go'}
    tokens = [t for t in tokens if len(t) > 1 or t in whitelist]
    return " ".join(tokens).strip()
