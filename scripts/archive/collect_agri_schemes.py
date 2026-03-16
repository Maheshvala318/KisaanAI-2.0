"""
collect_agri_schemes.py
========================
Phase 1 — Search API   : collects all agriculture scheme slugs
Phase 2 — HTML scrape  : visits each scheme page, extracts visible
                         text directly from the rendered HTML

Install:  pip install requests pandas tqdm beautifulsoup4 lxml
Run:      python collect_agri_schemes.py
Output:   dataset/agri_schemes.csv

Delete dataset/_ckpt.json before running if resuming from scratch.
If interrupted, just re-run — resumes from checkpoint automatically.
"""

import os
import json
import time
import random
import requests
import pandas as pd
from datetime import date
from tqdm import tqdm
from bs4 import BeautifulSoup

# ── API KEY ────────────────────────────────────────────────
API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
# ──────────────────────────────────────────────────────────

API_URL      = "https://api.myscheme.gov.in/search/v6/schemes"
SITE_BASE    = "https://www.myscheme.gov.in/schemes/"
CHECKPOINT   = "dataset/_ckpt.json"

API_HEADERS = {
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

PAGE_HEADERS = {
    "accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

AGRI_CATEGORIES = [
    "Agriculture,Rural & Environment",
    "Animal Husbandry & Dairying",
    "Fisheries",
]

AGRI_KEYWORDS = [
    "agriculture", "farmer", "kisan", "krishi", "crop",
    "irrigation", "horticulture", "livestock", "organic farming",
    "soil health", "fishery", "seed", "farm mechanization",
    "dairy", "pashupalan", "bagwani", "fasal bima",
]

STATES = {
    "GN": "All",
    "GJ": "Gujarat",        "MH": "Maharashtra",   "RJ": "Rajasthan",
    "UP": "Uttar Pradesh",  "HR": "Haryana",        "KA": "Karnataka",
    "TN": "Tamil Nadu",     "AP": "Andhra Pradesh", "MP": "Madhya Pradesh",
    "PB": "Punjab",         "WB": "West Bengal",    "OR": "Odisha",
    "BR": "Bihar",          "TS": "Telangana",
}


# ══════════════════════════════════════════════════════════
#  PHASE 1 — Search API (collect slugs)
# ══════════════════════════════════════════════════════════

def api_fetch_page(session, keyword="", category="", state_name="", from_=0, size=50):
    q = []
    if state_name and state_name != "All":
        q.append({"identifier": "beneficiaryState", "value": state_name})
    if category:
        q.append({"identifier": "schemeCategory", "value": category})

    params = {"lang": "en", "from": str(from_), "size": str(size), "sort": ""}
    if keyword:
        params["keyword"] = keyword
    if q:
        params["q"] = json.dumps(q)

    for attempt in range(3):
        try:
            r = session.get(API_URL, params=params, timeout=15)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 30)))
                continue
            if r.status_code in (401, 403):
                print(f"\n❌ HTTP {r.status_code} — API key expired.")
                return [], 0
            if r.status_code != 200:
                return [], 0

            data  = r.json().get("data", {})
            items = data.get("hits", {}).get("items", [])
            total = data.get("summary", {}).get("total", len(items))

            schemes = []
            for item in items:
                fields = item.get("fields", {})
                if fields:
                    if "schemeId" not in fields:
                        fields["schemeId"] = item.get("id", "")
                    schemes.append(fields)
            return schemes, int(total)

        except requests.Timeout:
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"\n  API error: {e}")
            return [], 0
    return [], 0


