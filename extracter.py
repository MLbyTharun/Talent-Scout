
import fitz
from urllib.parse import urlparse
from github_fetcher import get_evaluable_profiles


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


xi=extract_github_links("Tharun.pdf")["repo_apis"]
data = get_evaluable_profiles(xi)
for item in data:
    print(item["name"])