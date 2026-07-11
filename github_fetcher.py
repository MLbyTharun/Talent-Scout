
import base64
import os
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # personal access token, no special scopes needed
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}


def get_user_repos(username: str, include_forks: bool = False) -> list[dict]:
    """List a user's public repos, most recently pushed first."""
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "pushed", "direction": "desc"},
        )
        resp.raise_for_status() # error check
        batch = resp.json() 
        if not batch: # fi no output
            break
        repos.extend(batch)
        page += 1

    if not include_forks:
        repos = [r for r in repos if not r["fork"]]

    return repos


def get_languages(owner: str, repo: str) -> dict:
    """Bytes of code per language. Useful for tech-stack matching."""
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/languages", headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()


def get_readme(owner: str, repo: str) -> str | None:
    """Decoded README text, or None if there isn't one."""
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/readme", headers=HEADERS
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    content = resp.json()["content"]
    return base64.b64decode(content).decode("utf-8", errors="ignore")


def get_top_level_files(owner: str, repo: str) -> list[str]:
    """Top-level file/folder names — cheap signal for tooling (Dockerfile, requirements.txt, etc.)"""
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/", headers=HEADERS
    )
    if resp.status_code != 200:
        return []
    return [item["name"] for item in resp.json()]


def days_since_last_push(pushed_at: str) -> int:
    pushed = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - pushed).days


def build_repo_profile(username: str, repo_meta: dict) -> dict:
    """Assemble one repo's worth of context for the evaluator agent."""
    owner, name = username, repo_meta["name"]
    return {
        "name": name,
        "description": repo_meta.get("description"),
        "stars": repo_meta.get("stargazers_count", 0),
        "primary_language": repo_meta.get("language"),
        "languages": get_languages(owner, name),
        "readme": get_readme(owner, name),
        "top_level_files": get_top_level_files(owner, name),
        "days_since_last_push": days_since_last_push(repo_meta["pushed_at"]),
        "url": repo_meta["html_url"],
    }