"""
debug_api.py
============
Run this to see the EXACT response structure from the API.
This tells us which key the schemes list is stored under.

Run: python debug_api.py
"""

import requests
import json

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"   # ← paste your key here

url = "https://api.myscheme.gov.in/search/v6/schemes"

headers = {
    "x-api-key":       API_KEY,
    "accept":          "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "origin":          "https://www.myscheme.gov.in",
    "referer":         "https://www.myscheme.gov.in/search",
    "sec-fetch-dest":  "empty",
    "sec-fetch-mode":  "cors",
    "sec-fetch-site":  "same-site",
    "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

params = {
    "keyword": "agriculture",
    "lang":    "en",
    "from":    "0",
    "size":    "2",   # only 2 results — just to see structure
}

print("Sending request...")
r = requests.get(url, headers=headers, params=params, timeout=15)

print(f"Status code : {r.status_code}")
print(f"Response size: {len(r.text)} bytes")
print()

if r.status_code != 200:
    print(f"ERROR — non-200 response:")
    print(r.text[:500])
else:
    data = r.json()

    # Print top-level keys
    print("Top-level keys:", list(data.keys()))
    print()

    # Print full structure (first 2000 chars)
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    print("Full response (first 2000 chars):")
    print(pretty[:2000])
    print()

    # Walk the structure and find lists (these are the schemes arrays)
    print("=" * 50)
    print("LISTS FOUND IN RESPONSE (these are candidates for schemes):")
    print("=" * 50)

    def find_lists(obj, path="root"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                find_lists(v, f"{path}.{k}")
        elif isinstance(obj, list):
            print(f"  {path}  →  list with {len(obj)} items")
            if obj and isinstance(obj[0], dict):
                print(f"    First item keys: {list(obj[0].keys())}")
                # Check if it looks like a scheme
                first = obj[0]
                name = first.get("schemeName") or first.get("title") or first.get("name")
                if name:
                    print(f"    ✅ LOOKS LIKE SCHEMES! First name: '{name}'")

    find_lists(data)
