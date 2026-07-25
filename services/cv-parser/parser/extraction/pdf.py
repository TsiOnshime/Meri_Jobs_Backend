"""PDF text extraction (pdfplumber)."""
from .common import extract_fields


def extract_raw_text(file_path: str) -> str:
    try:
        import pdfplumber
        text_chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")
        text = "\n".join(text_chunks).strip()
        if text:
            return text
    except Exception:
        pass  # fall through to PyPDF2

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        # Both extractors failed -- likely a scanned image PDF with no text
        # layer. Return empty string rather than crashing; the confidence
        # scorer will naturally flag this for needs_review since every
        # field comes back empty.
        return ""


def parse(file_path: str) -> dict:
    raw_text = extract_raw_text(file_path)
    return extract_fields(raw_text)