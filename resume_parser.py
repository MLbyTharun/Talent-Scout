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


