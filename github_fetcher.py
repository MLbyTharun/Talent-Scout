import os
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}