import requests
import json

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
HEADERS = {
    "x-api-key": API_KEY,
    "origin": "https://www.myscheme.gov.in",
    "accept": "application/json, text/plain, */*",
}

SEARCH_URL = "https://api.myscheme.gov.in/search/v6/schemes"
DETAIL_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes"

def get_valid_slug():
    """Find a valid slug using the Search API."""
    params = {"keyword": "agriculture", "lang": "en", "size": 1}
    r = requests.get(SEARCH_URL, params=params, headers=HEADERS)
    if r.status_code == 200:
        items = r.json().get("data", {}).get("hits", {}).get("items", [])
        if items:
            return items[0].get("fields", {}).get("slug")
    return "pradhan-mantri-kisan-samman-nidhi" # Fallback

def test_exploration(slug):
    """Deep audit of all available fields for Chatbot enrichment."""
    print(f"Auditing: {slug}")
    url = f"{DETAIL_URL}?slug={slug}&lang=en"
    r = requests.get(url, headers=HEADERS, timeout=15)
    
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        return

    full_response = r.json()
    raw_data = full_response.get("data", {})
    data = raw_data.get("en", {})
    
    # Audit Basic Details
    bd = data.get("basicDetails", {})
    print("\n--- Basic Details Audit ---")
    for k, v in bd.items():
        print(f"  {k}: {v}")

    # Audit Scheme Content
    sc = data.get("schemeContent", {})
    print("\n--- Scheme Content Audit ---")
    for k, v in sc.items():
        val_preview = str(v)[:100] + "..." if len(str(v)) > 100 else v
        print(f"  {k}: {val_preview}")

    # Look for metadata / tags / rules
    print("\n--- Metadata & Rules Audit ---")
    for k in ["tags", "targetAudience", "financialAssistance", "rules"]:
        val = data.get(k)
        if val:
            print(f"  {k}: {val}")
        else:
            print(f"  {k}: [EMPTY]")

    # Check for state codes or IDs
    if not bd.get("stateName"):
        print("\nChecking for alternate state fields...")
        state_id = bd.get("state")
        if state_id:
            print(f"  Found 'state' ID: {state_id}")

    # Look for other top-level keys in 'en'
    print("\n--- Other 'en' Keys ---")
    for k in data.keys():
        if k not in ["basicDetails", "schemeContent", "tags", "targetAudience", "financialAssistance", "rules"]:
             print(f"  {k}: {type(data[k])}")

def test_extraction(slug):
    """Fetch and extract COMPLETE fields for Chatbot evaluation."""
    print(f"Target Slug: {slug}")
    url = f"{DETAIL_URL}?slug={slug}&lang=en"
    r = requests.get(url, headers=HEADERS, timeout=15)
    
    if r.status_code != 200:
        print(f"Error fetching detail: {r.status_code}")
        return

    raw_data = r.json().get("data")
    if not raw_data:
        print("No 'data' object found in API response.")
        return
        
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
    
    # Enrichment
    state_obj = bd.get("state")
    state_name = bd.get("stateName") or (state_obj.get("label") if isinstance(state_obj, dict) else None)
    
    beneficiaries = [b.get("label") for b in bd.get("targetBeneficiaries", []) if isinstance(b, dict)]
    nodal_dept = bd.get("nodalDepartmentName", {}).get("label") if isinstance(bd.get("nodalDepartmentName"), dict) else None
    benefit_type = sc.get("benefitTypes", {}).get("label") if isinstance(sc.get("benefitTypes"), dict) else None
    
    extracted = {
        "slug": slug,
        "scheme_name": bd.get("schemeName"),
        "state": state_name,
        "implementing_agency": bd.get("implementingAgency"),
        "nodal_department": nodal_dept,
        "benefit_type": benefit_type,
        "target_beneficiaries": beneficiaries,
        "tags": bd.get("tags", []),
        "category": [c.get("label") for c in bd.get("schemeCategory", []) if isinstance(c, dict)],
        "details": sc.get("detailedDescription_md"),
        "benefits": sc.get("benefits_md"),
        "eligibility": ec.get("eligibilityDescription_md"),
        "application_process": application_process,
        "references": sc.get("references", []),
        "url": f"https://www.myscheme.gov.in/schemes/{slug}",
        "api_id": scheme_id
    }

    output_file = "scripts/extracted_scheme.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2)
    
    print(f"COMPLETE extracted data saved to: {output_file}")

if __name__ == "__main__":
    slug = get_valid_slug()
    # test_exploration(slug)
    test_extraction("satgmsa") # Analyze the one the user pointed out
