import requests
import pandas as pd
import time
import json
from datetime import date
import os

# All Indian state codes for the API
STATES = {
    "GJ": "Gujarat",
}

AGRICULTURE_KEYWORDS = [
    "farmer", "agriculture", "krishi", "kisan", "crop",
    "irrigation", "soil", "horticulture", "fishery", "livestock"
]

def fetch_schemes_by_state(state_code: str) -> list:
    """
    Fetch all agriculture schemes for a state from api.myscheme.gov.in
    Using v6 API with required headers and API key.
    """
    all_schemes = []
    headers = {
        'x-api-key': 'tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc',
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://www.myscheme.gov.in',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for keyword in AGRICULTURE_KEYWORDS:
        # v6 endpoint
        url = "https://api.myscheme.gov.in/search/v6/schemes"
        
        # Format the JSON q parameter as discovered in research
        # q=[{"identifier":"beneficiaryState","value":"All"},{"identifier":"beneficiaryState","value":"Gujarat"}]
        q_filter = [
            {"identifier": "beneficiaryState", "value": "All"},
            {"identifier": "beneficiaryState", "value": state_code} # Use full state name if code doesn't work, but let's try mapping
        ]
        
        # The API expects full name in the value field based on research
        state_name = STATES.get(state_code, state_code)
        q_filter[1]["value"] = state_name

        params = {
            "keyword": keyword,
            "lang": "en",
            "from": 0,
            "size": 50,
            "q": json.dumps(q_filter),
            "sort": ""
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                schemes = data.get("data", {}).get("schemes", [])
                all_schemes.extend(schemes)
                print(f"  [SUCCESS] {state_name} + '{keyword}': {len(schemes)} schemes")
            else:
                print(f"  [ERROR] {state_name} + '{keyword}': Status {resp.status_code}")
                if resp.status_code != 200:
                    print(f"  [DEBUG] Response: {resp.text[:100]}")
        except Exception as e:
            print(f"  [FAILED] {state_name}/{keyword}: {e}")
        time.sleep(1.0) 
    
    return all_schemes

def parse_scheme(raw: dict, state_name: str) -> dict:
    """
    Extract and flatten fields from the API response.
    """
    return {
        "scheme_id":           raw.get("schemeId", ""),
        "scheme_name":         raw.get("schemeName", raw.get("title", "")),
        "state":               state_name,
        "ministry":            raw.get("nodeName", raw.get("ministry", "")),
        "category":            raw.get("tag", ""),
        "scheme_details":      raw.get("schemeShortTitle", raw.get("description", "")),
        "benefits":            raw.get("benefit", ""),
        "eligibility":         raw.get("eligibility", ""),
        "application_process": raw.get("applicationProcess", ""),
        "documents_required":  json.dumps(raw.get("documents", [])),
        "url":                 raw.get("schemeUrl", raw.get("url", "")),
        "is_active":           True,
        "last_verified":       str(date.today()),
        # Combined field for FAISS embedding
        "search_text": " ".join(filter(None, [
            raw.get("schemeName", ""),
            raw.get("schemeShortTitle", ""),
            raw.get("benefit", ""),
            raw.get("eligibility", ""),
            state_name
        ]))
    }

def build_scheme_dataset():
    all_rows = []
    seen_ids = set()
    
    # Ensure dataset directory exists
    if not os.path.exists("dataset"):
        os.makedirs("dataset")

    for state_code, state_name in STATES.items():
        print(f"\nFetching schemes for {state_name}...")
        schemes = fetch_schemes_by_state(state_code)
        
        for raw in schemes:
            sid = raw.get("schemeId", raw.get("title", ""))
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                all_rows.append(parse_scheme(raw, state_name))
    
    if not all_rows:
        print("No schemes found. Check your Internet connection or API status.")
        return

    df = pd.DataFrame(all_rows)
    df = df[df["scheme_name"].str.len() > 5]  # Remove empty/junk rows
    df.drop_duplicates(subset=["scheme_name", "state"], inplace=True)
    
    output_path = "dataset/schemes_india.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✅ Saved {len(df)} unique schemes to {output_path}")
    return df

if __name__ == "__main__":
    df = build_scheme_dataset()
    if df is not None:
        print("\n--- DATA SAMPLE ---")
        print(df[["scheme_name", "state"]].head(10))
