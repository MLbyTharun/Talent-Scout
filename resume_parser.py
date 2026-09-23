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


# ---- 1b. Deterministic GitHub link extraction ----
# Catches links embedded as clickable hyperlink annotations (e.g. a
# "GitHub" icon/button) that plain text extraction above never sees,
# since the visible text might just say "GitHub" with the URL hidden
# in the PDF's link metadata. More reliable than asking the LLM to spot
# a URL that may not even appear as text in the extracted content.

def extract_github_links(pdf_path: str) -> dict:
    """
    Returns {"username": str | None, "repos": [github.com urls], "repo_apis": [api.github.com urls]}.
    Repos are deduped by owner/repo (a deep link to a specific file
    collapses to that repo's root URL).

    Sources: PDF hyperlink annotations AND plain-text github.com/... matches
    (resumes with non-clickable text links would otherwise yield zero repos).
    """
    all_links: list[str] = []
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                for link in page.get_links():
                    if "uri" in link:
                        all_links.append(link["uri"])
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"Couldn't read PDF links from {pdf_path}: {e}") from e

    # Fallback: plain-text URLs the annotation scan missed.
    try:
        resume_text = extract_resume_text(pdf_path)
        all_links.extend(
            "https://" + m.group(0) for m in GITHUB_URL_RE.finditer(resume_text)
        )
    except ValueError:
        pass  # scanned PDF — annotation links alone are all we have

    seen_repos = set()
    repos = []
    repo_apis = []
    profile_username = None
    repo_owners: set[str] = set()

    for uri in all_links:
        parsed = urlparse(uri if "://" in uri else f"https://{uri}")
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            continue

        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            continue
        if parts[0].lower() in RESERVED_GITHUB_ROUTES:
            continue

        if len(parts) == 1 and profile_username is None:
            # bare github.com/<user> profile link — only that counts as
            # the candidate's username (a repo under someone else's org
            # must not become their username)
            profile_username = parts[0]

        if len(parts) >= 2:
            # skip reserved second segments (e.g. github.com/orgs/... handled above,
            # plus actions like /settings, /sponsors for a user page)
            if parts[1].lower() in RESERVED_GITHUB_ROUTES:
                continue
            repo_key = f"{parts[0]}/{parts[1]}"
            if repo_key not in seen_repos:
                seen_repos.add(repo_key)
                repos.append(f"https://github.com/{repo_key}")
                repo_apis.append(f"https://api.github.com/repos/{repo_key}")
            repo_owners.add(parts[0])

    # username: explicit profile link wins; else the single owner of all
    # linked repos (ambiguous multi-owner resumes fall through to the LLM)
    username = profile_username
    if username is None and len(repo_owners) == 1:
        username = next(iter(repo_owners))

    return {"username": username, "repos": repos, "repo_apis": repo_apis}


# ---- 2. LLM structuring ----

def _get_client():
    from llm_client import get_llm_client

    return get_llm_client()

RESUME_SYSTEM_PROMPT = """You extract structured data from resume text.
Output ONLY valid JSON with this shape, no other text:

{
  "name": "string or null",
  "github_username": "string or null (look for a github.com/... link)",
  "skills": ["list", "of", "technical", "skills"],
  "experience": [{"title": "", "company": "", "duration": "", "highlights": ["..."]}],
  "projects": [{"name": "", "description": "", "tech_stack": ["..."]}],
  "education": [{"degree": "", "institution": "", "year": ""}]
}

If a field isn't present in the resume, use null or an empty list — never invent data.
"""


RESUME_SCHEMA_DEFAULTS = {
    "name": None,
    "github_username": None,
    "skills": [],
    "experience": [],
    "projects": [],
    "education": [],
}


def _strip_code_fences(raw: str) -> str:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    return raw


def structure_resume(resume_text: str, _retry: bool = True) -> dict:
    from llm_client import chat_completion

    client, model = _get_client()
    response = chat_completion(
        client,
        model,
        messages=[
            {"role": "system", "content": RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": resume_text},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = _strip_code_fences(response.choices[0].message.content)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        # model returned a JSON list/scalar or non-JSON text — retry once,
        # then fail with the raw output for diagnosis
        if _retry:
            return structure_resume(resume_text, _retry=False)
        raise ValueError(
            f"Model did not return a JSON object after retry. Raw output "
            f"(first 300 chars): {raw[:300]!r}"
        )

    # fill any missing keys with safe defaults so downstream code
    # (parse_resume_node, evaluate_node) never has to guess
    return {**RESUME_SCHEMA_DEFAULTS, **data}

