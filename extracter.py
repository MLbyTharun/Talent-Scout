"""
Resume parser — turns a PDF resume into (a) raw text and (b) structured
JSON (skills, experience, projects, education) that the evaluator agent
can compare against the JD and GitHub data.

Two-step process, matching how the rest of the graph works:
  1. Deterministic: pull text out of the PDF (no LLM, cheap, fast)
  2. LLM: turn messy resume text into structured fields
"""

import json
import os
from urllib.parse import urlparse

import fitz  # PyMuPDF
import pdfplumber
from openai import OpenAI
from github_fetcher import get_evaluable_profiles

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
    """
    doc = fitz.open(pdf_path)

    all_links = []
    for page in doc:
        for link in page.get_links():
            if "uri" in link:
                all_links.append(link["uri"])

    seen_repos = set()
    repos = []
    repo_apis = []
    username = None

    for uri in all_links:
        parsed = urlparse(uri)
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            continue

        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            continue

        if username is None:
            username = parts[0]  # first github.com/<x>/... link found sets it

        if len(parts) >= 2:
            repo_key = f"{parts[0]}/{parts[1]}"
            if repo_key not in seen_repos:
                seen_repos.add(repo_key)
                repos.append(f"https://github.com/{repo_key}")
                repo_apis.append(f"https://api.github.com/repos/{repo_key}")

    return {"username": username, "repos": repos, "repo_apis": repo_apis}

# ---- 2. LLM structuring ----
from dotenv import load_dotenv
load_dotenv()
_nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

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


def structure_resume(resume_text: str, _retry: bool = True) -> dict:
    response = _nim_client.chat.completions.create(
        model="z-ai/glm-5.2",
        messages=[
            {"role": "system", "content": RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": resume_text},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        if _retry:
            # one retry — models occasionally wrap JSON in prose despite
            # the response_format hint; a second pass usually fixes it
            return structure_resume(resume_text, _retry=False)
        raise ValueError(
            f"Model did not return valid JSON after retry. Raw output "
            f"(first 300 chars): {raw[:300]!r}"
        )

    # fill any missing keys with safe defaults so downstream code
    # (parse_resume_node, evaluate_node) never has to guess
    return {**RESUME_SCHEMA_DEFAULTS, **data}


# ---- 3. Graph node ----

def parse_resume_node(state: dict) -> dict:
    """
    Drop-in node for agent_graph.py. Expects state["resume_path"],
    produces state["resume_text"] and state["resume_data"].

    GitHub username resolution order:
      1. state["username"] if explicitly passed in
      2. a github.com link found in the PDF's hyperlink annotations (reliable)
      3. the LLM's best guess from the resume text (fallback)
    """
    text = extract_resume_text(state["resume_path"])
    data = structure_resume(text)
    links = extract_github_links(state["resume_path"])

    result = {
        "resume_text": text,
        "resume_data": data,
        "linked_repos": links["repos"],       # for display/notes
        "repo_apis": links["repo_apis"],       # what fetch_github_node actually uses
    }

    username = state.get("username") or links["username"] or data.get("github_username")
    if not username:
        raise ValueError(
            "No GitHub username found — none was passed in state['username'], "
            "none found as a hyperlink in the PDF, and none extracted from "
            "the resume text. Pass it explicitly: "
            "app.invoke({'resume_path': ..., 'username': 'their-handle', ...})"
        )
    result["username"] = username

    return result


#-------------------------------------------------------------------
xi=extract_github_links("Tharun.pdf")["repo_apis"]
data = get_evaluable_profiles(xi)
for item in data:
    print(item["name"])




#if __name__ == "__main__":
#    import sys
#
#    
#    text = extract_resume_text("Tharun.pdf")
#    print("--- Extracted text (first 500 chars) ---")
#    print(text[:500])
#    print("\n--- Structured (requires NVIDIA_API_KEY) ---")
#    print(json.dumps(structure_resume(text), indent=2))