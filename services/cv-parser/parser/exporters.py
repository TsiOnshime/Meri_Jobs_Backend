"""FR2.4 -- export the optimized CV (parsed + user edits applied) as a PDF."""
import io


def build_cv_pdf(cv, parsed_cv) -> bytes:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=LETTER)
    _, height = LETTER
    y = height - 1 * inch

    def line(text, size=11, gap=16, bold=False):
        nonlocal y
        doc.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        doc.drawString(1 * inch, y, text)
        y -= gap

    line(parsed_cv.name or "Unnamed", size=16, gap=22, bold=True)
    contact = " | ".join(filter(None, [parsed_cv.email, parsed_cv.phone]))
    if contact:
        line(contact, size=10, gap=20)

    if parsed_cv.professional_summary:
        line("Professional Summary", bold=True)
        for chunk in _wrap(parsed_cv.professional_summary, 90):
            line(chunk, size=10)
        y -= 6

    if parsed_cv.experience:
        line("Experience", bold=True)
        for job in parsed_cv.experience:
            title = job.get("title", "") if isinstance(job, dict) else str(job)
            line(title, size=11, bold=True)
            for bullet in (job.get("bullets", []) if isinstance(job, dict) else []):
                line(f"  - {bullet}", size=10)
        y -= 6

    if parsed_cv.skills:
        line("Skills", bold=True)
        line(", ".join(parsed_cv.skills), size=10)
        y -= 6

    if parsed_cv.education:
        line("Education", bold=True)
        for entry in parsed_cv.education:
            line(f"  - {entry}", size=10)

    doc.save()
    return buffer.getvalue()


def _wrap(text: str, width: int):
    words, current, out = text.split(), "", []
    for w in words:
        if len(current) + len(w) + 1 > width:
            out.append(current)
            current = w
        else:
            current = f"{current} {w}".strip()
    if current:
        out.append(current)
    return out