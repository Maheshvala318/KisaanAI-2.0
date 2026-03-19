"""
NIPHM IPM PDF Downloader
=========================
Downloads all 87 crop IPM (Integrated Pest Management) PDF packages from
the National Institute of Plant Health Management (NIPHM), Government of India.

Source: http://niphm.gov.in/IPMPackages/
Output: dataset/niphm_pdfs/{CropName}.pdf

Usage:
    python scripts/download_niphm_pdfs.py
"""

import os
import sys
import time
import requests
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────
BASE_URL = "http://niphm.gov.in/IPMPackages/"
PDF_DIR = Path(__file__).resolve().parent.parent / "dataset" / "niphm_pdfs"
DELAY = 0.5  # seconds between downloads (be respectful)
MIN_FILE_SIZE = 5000  # bytes — skip corrupt/empty files
TIMEOUT = 60  # seconds per download

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ── All 87 PDFs: {local_name: remote_filename} ─────────────────
ALL_PDFS = {
    # ═══ Cereals & Millets (5) ═══
    "Rice":              "Rice.pdf",
    "Wheat":             "Wheat.pdf",
    "Maize":             "Maize.pdf",
    "Sorghum":           "Sorghum.pdf",
    "Pearl_Millet":      "Pearlmillet.pdf",

    # ═══ Cash Crops (8) ═══
    "Cotton":            "Cotton.pdf",
    "Sugarcane":         "Sugarcane.pdf",
    "Sunflower":         "Sunflower.pdf",
    "Safflower":         "Safflower.pdf",
    "Sesame":            "Sesame.pdf",
    "Castor":            "Castor.pdf",
    "Tobacco":           "Tobacco.pdf",
    "Oil_Palm":          "Oilpalm.pdf",

    # ═══ Pulses (11) ═══
    "Chickpea":          "Chickpea.pdf",
    "Red_Gram":          "Redgram.pdf",
    "Blackgram_Greengram": "BlackgramandGreengram.pdf",
    "Lentil":            "Lentil.pdf",
    "Soybean":           "Soyabean.pdf",
    "Pea":               "Pea.pdf",
    "Horse_Gram":        "Horsegram.pdf",
    "Moth_Bean":         "Mothbean.pdf",
    "Rajmah":            "Rajmah.pdf",
    "Lablab_Bean":       "Lablabbean.pdf",
    "Leguminous_Vegetables": "Leguminousvegetables.pdf",

    # ═══ Oilseeds (2) ═══
    "Groundnut":         "Groundnut.pdf",
    "Mustard":           "Mustard.pdf",

    # ═══ Vegetables (12) ═══
    "Tomato":            "Tomato.pdf",
    "Potato":            "Potato.pdf",
    "Onion":             "Onion.pdf",
    "Brinjal":           "Brinjal.pdf",
    "Chilli":            "Chilli.pdf",
    "Okra":              "Okra.pdf",
    "Cabbage_Cauliflower": "CabbageandCauliflower.pdf",
    "Broccoli":          "Broccoli.pdf",
    "Cucurbits":         "CucurbitaceousVegetable.pdf",
    "Spinach":           "Spinach.pdf",
    "Drumstick":         "Drumstick.pdf",
    "Tapioca":           "Tapioca.pdf",

    # ═══ Fruits (31) ═══
    "Mango":             "Mango.pdf",
    "Banana":            "Banana.pdf",
    "Guava":             "Guava.pdf",
    "Papaya":            "Papaya.pdf",
    "Grapes":            "Grapes.pdf",
    "Pomegranate":       "Pomegranate.pdf",
    "Citrus":            "Citrus.pdf",
    "Coconut":           "Coconut.pdf",
    "Cashew":            "Cashew.pdf",
    "Litchi":            "Litchi.pdf",
    "Pineapple":         "Pineapple.pdf",
    "Amla":              "Amla.pdf",
    "Sapota":            "Sapota.pdf",
    "Fig":               "Fig.pdf",
    "Jackfruit":         "Jackfruit.pdf",
    "Watermelon":        "Watermelon.pdf",
    "Apple":             "Apple.pdf",
    "Strawberry":        "Strawberry.pdf",
    "Apricot":           "Apricot.pdf",
    "Peach":             "Peach.pdf",
    "Pear":              "Pear.pdf",
    "Cherry":            "Cherry.pdf",
    "Kiwi":              "Kiwi.pdf",
    "Walnut":            "Walnut.pdf",
    "Raspberry":         "Raspberry.pdf",
    "Loquat":            "Loquat.pdf",
    "Persimmon":         "Persimmon.pdf",
    "Phalsa":            "Phalsa.pdf",
    "Passion_Fruit":     "Passion-fruit.pdf",
    "Custard_Apple":     "CustardApple.pdf",
    "Ber":               "Ber.pdf",

    # ═══ Spices (14) ═══
    "Ginger":            "Ginger.pdf",
    "Turmeric":          "Turmeric.pdf",
    "Garlic":            "Garlic.pdf",
    "Coriander":         "Coriander.pdf",
    "Cumin":             "Cumin.pdf",
    "Fennel":            "Fennel.pdf",
    "Fenugreek":         "Fenugreek.pdf",
    "Black_Pepper":      "Blackpepper.pdf",
    "Large_Cardamom":    "Largecardamom.pdf",
    "Small_Cardamom":    "Smallcardamom.pdf",
    "Clove":             "Clove.pdf",
    "Mint":              "Mint.pdf",
    "Curry_Leaf":        "Curryleaf.pdf",
    "Saffron":           "Saffron.pdf",

    # ═══ Plantation & Others (4) ═══
    "Coffee":            "Coffee.pdf",
    "Tea":               "Tea.pdf",
    "Arecanut":          "Arecanut.pdf",
    "Betelvine":         "Betelvine.pdf",
}


