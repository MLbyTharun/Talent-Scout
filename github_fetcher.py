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
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # personal access token, no special scopes needed
HEADERS = {
    "Accept": "application/vnd.github+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

REQUEST_TIMEOUT = 15
ALLOWED_API_HOST = "api.github.com"


def _validate_api_url(api_url: str) -> str:
    """Refuse anything that isn't a plain https GitHub API repo URL.

    Defense in depth: URLs are built internally today, but this module
    must never send the token to another host or follow path traversal
    (e.g. /repos/../...) if a future caller passes resume-derived input.
    """
    parsed = urlparse(str(api_url))
    if parsed.scheme != "https" or parsed.netloc.lower() != ALLOWED_API_HOST:
        raise ValueError(f"refusing non-GitHub API URL: {api_url!r}")
    if ".." in parsed.path.split("/"):
        raise ValueError(f"refusing path traversal in URL: {api_url!r}")
    if parsed.query or parsed.fragment:
        raise ValueError(f"refusing URL with query/fragment: {api_url!r}")
    return api_url


def get_repo_metadata(api_url: str) -> dict:
    """Full repo metadata in one call — name, description, stars, language,
    pushed_at, html_url all come back from GET on the repo's own API url."""
    resp = requests.get(_validate_api_url(api_url), headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_languages(api_url: str) -> dict:
    """Bytes of code per language. Useful for tech-stack matching."""
    resp = requests.get(
        _validate_api_url(api_url).rstrip("/") + "/languages",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}


def get_readme(api_url: str) -> str | None:
    """Decoded README text, or None if there isn't one."""
    resp = requests.get(
        _validate_api_url(api_url).rstrip("/") + "/readme",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    try:
        content = resp.json().get("content")
    except ValueError:
        return None
    if not content:
        return None
    try:
        return base64.b64decode(content).decode("utf-8", errors="ignore")
    except (ValueError, base64.binascii.Error):
        return None


def get_top_level_files(api_url: str) -> list[str]:
    """Top-level file/folder names — cheap signal for tooling (Dockerfile, requirements.txt, etc.)"""
    resp = requests.get(
        _validate_api_url(api_url).rstrip("/") + "/contents/",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError:
        return []
    if isinstance(data, dict):
        # error payload (e.g. empty repo, rate limit) — not a file listing
        return []
    return [item.get("name", "") for item in data if isinstance(item, dict) and "name" in item]


def days_since_last_push(pushed_at: str | None) -> int:
    if not pushed_at:
        return 10**9  # unknown — treat as very stale so it gets filtered
    try:
        # GitHub returns "2024-01-02T15:04:05Z"; fromisoformat needs +00:00
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        if pushed.tzinfo is None:
            pushed = pushed.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            pushed = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return 10**9
    return max(0, (datetime.now(timezone.utc) - pushed).days)


def build_repo_profile(api_url: str) -> dict:
    """Assemble one repo's worth of context for the evaluator agent,
    starting from nothing but its direct API url."""
    meta = get_repo_metadata(api_url)
    if not isinstance(meta, dict) or "name" not in meta:
        raise ValueError(f"unexpected GitHub response for {api_url}: {str(meta)[:200]}")
    return {
        "name": meta["name"],
        "description": meta.get("description"),
        "stars": meta.get("stargazers_count", 0),
        "primary_language": meta.get("language"),
        "languages": get_languages(api_url),
        "readme": get_readme(api_url),
        "top_level_files": get_top_level_files(api_url),
        "days_since_last_push": days_since_last_push(meta.get("pushed_at")),
        "url": meta.get("html_url"),
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
            _validate_api_url(api_url)
            profile = build_repo_profile(api_url)
        except requests.HTTPError as e:
            # 404 (deleted/renamed) -> skip; 401/403/429 (bad token, rate
            # limit) -> fail fast so a misconfigured token or exhausted
            # quota surfaces as github_fetch_error instead of silently
            # looking like "no repos".
            status = e.response.status_code if e.response is not None else None
            if status in (401, 403, 429):
                raise
            continue  # bad/deleted/renamed repo — skip rather than crash the batch
        except (ValueError, KeyError, AttributeError):
            continue

        if profile["days_since_last_push"] > skip_stale_after_days:
            continue
        if profile["readme"] is None and not profile["description"]:
            continue  # nothing to evaluate on, skip

        profiles.append(profile)

    return profiles
