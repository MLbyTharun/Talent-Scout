"""
Resume parser — turns a PDF resume into (a) raw text and (b) structured
JSON (skills, experience, projects, education) that the evaluator agent
can compare against the JD and GitHub data.

Two-step process, matching how the rest of the graph works:
  1. Deterministic: pull text out of the PDF (no LLM, cheap, fast)
  2. LLM: turn messy resume text into structured fields
"""

import json
import re
from urllib.parse import urlparse

import pymupdf as fitz  # PyMuPDF
import pdfplumber

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# github.com routes that are not user profiles — never treat as username
# even if they appear as the first path segment.
RESERVED_GITHUB_ROUTES = {
    "topics", "sponsors", "settings", "marketplace", "explore",
    "organizations", "orgs", "trending", "collections", "events",
    "features", "pricing", "about", "blog", "login", "join",
}

GITHUB_URL_RE = re.compile(
    r"github\.com/([A-Za-z0-9-]+(?:/[A-Za-z0-9_.-]+)?)", re.IGNORECASE
)


# ---- 1. Deterministic text extraction ----

def extract_resume_text(pdf_path: str) -> str:
    """
    Resumes are text-heavy, single/double-column documents — text
    extraction is the right tool here (not rasterization). If a resume
    ever comes back garbled or empty, that's the signal it's a scanned
    image and needs OCR instead — not handled here, flag it if you hit one.
    """
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n".join(text_parts).strip()

    if not text:
        raise ValueError(
            f"No extractable text in {pdf_path} — likely a scanned/image "
            "resume. Needs OCR (pytesseract), not handled by this parser."
        )

    return text

