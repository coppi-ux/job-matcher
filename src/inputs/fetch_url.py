"""Fetch a web page and return its readable text."""
import sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "internship-offer-reader (personal project)"}


def clean_url(url: str) -> str:
    """Remove tracking parameters (utm_*, source) and the #fragment."""
    parts = urlparse(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query)
        if not k.startswith("utm_") and k != "source"
    ]
    return urlunparse(parts._replace(query=urlencode(query), fragment=""))


def fetch_text(url: str) -> str:
    """Download a page and return its text, one non-empty line per row."""
    url = clean_url(url)
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()

    lines = [line.strip()
             for line in soup.get_text(separator="\n").splitlines()]
    return "\n".join(line for line in lines if line)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # avoids errors on Windows
    if len(sys.argv) < 2:
        print('Usage: python src/inputs/fetch_url.py "<url>" [output_file]')
        sys.exit(1)

    text = fetch_text(sys.argv[1])
    print(f"Fetched {len(text)} characters")
    if len(text) < 500:
        print("Warning: very little text. The page may load its content with JavaScript.")

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {sys.argv[2]}")
    else:
        print(text[:3000])
