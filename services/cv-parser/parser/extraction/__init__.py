"""Strategy pattern: one extraction module per file type (pdf.py, docx.py).
Each exposes the same parse(file_path) -> dict interface."""


def get_parser(file_type: str):
    if file_type == "pdf":
        from . import pdf
        return pdf
    if file_type == "docx":
        from . import docx
        return docx
    raise ValueError(f"Unsupported file_type: {file_type}")