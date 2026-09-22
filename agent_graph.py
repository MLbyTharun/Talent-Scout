"""
The actual agent: a LangGraph graph that ties together
resume + JD + GitHub repo data, and produces evaluation notes.

Flow (matches the diagram from earlier):
  START -> fetch_github (deterministic, uses GITHUB_TOKEN) -> evaluate (LLM call) -> END

Run:
    export GITHUB_TOKEN=ghp_xxx
    export GROQ_API_KEY=gsk_xxx   (or GOOGLE_API_KEY with LLM_PROVIDER=google)
    python agent_graph.py
"""

import os
import json
from typing import TypedDict

import requests
from langgraph.graph import StateGraph, END

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from github_fetcher import get_evaluable_profiles
from resume_parser import parse_resume_node


def _get_eval_client():
    from llm_client import get_llm_client

    return get_llm_client("heavy")  # repo evaluation is heavy -> Gemini


# ---- 1. State: the shared data every node reads/writes ----

class EvalState(TypedDict, total=False):
    resume_path: str       # input: path to the resume PDF
    username: str            # filled in by parse_resume if found in resume, else pass it in directly
    resume_text: str         # filled in by parse_resume
    resume_data: dict        # filled in by parse_resume (structured JSON)
    linked_repos: list       # filled in by parse_resume — github.com urls, for display
    repo_apis: list          # filled in by parse_resume — direct api.github.com urls, what fetch_github_node uses
    jd_text: str
    repo_profiles: list
    github_fetch_error: str  # set if GitHub fetch failed (rate limit, bad token, outage)
    notes: dict              # filled in by evaluate (structured JSON notes)


# ---- 2. Node: GitHub fetching (deterministic — no LLM here) ----

def fetch_github_node(state: EvalState) -> dict:
    """
    This is the node from the diagram's teal chain.
    Scoped to only what the candidate directly linked in their resume —
    no listing call, no broader sweep of their GitHub activity. Repo
    discovery already happened upstream in resume_parser.py; this node
    just fetches full data for the exact repos it was handed.
    """
    apis = state.get("repo_apis", [])
    if not apis:
        return {"repo_profiles": []}

    try:
        profiles = get_evaluable_profiles(apis)
    except requests.RequestException as e:
        # bad url, rate limit, timeout, or GitHub outage — don't kill the
        # whole evaluation over it, let evaluate_node know repos are
        # unavailable and continue with resume-only judgment
        return {"repo_profiles": [], "github_fetch_error": str(e)}
    except (KeyError, ValueError, AttributeError) as e:
        return {"repo_profiles": [], "github_fetch_error": f"malformed GitHub response: {e}"}

    # trim READMEs so we don't blow the prompt budget on any one repo
    for p in profiles:
        if p.get("readme"):
            p["readme"] = p["readme"][:2000]

    return {"repo_profiles": profiles}


# ---- 3. Node: evaluation (the LLM does the reasoning here) ----

EVAL_SYSTEM_PROMPT = """You are a technical recruiter's assistant. You are given:
1. A candidate's resume text
2. A job description
3. Structured data pulled from the candidate's public GitHub repos

Your job: produce evaluation notes that connect claims on the resume to
evidence (or lack of evidence) in the actual GitHub repos, and judge fit
against the job description. Be specific and cite repo names.

Output as JSON with this shape:
{
  "resume_jd_match": "short summary of how resume claims align with JD requirements",
  "github_evidence": [{"repo": "name", "relevance": "why it matters for this JD", "confidence": "high|medium|low"}],
  "gaps": ["things the JD asks for that neither resume nor GitHub clearly show"],
  "overall_notes": "3-5 sentence summary for the recruiter"
}
"""


