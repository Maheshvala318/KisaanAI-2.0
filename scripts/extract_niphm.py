"""
NIPHM PDF Extractor via PyMuPDF (fitz)
======================================
Extracts BOTH text and embedded images from NIPHM PDFs.
Saves images to dataset/niphm_images/ and embeds [IMAGE: filename]
tags directly into the text chunks for RAG integration.

Usage:
    python scripts/extract_niphm.py
"""

import os
import gc
import json
import re
from pathlib import Path
from tqdm import tqdm
import fitz  # PyMuPDF

# ── Config ──────────────────────────────────────────────────────
PDF_DIR = Path(__file__).resolve().parent.parent / "dataset" / "niphm_pdfs"
CHUNK_DIR = Path(__file__).resolve().parent.parent / "dataset" / "chunks"
IMAGE_DIR = Path(__file__).resolve().parent.parent / "dataset" / "niphm_images"

CHUNK_SIZE = 300     # words per chunk
CHUNK_OVERLAP = 50   # word overlap for context

def init():
    print("=" * 60)
    print("🌾 NIPHM Multimodal Extractor (PyMuPDF)")
    print(f"   Source PDFs: {PDF_DIR}")
    print(f"   Output JSON: {CHUNK_DIR}")
    print(f"   Output IMGs: {IMAGE_DIR}")
    print("=" * 60)
    
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    pdfs = list(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("❌ No PDFs found in dataset/niphm_pdfs. Run download_niphm_pdfs.py first.")
        exit(1)
        
    return pdfs

def clean_text(text: str) -> str:
    """Basic text cleanup."""
    if not text:
        return ""
    # We don't want to break the [IMAGE: ...] tags, so just collapse spaces.
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def chunk_text(text: str, doc_name: str, source_file: str) -> list[dict]:
    """Split text into overlapping searchable chunks, preserving [IMAGE: ...] tags."""
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + CHUNK_SIZE]).strip()
        if len(chunk) > 100:  # Skip tiny fragments
            
            # Extract image references from this chunk for metadata
            images_in_chunk = re.findall(r"\[IMAGE: (.*?)\]", chunk)
            
            chunks.append({
                "id": f"{doc_name}_chunk_{len(chunks)}",
                "type": "multimodal",
                "crop": doc_name,
                "text": chunk,
                "images": images_in_chunk,  # Metadata array of image filenames
                "source": source_file,
                "search_text": f"{doc_name} {chunk}",
            })
        i += CHUNK_SIZE - CHUNK_OVERLAP
        
    return chunks

def extract_pdf_multimodal(pdf_path: Path, crop_name: str) -> str:
    """Extract all text and images from a PDF using PyMuPDF."""
    doc = fitz.open(str(pdf_path))
    full_text_parts = []
    
    # Create crop specific image folder
    crop_img_dir = IMAGE_DIR / crop_name
    crop_img_dir.mkdir(parents=True, exist_ok=True)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Extract Text
        page_text = page.get_text("text").replace("\n", " ").strip()
        
        # 2. Extract Images
        images_on_page = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            
            # Only extract decent sized images, skip tiny icons/1x1 transparent pixels
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)
            
            # Filter out tiny insignificant images (like bullets or logos)
            if width < 50 or height < 50:
                continue
                
            image_filename = f"{crop_name}_p{page_num+1}_i{img_index+1}.{image_ext}"
            image_filepath = crop_img_dir / image_filename
            
            # Save to disk
            with open(image_filepath, "wb") as f:
                f.write(image_bytes)
                
            # Path relative to project root for easy rendering in frontend later
            rel_img_path = f"dataset/niphm_images/{crop_name}/{image_filename}"
            images_on_page.append(rel_img_path)
            
        # 3. Append image references linearly into the page text
        if images_on_page:
            image_refs = " ".join([f"[IMAGE: {img}]" for img in images_on_page])
            page_text = f"{page_text} {image_refs}"
            
        if page_text:
            full_text_parts.append(page_text)
            
    doc.close()
    return " ".join(full_text_parts)

def main():
    pdfs = init()
    
    failed = []
    success_count = 0
    total_chunks = 0
    total_images = 0
    
    for pdf_path in tqdm(pdfs, desc="Extracting PDFs"):
        crop_name = pdf_path.stem
        output_path = CHUNK_DIR / f"niphm_text_{crop_name}.json"
        
        # To avoid bugs where we only extracted text before, we overwrite existing jsons 
        # this time since we changed to multimodal feature.
        
        try:
            # 1. Extract raw text + download images in one pass
            raw_text = extract_pdf_multimodal(pdf_path, crop_name)
            clean = clean_text(raw_text)
            
            # 2. Chunk the text
            chunks = chunk_text(clean, crop_name, pdf_path.name)
            
            # 3. Save immediately
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
                
            total_chunks += len(chunks)
            total_images += sum([len(c["images"]) for c in chunks])
            success_count += 1
            
            # 4. Aggressive memory cleanup
            del raw_text
            del clean
            del chunks
            gc.collect()
            
        except Exception as e:
            tqdm.write(f"❌ Failed to extract {crop_name}: {e}")
            failed.append(crop_name)
            
    print("\n" + "=" * 60)
    print("📊 MULTIMODAL EXTRACTION SUMMARY")
    print(f"   Success: {success_count}/{len(pdfs)} PDFs")
    print(f"   Failed:  {len(failed)}")
    print(f"   Total text chunks generated: {total_chunks:,}")
    print(f"   Total image references:      {total_images:,}")
    print(f"   Saved to: {CHUNK_DIR}")
    print("=" * 60)
    
if __name__ == "__main__":
    main()
