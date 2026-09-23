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

