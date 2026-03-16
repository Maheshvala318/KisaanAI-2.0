"""
test_one_row.py
================
Tests the scraper on the FIRST row of agri_schemes.csv.
Prints every extracted field so you can verify before running on all rows.

Run: python test_one_row.py
"""

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

PAGE_HEADERS = {
    "accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

SECTIONS = [
    ("scheme_details",      ["Details", "About the Scheme", "Overview",
                              "About", "Scheme Details", "Description"]),
    ("benefits",            ["Benefits", "Benefit", "What You Get",
                              "Financial Assistance", "Scheme Benefits"]),
    ("eligibility",         ["Eligibility", "Eligibility Criteria",
                              "Who Can Apply", "Eligibility Conditions"]),
    ("application_process", ["Application Process", "How to Apply",
                              "Application Mode", "Steps to Apply"]),
    ("documents_required",  ["Documents Required", "Required Documents",
                              "Documents Needed", "Documents"]),
]

ALL_HEADINGS = sorted(
    [h for _, heads in SECTIONS for h in heads],
    key=len, reverse=True
)
SPLIT_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(h) for h in ALL_HEADINGS) + r')\b',
    re.IGNORECASE
)


def heading_to_field(heading: str) -> str:
    h = heading.lower().strip()
    if any(x in h for x in ["detail", "about", "overview", "description"]):
        return "scheme_details"
    if any(x in h for x in ["benefit", "financial", "what you get"]):
        return "benefits"
    if any(x in h for x in ["eligib", "who can"]):
        return "eligibility"
    if any(x in h for x in ["application", "how to", "apply", "steps"]):
        return "application_process"
    if any(x in h for x in ["document", "required doc"]):
        return "documents_required"
    return ""


def clean(text: str) -> str:
    return " ".join(str(text).split()).strip()


def scrape(url: str) -> dict:
    result = {f: "" for f, _ in SECTIONS}

    r = requests.get(url, headers=PAGE_HEADERS, timeout=20)
    print(f"HTTP status : {r.status_code}")
    print(f"Page size   : {len(r.text)} bytes\n")

    soup = BeautifulSoup(r.text, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer",
                      "noscript", "meta", "link", "button"]):
        tag.decompose()

    full_text = clean(soup.get_text(" ", strip=True))
    print(f"Cleaned text length: {len(full_text)} chars")
    print(f"Text preview (first 300 chars):\n{full_text[:300]}\n")

    parts = SPLIT_PATTERN.split(full_text)
    print(f"Section headings found: {len(parts)//2}")
    headings_found = [parts[i] for i in range(1, len(parts), 2)]
    print(f"Headings: {headings_found}\n")

    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        content = clean(parts[i + 1]) if i + 1 < len(parts) else ""
        field   = heading_to_field(heading)
        i += 2
        if field and content and len(result[field]) < len(content):
            result[field] = content[:1500]

    if not result["scheme_details"] and parts:
        result["scheme_details"] = clean(parts[0])[:1500]

    return result


# ── Load first row ─────────────────────────────────────
df  = pd.read_csv("dataset/agri_schemes.csv", encoding="utf-8").fillna("")
row = df.iloc[0]

print("=" * 60)
print(f"Testing scheme : {row['scheme_name']}")
print(f"URL            : {row['url']}")
print("=" * 60 + "\n")

fields = scrape(row["url"])

print("=" * 60)
print("EXTRACTED FIELDS:")
print("=" * 60)
for field, value in fields.items():
    print(f"\n[{field}]")
    print(value[:400] if value else "-- EMPTY --")