def download_pdf(crop_name: str, filename: str) -> bool:
    """Download a single PDF. Returns True on success."""
    save_path = PDF_DIR / f"{crop_name}.pdf"

    # Skip if already downloaded
    if save_path.exists() and save_path.stat().st_size > MIN_FILE_SIZE:
        print(f"  SKIP  {crop_name} (already exists, {save_path.stat().st_size // 1024}KB)")
        return True

    url = BASE_URL + filename
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and len(r.content) > MIN_FILE_SIZE:
            save_path.write_bytes(r.content)
            print(f"  OK    {crop_name} ({len(r.content) // 1024}KB)")
            return True
        else:
            print(f"  FAIL  {crop_name} — HTTP {r.status_code}, {len(r.content)} bytes")
            return False
    except requests.exceptions.Timeout:
        print(f"  ERR   {crop_name} — Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"  ERR   {crop_name} — {e}")
        return False


def main():
    print("=" * 60)
    print("🌾 NIPHM IPM PDF Downloader")
    print(f"   Source: {BASE_URL}")
    print(f"   Output: {PDF_DIR}")
    print(f"   Total:  {len(ALL_PDFS)} PDFs")
    print("=" * 60)

    # Create output directory
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = []

    for i, (crop_name, filename) in enumerate(ALL_PDFS.items(), 1):
        print(f"[{i:2d}/{len(ALL_PDFS)}]", end="")
        if download_pdf(crop_name, filename):
            success += 1
        else:
            failed.append(crop_name)
        time.sleep(DELAY)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"   Success: {success}/{len(ALL_PDFS)}")
    print(f"   Failed:  {len(failed)}")
    if failed:
        print(f"   Failed crops: {', '.join(failed)}")
    print(f"   Location: {PDF_DIR}")

    # Count total size
    total_size = sum(f.stat().st_size for f in PDF_DIR.glob("*.pdf"))
    print(f"   Total size: {total_size // (1024 * 1024)}MB")
    print("=" * 60)

    if failed:
        print(f"\nTo retry failed downloads, run the script again.")
        print(f"Already-downloaded files will be skipped automatically.")
        sys.exit(1)


if __name__ == "__main__":
    main()
