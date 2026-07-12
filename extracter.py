from pypdf import PdfReader
import pandas as pd
import fitz
from urllib.parse import urlparse

# Extracts text from candidate and job descrptn
def txt_extract(file):
    pdf = PdfReader(file)
    for page in pdf.pages:
        txt = page.extract_text() or ""
    
    return txt


# Links Extracter

def github_repos(file):
    doc = fitz.open(file)

    all_links = []
    repos = []
    for page in doc:
        links = page.get_links()

        for link in links:
            if "uri" in link:
                all_links.append(link["uri"])
            
    for uri in all_links:
        parsed = urlparse(uri)
        
        if parsed.netloc.lower() not in ["github.com","www.github.com"]:
            continue

        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2:
            repos.append(uri)
        
    return repos

def github_to_api(urls):
    apis = []
    for url in urls:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 1:
            apis.append(f"https:api.github.com/users/{parts[0]}")
        elif len(parts) >= 2:
            apis.append(f"https://api.github.com/repos/{parts[0]}/{parts[1]}")
    
    return apis

#-----------------------------------------------------------------------------------------------

import base64
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # personal access token, no special scopes needed
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github+json",
}

def all(file):
    
    x = github_repos(file)
    y = github_to_api(x)
    
    return y

def get_languages(owner: str, repo: str) -> dict:
    """Bytes of code per language. Useful for tech-stack matching."""
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/languages", headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()

def get_lang(api):
    resp = requests.get(api,headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

print(get_lang('https://api.github.com/repos/MLbyTharun/Startup-Research-Agent/contents/'))