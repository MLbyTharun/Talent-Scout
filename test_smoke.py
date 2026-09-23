"""Smoke tests for talent-scout (live: GitHub + LLM).

Run: python test_smoke.py
Requires .env with GITHUB_TOKEN + an LLM key (GROQ_API_KEY or GOOGLE_API_KEY).
PDF fixture: place a resume at Tharun.pdf (gitignored) — tests that need it
are skipped if it's missing.
"""

import os
import shutil
import tempfile

from resume_parser import extract_resume_text, extract_github_links, structure_resume
from github_fetcher import days_since_last_push, get_evaluable_profiles
from agent_graph import build_graph, evaluate_node
from batch_runner import run_batch

PDF = "Tharun.pdf"
HAS_PDF = os.path.exists(PDF)
JD = (
    "AI / Generative AI / Agentic AI Intern: Python, LangChain, LangGraph, CrewAI, "
    "RAG pipelines and vector DBs, tool calling, structured outputs. "
    "Must have built real AI systems, not tutorial chatbots."
)

passed = []
skipped = []


def check(name, fn, needs_pdf=False):
    if needs_pdf and not HAS_PDF:
        skipped.append(name)
        print(f"SKIP {name} (missing {PDF})")
        return
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_resume_text():
    t = extract_resume_text(PDF)
    assert len(t) > 500, "resume text too short"
    try:
        extract_resume_text("nope-missing.pdf")
        raise AssertionError("should have raised")
    except Exception:
        pass


def test_github_links():
    links = extract_github_links(PDF)
    assert links["username"], links
    assert len(links["repos"]) >= 1, links
    assert len(links["repo_apis"]) == len(links["repos"])


def test_days_since_push_edge():
    assert days_since_last_push(None) > 10**6
    assert days_since_last_push("not-a-date") > 10**6
    assert days_since_last_push("2024-01-01T00:00:00Z") >= 0


def test_fetcher_max_repos():
    apis = extract_github_links(PDF)["repo_apis"]
    profs = get_evaluable_profiles(apis, max_repos=2)
    assert len(profs) <= 2, profs
    assert all("name" in p and "readme" in p for p in profs)


def test_evaluate_node_requires_jd():
    try:
        evaluate_node({"resume_data": {}, "repo_profiles": []})
        raise AssertionError("should have raised on missing jd")
    except ValueError:
        pass


def test_full_graph():
    app = build_graph(use_crew=False)
    r = app.invoke({"resume_path": PDF, "jd_text": JD})
    notes = r["notes"]
    assert not notes.get("parse_error"), notes.get("raw_output", "")[:300]
    for k in ("resume_jd_match", "github_evidence", "gaps", "overall_notes"):
        assert k in notes, f"missing {k}"
    assert len(r["repo_profiles"]) >= 1


def test_batch_order():
    tmp = tempfile.mkdtemp(prefix="ts-test-")
    try:
        p1 = os.path.join(tmp, "a.pdf")
        p2 = os.path.join(tmp, "b.pdf")
        shutil.copy(PDF, p1)
        shutil.copy(PDF, p2)
        res = run_batch([p1, p2], JD, use_crew=False, max_workers=1)
        assert [r.resume_path for r in res] == [p1, p2], "order not preserved"
        assert all(r.success for r in res), [r.error for r in res]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


for name, fn, needs_pdf in [
    ("resume_text", test_resume_text, True),
    ("github_links", test_github_links, True),
    ("days_since_push_edge", test_days_since_push_edge, False),
    ("fetcher_max_repos", test_fetcher_max_repos, True),
    ("evaluate_node_requires_jd", test_evaluate_node_requires_jd, False),
    ("full_graph", test_full_graph, True),
    ("batch_order", test_batch_order, True),
]:
    check(name, fn, needs_pdf=needs_pdf)

total = len(passed) + len(skipped)
print(f"\n{len(passed)}/{total} SMOKE TESTS PASSED" + (f", {len(skipped)} skipped" if skipped else ""))
