import os
import requests
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}

def get_user_repo(username :str, include_forks : bool = False)->list[dict]:
    repos = []
    page = 1

    while True:
        resp = requests.get(
            f"https://api/github.com/users/{username}/repos",
            headers = HEADERS,
            params = {"per_page" : 100,"page":1, "sort":"pushed","direction":"desc",}
            )
        resp.raise_for_status() # err check
        batch = resp.json()

        if not batch:  # breaks if no outptu
            break
        repos.extend(batch)
        page += 1

    if not include_forks: # else alll
        repos =  [r for r in repos if not r["fork"]]
        
    return repos
    
r = get_user_repo("MLbyTharun")
print(r)