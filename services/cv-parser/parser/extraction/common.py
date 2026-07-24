"""
Shared section-splitting/field-guessing logic used by both pdf.py and
docx.py, so that logic isn't duplicated per file type (Strategy pattern:
each file type only implements extract_raw_text()).
"""
import re

SECTION_HEADERS = {
    "education": ["education", "academic background"],
    "experience": ["experience", "work experience", "employment history"],
    "skills": ["skills", "technical skills", "core competencies"],
    "certifications": ["certifications", "certificates", "licenses"],
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s()]{6,}\d)")


def _first_match(pattern, text):
    m = pattern.search(text or "")
    return m.group(0).strip() if m else ""


def _guess_name(text):
    for line in (text or "").splitlines():
        line = line.strip()
        if line and "@" not in line and not any(c.isdigit() for c in line):
            return line
    return ""


def _section_bounds(text, section_key):
    headers = SECTION_HEADERS.get(section_key, [section_key])
    lines = (text or "").splitlines()
    start = None
    for i, line in enumerate(lines):
        if any(h in line.strip().lower() for h in headers):
            start = i + 1
            break
    if start is None:
        return None, None
    end = len(lines)
    all_headers = [h for hs in SECTION_HEADERS.values() for h in hs]
    for i in range(start, len(lines)):
        if any(h in lines[i].strip().lower() for h in all_headers):
            end = i
            break
    return start, end


def _extract_section(text, section_key):
    start, end = _section_bounds(text, section_key)
    if start is None:
        return ""
    return "\n".join((text or "").splitlines()[start:end]).strip()


def _extract_list_section(text, section_key):
    block = _extract_section(text, section_key)
    return [line.strip("-• \t") for line in block.splitlines() if line.strip()]


def _extract_skills(text):
    raw = _extract_list_section(text, "skills")
    skills = set()
    for line in raw:
        for token in re.split(r"[,/|]", line):
            token = token.strip().lower()
            if token:
                skills.add(token)
    return sorted(skills)


def _extract_experience(text):
    block = _extract_section(text, "experience")
    if not block:
        return []
    jobs, current = [], None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] in "-•*":
            if current is None:
                current = {"title": "Unknown role", "bullets": []}
                jobs.append(current)
            current["bullets"].append(stripped.lstrip("-•* \t"))
        else:
            current = {"title": stripped, "bullets": []}
            jobs.append(current)
    return jobs


def extract_fields(raw_text: str) -> dict:
    """Turns raw extracted text into the structured field dict every
    parser (pdf.py, docx.py) returns, regardless of file type."""
    return {
        "name": _guess_name(raw_text),
        "email": _first_match(EMAIL_RE, raw_text),
        "phone": _first_match(PHONE_RE, raw_text),
        "professional_summary": _extract_section(raw_text, "summary"),
        "education": _extract_list_section(raw_text, "education"),
        "experience": _extract_experience(raw_text),
        "skills": _extract_skills(raw_text),
        "certifications": _extract_list_section(raw_text, "certifications"),
        "raw_text": raw_text or "",
    }