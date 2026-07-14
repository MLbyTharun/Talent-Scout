"""
GitHub repo data fetcher — pulls just enough signal per repo for an LLM
to evaluate it against a job description, without cloning anything.

No repo listing/discovery here — that already happened upstream, in
resume_parser.py's extract_github_links(), which converts resume links
directly into GitHub API urls. This module just takes those urls and
fetches what's needed. Sequential on purpose: with only a handful of
resume-linked repos to fetch (not a broad sweep of everything a user has),
parallelizing isn't worth the extra complexity.
"""

import base64
import os
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # personal access token, no special scopes needed
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}


def get_repo_metadata(api_url: str) -> dict:
    """Full repo metadata in one call — name, description, stars, language,
    pushed_at, html_url all come back from GET on the repo's own API url."""
    resp = requests.get(api_url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_languages(api_url: str) -> dict:
    """Bytes of code per language. Useful for tech-stack matching."""
    resp = requests.get(api_url.rstrip("/") + "/languages", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_readme(api_url: str) -> str | None:
    """Decoded README text, or None if there isn't one."""
    resp = requests.get(api_url.rstrip("/") + "/readme", headers=HEADERS)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    content = resp.json()["content"]
    return base64.b64decode(content).decode("utf-8", errors="ignore")


def get_top_level_files(api_url: str) -> list[str]:
    """Top-level file/folder names — cheap signal for tooling (Dockerfile, requirements.txt, etc.)"""
    resp = requests.get(api_url.rstrip("/") + "/contents/", headers=HEADERS)
    if resp.status_code != 200:
        return []
    return [item["name"] for item in resp.json()]


def days_since_last_push(pushed_at: str) -> int:
    pushed = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - pushed).days


def build_repo_profile(api_url: str) -> dict:
    """Assemble one repo's worth of context for the evaluator agent,
    starting from nothing but its direct API url."""
    meta = get_repo_metadata(api_url)
    return {
        "name": meta["name"],
        "description": meta.get("description"),
        "stars": meta.get("stargazers_count", 0),
        "primary_language": meta.get("language"),
        "languages": get_languages(api_url),
        "readme": get_readme(api_url),
        "top_level_files": get_top_level_files(api_url),
        "days_since_last_push": days_since_last_push(meta["pushed_at"]),
        "url": meta["html_url"],
    }


def get_evaluable_profiles(apis: list[str], max_repos: int = 15, skip_stale_after_days: int = 730) -> list[dict]:
    """
    apis: direct GitHub API urls to specific repos, e.g.
        ["https://api.github.com/repos/owner/repo1", ...]
    — already resolved from the resume (extract_github_links -> repo_apis).
    No listing call needed: we already know exactly which repos to fetch.
    """
    profiles = []
    for api_url in apis[:max_repos]:
        try:
            profile = build_repo_profile(api_url)
        except requests.HTTPError:
            continue  # bad/deleted/renamed repo — skip rather than crash the batch

        if profile["days_since_last_push"] > skip_stale_after_days:
            continue
        if profile["readme"] is None and not profile["description"]:
            continue  # nothing to evaluate on, skip

        profiles.append(profile)

    return profiles


if __name__ == "__main__":
    import json
    import sys

    apis = sys.argv[1:] or ["https://api.github.com/repos/MLbyTharun/HR-Knowledge-Assistant"]
    profiles = get_evaluable_profiles(apis)
    print(json.dumps(profiles, indent=2))