def run_phase1(session) -> dict:
    print("=" * 55)
    print("  Phase 1 — Collecting slugs via Search API")
    print("=" * 55)
    all_slugs = {}

    pbar = tqdm(total=len(AGRI_CATEGORIES) * len(STATES), desc="Category × State")
    for cat in AGRI_CATEGORIES:
        for state_name in STATES.values():
            from_ = 0
            while True:
                schemes, total = api_fetch_page(
                    session, category=cat, state_name=state_name, from_=from_
                )
                if not schemes:
                    break
                for s in schemes:
                    slug = s.get("slug") or s.get("schemeShortTitle") or ""
                    name = s.get("schemeName") or s.get("title") or ""
                    state = s.get("beneficiaryState") or state_name
                    if isinstance(state, list):
                        state = state[0] if state else state_name
                    if slug and name:
                        all_slugs[slug] = {
                            "slug": slug, "scheme_name": name.strip(),
                            "state": str(state),
                            "category": str(s.get("schemeCategory") or cat or "Agriculture"),
                            "tags": str(s.get("tags") or ""),
                            "ministry": str(s.get("nodeName") or ""),
                        }
                if from_ + 50 >= total:
                    break
                from_ += 50
                time.sleep(random.uniform(0.3, 0.6))
            pbar.set_postfix({"slugs": len(all_slugs)})
            pbar.update(1)
            time.sleep(random.uniform(0.5, 1.0))
    pbar.close()

    pbar = tqdm(total=len(AGRI_KEYWORDS) * len(STATES), desc="Keyword  × State")
    for kw in AGRI_KEYWORDS:
        for state_name in STATES.values():
            from_ = 0
            while True:
                schemes, total = api_fetch_page(
                    session, keyword=kw, state_name=state_name, from_=from_
                )
                if not schemes:
                    break
                for s in schemes:
                    slug = s.get("slug") or s.get("schemeShortTitle") or ""
                    name = s.get("schemeName") or s.get("title") or ""
                    state = s.get("beneficiaryState") or state_name
                    if isinstance(state, list):
                        state = state[0] if state else state_name
                    if slug and name and slug not in all_slugs:
                        all_slugs[slug] = {
                            "slug": slug, "scheme_name": name.strip(),
                            "state": str(state),
                            "category": str(s.get("schemeCategory") or "Agriculture"),
                            "tags": str(s.get("tags") or ""),
                            "ministry": str(s.get("nodeName") or ""),
                        }
                if from_ + 50 >= total:
                    break
                from_ += 50
                time.sleep(random.uniform(0.3, 0.6))
            pbar.set_postfix({"slugs": len(all_slugs)})
            pbar.update(1)
            time.sleep(random.uniform(0.5, 1.0))
    pbar.close()

    print(f"\n  Phase 1 done — {len(all_slugs)} unique slugs\n")
    return all_slugs


# ══════════════════════════════════════════════════════════
#  PHASE 2 — HTML scraping (extract visible text)
# ══════════════════════════════════════════════════════════

def clean(text: str) -> str:
    """Strip extra whitespace."""
    return " ".join(str(text).split()).strip()


