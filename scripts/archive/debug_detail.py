"""
debug_detail.py
================
Prints the EXACT __NEXT_DATA__ structure from one scheme detail page.
Run this to find the correct field names for benefits, eligibility etc.

Run: python debug_detail.py
"""

import requests
import json
import re

PAGE_HEADERS = {
    "accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Using pm-kisan — one of the most well-known schemes
TEST_URL = "https://www.myscheme.gov.in/schemes/pm-kisan"

print(f"Fetching: {TEST_URL}\n")
r = requests.get(TEST_URL, headers=PAGE_HEADERS, timeout=20)
print(f"Status: {r.status_code}")
print(f"Page size: {len(r.text)} bytes\n")

# Extract __NEXT_DATA__
match = re.search(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    r.text, re.DOTALL
)

if not match:
    print("❌ __NEXT_DATA__ tag NOT FOUND in page")
    print("First 2000 chars of HTML:")
    print(r.text[:2000])
else:
    print("✅ __NEXT_DATA__ found\n")
    nd = json.loads(match.group(1))

    # Print ALL keys at every level to find where data lives
    def print_structure(obj, path="", depth=0):
        if depth > 5:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_path = f"{path}.{k}" if path else k
                if isinstance(v, dict):
                    print(f"{'  '*depth}[dict]  {full_path}  → keys: {list(v.keys())[:8]}")
                    print_structure(v, full_path, depth+1)
                elif isinstance(v, list):
                    print(f"{'  '*depth}[list]  {full_path}  → {len(v)} items", end="")
                    if v and isinstance(v[0], dict):
                        print(f"  first item keys: {list(v[0].keys())[:6]}")
                        if depth < 3:
                            print_structure(v[0], full_path+"[0]", depth+1)
                    else:
                        val = str(v)[:80]
                        print(f"  value: {val}")
                else:
                    val = str(v)[:100] if v else "None"
                    print(f"{'  '*depth}[val]   {full_path}  = {val}")

    print("=" * 60)
    print("FULL __NEXT_DATA__ STRUCTURE:")
    print("=" * 60)
    print_structure(nd)

    # Also print the raw props.pageProps to see it clearly
    pp = nd.get("props", {}).get("pageProps", {})
    print("\n" + "=" * 60)
    print("props.pageProps keys:", list(pp.keys()))
    print("=" * 60)

    # Find the scheme object
    for key in ["schemeData", "scheme", "data"]:
        if key in pp:
            scheme = pp[key]
            print(f"\nFound scheme at pageProps.{key}")
            print(f"Scheme keys: {list(scheme.keys()) if isinstance(scheme, dict) else type(scheme)}")
            if isinstance(scheme, dict):
                print("\nAll scheme fields with values:")
                for k, v in scheme.items():
                    val = str(v)[:150] if v else "None/Empty"
                    print(f"  [{k}] = {val}")
            break