def evaluate_node(state: EvalState) -> dict:
    jd_text = state.get("jd_text")
    if not jd_text:
        raise ValueError(
            "Missing state['jd_text'] — pass a job description: "
            "app.invoke({'resume_path': ..., 'jd_text': ...})"
        )
    if state.get("github_fetch_error"):
        # distinguish "fetch failed" from "candidate has no repos" so the
        # LLM doesn't treat a rate-limit/token error as a missing portfolio
        repo_summary = (
            "GitHub repo data could not be fetched "
            f"({state['github_fetch_error']}). Evaluate resume/JD only and "
            "note that GitHub evidence was unavailable."
        )
    elif not state.get("repo_profiles"):
        # not fatal — candidate may just have no evaluable public repos —
        # but the LLM should know that explicitly rather than us silently
        # passing it an empty list and hoping it notices
        repo_summary = "No evaluable public repos found for this candidate."
    else:
        repo_summary = json.dumps(
            [
                {
                    "name": p["name"],
                    "description": p["description"],
                    "primary_language": p["primary_language"],
                    "languages": p["languages"],
                    "readme_excerpt": p["readme"],
                    "days_since_last_push": p["days_since_last_push"],
                }
                for p in state["repo_profiles"]
            ],
            indent=2,
        )

    # use the structured resume data, not raw text — cheaper on tokens
    # and the model doesn't have to re-parse messy formatting itself
    resume_summary = json.dumps(state.get("resume_data", {}), indent=2)

    user_prompt = f"""RESUME (structured):
{resume_summary}

JOB DESCRIPTION:
{jd_text}

GITHUB REPO DATA:
{repo_summary}
"""

    client, model = _get_eval_client()
    from llm_client import chat_completion

    response = chat_completion(
        client,
        model,
        messages=[
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = (response.choices[0].message.content or "").strip()

    # Strip ```json fences — some providers add them despite response_format.
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        notes = json.loads(raw)
    except json.JSONDecodeError:
        notes = None
    # don't crash the whole graph over a formatting slip — keep the raw
    # text so nothing is lost, just flag that it wasn't valid JSON.
    # Non-dict JSON (array/scalar) gets the same treatment as bad JSON.
    if not isinstance(notes, dict):
        notes = {"parse_error": True, "raw_output": raw}
    else:
        if not isinstance(notes.get("gaps"), list):
            notes["gaps"] = (
                [str(notes["gaps"])] if notes.get("gaps") is not None else []
            )
        if isinstance(notes.get("github_evidence"), dict):
            notes["github_evidence"] = [notes["github_evidence"]]
        elif not isinstance(notes.get("github_evidence"), list):
            notes["github_evidence"] = []

    if state.get("github_fetch_error"):
        notes["github_fetch_error"] = state["github_fetch_error"]

    return {"notes": notes}


def _load_crew_node():
    from crew_evaluator import crew_evaluate_node

    return crew_evaluate_node


# ---- 4. Wire the graph ----

def build_graph(use_crew: bool = True):
    """
    use_crew=True  -> evaluate step is the 3-agent CrewAI crew
                       (resume analyst + code reviewer + recruiter).
                       Falls back to single-LLM evaluate_node with a warning
                       if crewai isn't installed.
    use_crew=False -> evaluate step is the single evaluate_node LLM call
                       above (cheaper/faster, useful for quick testing)
    """
    import warnings

    graph = StateGraph(EvalState)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("fetch_github", fetch_github_node)

    if use_crew:
        try:
            graph.add_node("evaluate", _load_crew_node())
        except ImportError:
            warnings.warn(
                "crewai not installed — falling back to single-LLM evaluation. "
                "Install with `pip install crewai` to enable the crew path."
            )
            graph.add_node("evaluate", evaluate_node)
    else:
        graph.add_node("evaluate", evaluate_node)

    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "fetch_github")
    graph.add_edge("fetch_github", "evaluate")
    graph.add_edge("evaluate", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    result = app.invoke({
        "resume_path": "/path/to/resume.pdf",
        "jd_text": "Paste job description here...",
        # "username": "override-here",  # only needed if resume has no GitHub link
    })

    print(result["notes"])