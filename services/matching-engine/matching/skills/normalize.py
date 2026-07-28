"""Lowercase, split compound skills, strip punctuation."""
import re

COMPOUND_DELIMITERS = re.compile(r"[/,&+]|\band\b")
NON_WORD_CHARS = re.compile(r"[^\w\s]")

def normalize(raw_skill: str) -> list[str]:
    text = raw_skill.strip().lower()
    parts = COMPOUND_DELIMITERS.split(text)
    cleaned = []
    for part in parts:
        part = NON_WORD_CHARS.sub("", part).strip()
        if part:
            cleaned.append(part)
    
    return cleaned