"""
collect_agri_schemes_v2.py
===========================
Uses myScheme v6 public API to fetch detailed agricultural schemes.
Phase 1: Search API (15 States x Categories/Keywords) -> Collect Slugs
Phase 2: Detail API -> Fetch full markdown content (benefits, eligibility, etc.)

Reliably fetches 1000+ schemes without "Something went wrong" errors.
Includes a checkpoint system to resume if interrupted.

Output: dataset/agri_schemes_full.csv
"""

import os
import json
import time
import random
import requests
import pandas as pd
from datetime import date
from tqdm import tqdm

# ── API CONFIG ─────────────────────────────────────────────
API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
HEADERS = {
    "x-api-key": API_KEY,
    "origin": "https://www.myscheme.gov.in",
    "accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_URL = "https://api.myscheme.gov.in/search/v6/schemes"
DETAIL_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes"
CHECKPOINT_SLUGS = "dataset/_slugs_ckpt.json"
CHECKPOINT_DATA = "dataset/_data_ckpt.json"

# MATCHING ORIGINAL SCRIPT PARAMS
STATES = {
    "GN": "All",
    "GJ": "Gujarat",        "MH": "Maharashtra",   "RJ": "Rajasthan",
    "UP": "Uttar Pradesh",  "HR": "Haryana",        "KA": "Karnataka",
    "TN": "Tamil Nadu",     "AP": "Andhra Pradesh", "MP": "Madhya Pradesh",
    "PB": "Punjab",         "WB": "West Bengal",    "OR": "Odisha",
    "BR": "Bihar",          "TS": "Telangana",
}

AGRI_CATEGORIES = [
    "Agriculture,Rural & Environment",
    "Animal Husbandry & Dairying",
    "Fisheries",
]

KEYWORDS = [
    "agriculture", "farmer", "kisan", "krishi", "crop",
    "irrigation", "horticulture", "livestock", "organic farming",
    "soil health", "fishery", "seed", "farm mechanization",
    "dairy", "pashupalan", "bagwani", "fasal bima",
]

def fetch_search_page(session, keyword="", category="", state_name="", from_idx=0):
    """Fetch one page of search results."""
    q = []
    if state_name and state_name != "All":
        q.append({"identifier": "beneficiaryState", "value": state_name})
    if category:
        q.append({"identifier": "schemeCategory", "value": category})

    params = {
        "lang": "en",
        "from": from_idx,
        "size": 50,
    }
    if keyword:
        params["keyword"] = keyword
    if q:
        params["q"] = json.dumps(q)

    try:
        r = session.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", {})
            items = data.get("hits", {}).get("items", [])
            total = data.get("summary", {}).get("total", len(items))
            return items, total
    except Exception as e:
        print(f"  Search error: {e}")
    return [], 0

def fetch_details(slug):
    """Fetch full details for a scheme using the Detail API."""
    try:
        url = f"{DETAIL_URL}?slug={slug}&lang=en"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        
        raw_data = r.json().get("data", {})
        data = raw_data.get("en", {})
        scheme_id = raw_data.get("_id")
        
        bd = data.get("basicDetails", {})
        sc = data.get("schemeContent", {})
        ec = data.get("eligibilityCriteria", {})
        ap_list = data.get("applicationProcess", [])
        
        # Process management
        application_process = ""
        if isinstance(ap_list, list):
             application_process = "\n\n".join([str(item.get("process_md") or "") for item in ap_list if item.get("process_md")])
        
        # Enrichment & Defensive Filtering
        state_obj = bd.get("state")
        state_name = bd.get("stateName") or (state_obj.get("label") if isinstance(state_obj, dict) else None)
        
        beneficiaries_raw = bd.get("targetBeneficiaries") or []
        beneficiaries = [b.get("label") for b in beneficiaries_raw 
                        if isinstance(b, dict) and b.get("label")]
        
        nodal_dept = bd.get("nodalDepartmentName", {}).get("label") if isinstance(bd.get("nodalDepartmentName"), dict) else None
        benefit_type = sc.get("benefitTypes", {}).get("label") if isinstance(sc.get("benefitTypes"), dict) else None
        
        tags_raw = bd.get("tags") or []
        tags_list = [t for t in tags_raw if isinstance(t, str) and t]
        
        cats_raw = bd.get("schemeCategory") or []
        cat_list = [c.get("label") for c in cats_raw 
                   if isinstance(c, dict) and c.get("label")]
        
        # Fetch documents if ID is available
        docs_text = ""
        if scheme_id:
            try:
                docs_url = f"https://api.myscheme.gov.in/schemes/v6/public/schemes/{scheme_id}/documents?lang=en"
                dr = requests.get(docs_url, headers=HEADERS, timeout=10)
                if dr.status_code == 200:
                    docs_data = dr.json()
                    if isinstance(docs_data, list):
                        docs_text = "\n".join([f"- {str(d.get('documentName') or '')}" for d in docs_data if d.get('documentName')])
            except:
                pass

        return {
            "slug": slug,
            "scheme_name": bd.get("schemeName"),
            "state": state_name,
            "implementing_agency": bd.get("implementingAgency"),
            "nodal_department": nodal_dept,
            "benefit_type": benefit_type,
            "target_beneficiaries": "|".join(beneficiaries),
            "tags": "|".join(tags_list),
            "category": "|".join(cat_list),
            "scheme_details": sc.get("detailedDescription_md"),
            "benefits": sc.get("benefits_md"),
            "eligibility": ec.get("eligibilityDescription_md"),
            "application_process": application_process,
            "documents": docs_text,
            "url": f"https://www.myscheme.gov.in/schemes/{slug}",
            "last_verified": str(date.today()),
            "api_id": scheme_id
        }
    except Exception as e:
        print(f"Error fetching detail for {slug}: {e}")
        return None

def main():
    os.makedirs("dataset", exist_ok=True)
    session = requests.Session()
    
    # ── PHASE 1: SLUG COLLECTION ───────────────────────────
    all_slugs_data = {}
    if os.path.exists(CHECKPOINT_SLUGS):
        with open(CHECKPOINT_SLUGS, "r") as f:
            all_slugs_data = json.load(f)
        print(f"Phase 1: {len(all_slugs_data)} slugs loaded from checkpoint.")
    else:
        print("Step 1: Collecting slugs from Search API (Cat pass + Kw pass)...")
        # Categories
        pbar = tqdm(total=len(AGRI_CATEGORIES) * len(STATES), desc="Categories")
        for cat in AGRI_CATEGORIES:
            for state_name in STATES.values():
                from_idx = 0
                while True:
                    items, total = fetch_search_page(session, category=cat, state_name=state_name, from_idx=from_idx)
                    if not items: break
                    for item in items:
                        slug = item.get("fields", {}).get("slug")
                        if slug and slug not in all_slugs_data:
                            all_slugs_data[slug] = item.get("fields", {}).get("schemeName")
                    if from_idx + 50 >= total: break
                    from_idx += 50
                    time.sleep(0.3)
                pbar.update(1)
        pbar.close()

        # Keywords
        pbar = tqdm(total=len(KEYWORDS) * len(STATES), desc="Keywords")
        for kw in KEYWORDS:
            for state_name in STATES.values():
                from_idx = 0
                while True:
                    items, total = fetch_search_page(session, keyword=kw, state_name=state_name, from_idx=from_idx)
                    if not items: break
                    for item in items:
                        slug = item.get("fields", {}).get("slug")
                        if slug and slug not in all_slugs_data:
                            all_slugs_data[slug] = item.get("fields", {}).get("schemeName")
                    if from_idx + 50 >= total: break
                    from_idx += 50
                    time.sleep(0.3)
                pbar.update(1)
        pbar.close()
        
        with open(CHECKPOINT_SLUGS, "w") as f:
             json.dump(all_slugs_data, f)
        print(f"Step 1 Complete: {len(all_slugs_data)} unique slugs found.")

    # ── PHASE 2: DETAIL EXTRACTION ─────────────────────────
    all_data = []
    if os.path.exists(CHECKPOINT_DATA):
        try:
            with open(CHECKPOINT_DATA, "r") as f:
                all_data = json.load(f)
        except:
            pass
    
    done_slugs = {d["slug"] for d in all_data if "slug" in d}
    pending_slugs = [s for s in all_slugs_data.keys() if s not in done_slugs]
    
    if pending_slugs:
        print(f"\nStep 2: Fetching full details ({len(pending_slugs)} schemes remaining)...")
        for i, slug in enumerate(tqdm(pending_slugs)):
            detail = fetch_details(slug)
            if detail:
                all_data.append(detail)
            
            # Save checkpoint every 20 items
            if (i + 1) % 20 == 0:
                with open(CHECKPOINT_DATA, "w") as f:
                    json.dump(all_data, f)
            
            time.sleep(random.uniform(0.5, 1.2))

    # ── FINAL SAVE ─────────────────────────────────────────
    if all_data:
        df = pd.DataFrame(all_data)
        # Combine text for RAG
        df["search_text"] = df["scheme_name"].fillna("") + " " + \
                            df["scheme_details"].fillna("").str[:400] + " " + \
                            df["benefits"].fillna("").str[:400]
        
        output_path = "dataset/agri_schemes_full.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"\n✅ SUCCESS: Finalized {len(df)} detailed schemes in {output_path}")
        
        # Cleanup checkpoints
        # for f in [CHECKPOINT_SLUGS, CHECKPOINT_DATA]:
        #     if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    main()
