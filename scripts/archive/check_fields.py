"""
check_fields.py
================
Shows the EXACT field names inside data.hits.items[].fields
so we can fix the parse() function to extract all data correctly.

Run: python check_fields.py
"""

import requests
import json

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"   # ← paste your key

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

params = {"keyword": "agriculture", "lang": "en", "from": "0", "size": "1"}

r = requests.get(url, headers=headers, params=params, timeout=15)
print(f"Status: {r.status_code}\n")

data   = r.json()
items  = data.get("data", {}).get("hits", {}).get("items", [])

if not items:
    print("No items found")
else:
    item   = items[0]
    fields = item.get("fields", {})

    print("=" * 60)
    print("ALL FIELD NAMES AND VALUES (first scheme):")
    print("=" * 60)
    for key, value in fields.items():
        # Truncate long values for readability
        val_str = str(value)
        if len(val_str) > 120:
            val_str = val_str[:120] + "..."
        print(f"\n  [{key}]")
        print(f"  {val_str}")