def scrape_scheme_page(session, slug: str) -> dict:
    """
    Fetch the scheme detail page and extract ALL visible text
    from every section: details, benefits, eligibility,
    application process, documents required.

    Strategy: the page renders all tab content in the HTML
    even though it shows only one tab at a time visually.
    BeautifulSoup reads ALL of it at once.
    """
    url = f"{SITE_BASE}{slug}"
    for attempt in range(3):
        try:
            r = session.get(url, headers=PAGE_HEADERS, timeout=20)
            if r.status_code == 404:
                return {}
            if r.status_code == 403:
                time.sleep(random.uniform(5, 10))
                continue
            if r.status_code != 200:
                return {}

            soup = BeautifulSoup(r.text, "lxml")

            # Remove nav, header, footer, scripts, styles — keep only content
            for tag in soup(["script", "style", "nav", "header",
                              "footer", "noscript", "meta", "link"]):
                tag.decompose()

            result = {}

            # ── Strategy 1: find sections by heading text ──────────
            #
            # The page has headings/labels like "Benefits", "Eligibility" etc.
            # We find those and grab the text block that follows them.
            #
            SECTION_LABELS = {
                "scheme_details":      ["Details", "About", "Description",
                                        "Overview", "Scheme Details"],
                "benefits":            ["Benefits", "Benefit", "What You Get",
                                        "Financial Assistance"],
                "eligibility":         ["Eligibility", "Who Can Apply",
                                        "Eligibility Criteria"],
                "application_process": ["Application Process", "How to Apply",
                                        "Apply", "Application"],
                "documents_required":  ["Documents Required", "Documents",
                                        "Required Documents"],
            }

            # Find all headings and labelled divs
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5",
                                      "p", "span", "div", "label", "li"])

            for field, labels in SECTION_LABELS.items():
                if field in result:
                    continue
                for elem in headings:
                    elem_text = clean(elem.get_text())
                    if elem_text in labels or any(
                        lbl.lower() in elem_text.lower() for lbl in labels
                        if len(lbl) > 5
                    ):
                        # Grab the next sibling or parent's next content block
                        content_parts = []

                        # Try next siblings
                        for sib in elem.find_next_siblings():
                            sib_text = clean(sib.get_text(" ", strip=True))
                            # Stop if we hit another section heading
                            if any(lbl.lower() in sib_text.lower()[:50]
                                   for lbl_group in SECTION_LABELS.values()
                                   for lbl in lbl_group
                                   if len(lbl) > 5 and sib_text != elem_text):
                                break
                            if len(sib_text) > 10:
                                content_parts.append(sib_text)
                            if len(" ".join(content_parts)) > 2000:
                                break

                        # Try parent's next sibling if nothing found
                        if not content_parts and elem.parent:
                            for sib in elem.parent.find_next_siblings():
                                sib_text = clean(sib.get_text(" ", strip=True))
                                if len(sib_text) > 10:
                                    content_parts.append(sib_text)
                                if len(" ".join(content_parts)) > 2000:
                                    break

                        if content_parts:
                            result[field] = " | ".join(content_parts[:5])
                            break

            # ── Strategy 2: grab ALL body text as fallback ─────────
            #
            # If strategy 1 found nothing, extract ALL visible text
            # from the page body. This is the nuclear option —
            # you get everything, but at least the data is there.
            #
            body_text = clean(soup.get_text(" ", strip=True))

            if not any(result.values()):
                # Split body by common section keywords and assign
                import re
                sections = re.split(
                    r'(?:Benefits|Eligibility|Application Process|'
                    r'Documents Required|How to Apply)',
                    body_text, flags=re.IGNORECASE
                )
                if len(sections) >= 2:
                    result["scheme_details"]      = clean(sections[0])[-1000:]
                    result["benefits"]            = clean(sections[1])[:1000] if len(sections) > 1 else ""
                    result["eligibility"]         = clean(sections[2])[:1000] if len(sections) > 2 else ""
                    result["application_process"] = clean(sections[3])[:1000] if len(sections) > 3 else ""
                    result["documents_required"]  = clean(sections[4])[:1000] if len(sections) > 4 else ""
                else:
                    # Last resort: store the whole page text
                    result["scheme_details"] = body_text[:3000]

            # Fill any missing fields with empty string
            for field in ["scheme_details", "benefits", "eligibility",
                           "application_process", "documents_required"]:
                result.setdefault(field, "")

            return result

        except requests.Timeout:
            time.sleep(2 ** attempt)
        except Exception as e:
            return {}

    return {}


