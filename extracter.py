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

x = github_repos("Tharun.pdf")
y = github_to_api(x)
print(y)