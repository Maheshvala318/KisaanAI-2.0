"""
NIPHM Knowledge Base Indexer
============================
Creates embeddings for all Docling-extracted Markdown chunks using 
SentenceTransformers and stores them locally in Qdrant.

Usage:
    python scripts/build_niphm_qdrant.py
"""

import os
import json
from pathlib import Path
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# ── Config ──────────────────────────────────────────────────────
# Using a fast, high-quality English model (since Groq pre-translates queries to English)
EMBED_MODEL = "all-MiniLM-L6-v2"
QDRANT_PATH = Path(__file__).resolve().parent.parent / "qdrant_storage"
CHUNK_DIR = Path(__file__).resolve().parent.parent / "dataset" / "chunks"
COLLECTION = "niphm_disease_kb"
BATCH_SIZE = 64

def main():
    print("=" * 60)
    print("🧠 Building NIPHM Knowledge Base (Qdrant)")
    print("=" * 60)
    
    chunk_files = list(CHUNK_DIR.glob("niphm_text_*.json"))
    if not chunk_files:
        print(f"❌ No 'niphm_text_*.json' chunks found in {CHUNK_DIR}. Run extract_niphm.py first.")
        exit(1)
        
    chunks = []
    for cf in chunk_files:
        with open(cf, "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))
        
    print(f"📦 Loaded {len(chunks):,} intelligent chunks.")
    
    print("\n⏳ Loading Embedding Model (might download on first run)...")
    model = SentenceTransformer(EMBED_MODEL)
    embed_dim = model.get_sentence_embedding_dimension()
    print(f"✅ Model loaded (Dimension: {embed_dim})")
    
    print("\n💾 Connecting to local Qdrant...")
    client = QdrantClient(path=str(QDRANT_PATH))
    
    # Check if collection exists
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing:
        client.delete_collection(collection_name=COLLECTION)
        print(f"✅ Deleted old collection: '{COLLECTION}'")
        
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=embed_dim, distance=Distance.COSINE),
    )
    print(f"✅ Created fresh collection: '{COLLECTION}'")
    start_id = 1
        
    print("\n🚀 Generating embeddings and indexing...")
    point_id = start_id
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Indexing Batches"):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [item["search_text"] for item in batch]
        
        # Generate embeddings
        embeddings = model.encode(texts, batch_size=len(batch), show_progress_bar=False, convert_to_numpy=True)
        
        # Build points
        points = []
        for item, emb in zip(batch, embeddings):
            points.append(PointStruct(
                id=point_id,
                vector=emb.tolist(),
                payload={
                    "id": item.get("id", ""),
                    "crop": item.get("crop", ""),
                    "text": item.get("text", ""),
                    "source": item.get("source", ""),
                    "images": item.get("images", [])
                }
            ))
            point_id += 1
            
        # Upload batch
        client.upsert(collection_name=COLLECTION, points=points)
        
    total_vectors = client.count(COLLECTION).count
    print("\n" + "=" * 60)
    print(f"🎉 INDEXING COMPLETE")
    print(f"   Database: {QDRANT_PATH}")
    print(f"   Total Vectors: {total_vectors:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