def run_phase2(all_slugs: dict) -> list:
    print("=" * 55)
    print("  Phase 2 — HTML scraping (visible text extraction)")
    print(f"  Total schemes : {len(all_slugs)}")
    est = len(all_slugs) * 1.5 / 60
    print(f"  Est. time     : {est:.0f}–{est * 1.5:.0f} minutes")
    print("=" * 55)

    done    = load_checkpoint()
    pending = [(s, i) for s, i in all_slugs.items() if s not in done]
    print(f"  Already done: {len(done)}  |  Remaining: {len(pending)}\n")

    page_session = requests.Session()
    rows    = []
    success = 0
    empty   = 0

    for i, (slug, base) in enumerate(tqdm(pending, desc="Scraping pages")):
        detail = scrape_scheme_page(page_session, slug)

        has_data = any(
            len(detail.get(f, "")) > 20
            for f in ["benefits", "eligibility", "scheme_details"]
        )

        row = {
            "scheme_name":         base.get("scheme_name", ""),
            "state":               base.get("state", ""),
            "ministry":            base.get("ministry", ""),
            "category":            base.get("category", "Agriculture"),
            "tags":                base.get("tags", ""),
            "scheme_details":      detail.get("scheme_details", ""),
            "benefits":            detail.get("benefits", ""),
            "eligibility":         detail.get("eligibility", ""),
            "application_process": detail.get("application_process", ""),
            "documents_required":  detail.get("documents_required", ""),
            "url":                 f"{SITE_BASE}{slug}",
            "last_verified":       str(date.today()),
        }
        row["search_text"] = " ".join(filter(None, [
            row["scheme_name"],
            row["scheme_details"][:200],
            row["benefits"][:200],
            row["eligibility"][:200],
            row["state"],
        ]))
        rows.append(row)

        success += 1 if has_data else 0
        empty   += 0 if has_data else 1
        done.add(slug)

        if (i + 1) % 50 == 0:
            save_checkpoint(done)
            pd.DataFrame(rows).fillna("").to_csv(
                "dataset/_partial.csv", index=False, encoding="utf-8"
            )
            tqdm.write(
                f"  Checkpoint @ {i+1}: {success} with data, {empty} empty"
            )

        time.sleep(random.uniform(1.0, 2.0))

    save_checkpoint(done)
    print(f"\n  Phase 2 done — {success} with data, {empty} empty")
    return rows


# ══════════════════════════════════════════════════════════
#  CHECKPOINT
# ══════════════════════════════════════════════════════════

def save_checkpoint(done: set):
    os.makedirs("dataset", exist_ok=True)
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(list(done), f)

def load_checkpoint() -> set:
    if os.path.exists(CHECKPOINT):
        try:
            return set(json.loads(open(CHECKPOINT, encoding="utf-8").read()))
        except Exception:
            pass
    return set()


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    os.makedirs("dataset", exist_ok=True)

    # Phase 1
    api_session = requests.Session()
    api_session.headers.update(API_HEADERS)
    all_slugs = run_phase1(api_session)

    if not all_slugs:
        print("❌ Phase 1 returned 0 slugs — API key may be expired.")
        return

    # Phase 2
    rows = run_phase2(all_slugs)

    # Final CSV
    df = pd.DataFrame(rows)
    df = df[df["scheme_name"].str.strip().str.len() > 5]
    df.drop_duplicates(subset=["scheme_name"], keep="first", inplace=True)
    df.fillna("", inplace=True)
    df.reset_index(drop=True, inplace=True)

    output = "dataset/agri_schemes.csv"
    df.to_csv(output, index=False, encoding="utf-8")

    for f in [CHECKPOINT, "dataset/_partial.csv"]:
        if os.path.exists(f):
            os.remove(f)

    print(f"\n{'='*55}")
    print(f"✅  {len(df)} agriculture schemes → {output}")
    print(f"{'='*55}")
    print(f"  States covered    : {df['state'].nunique()}")
    print(f"  Has description   : {(df['scheme_details'].str.len()>20).sum()}")
    print(f"  Has benefits      : {(df['benefits'].str.len()>10).sum()}")
    print(f"  Has eligibility   : {(df['eligibility'].str.len()>10).sum()}")
    print(f"  Has app_process   : {(df['application_process'].str.len()>10).sum()}")
    print(f"  Has documents     : {(df['documents_required'].str.len()>10).sum()}")

    full = df[df["benefits"].str.len() > 10]
    if not full.empty:
        row = full.iloc[0]
        print(f"\nSample — {row['scheme_name']} [{row['state']}]")
        print(f"  Benefits   : {row['benefits'][:150]}")
        print(f"  Eligibility: {row['eligibility'][:150]}")


if __name__ == "__main__":
    main()
