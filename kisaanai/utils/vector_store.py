import faiss
import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from kisaanai.core.config import EMBED_MODEL_NAME

class VectorStore:
    """Reusable FAISS-based vector store for RAG."""
    
    def __init__(self, index_name: str, index_dir: Path):
        self.index_name = index_name
        self.index_dir = index_dir
        self.index_path = index_dir / f"{index_name}.index"
        self.meta_path = index_dir / f"{index_name}_meta.json"
        
        self._embedder = None
        self.index = None
        self.metadata = []
        self._loaded = False

    @property
    def embedder(self):
        """Lazy load the sentence transformer model."""
        if self._embedder is None:
            print(f"📥 Loading embedding model: {EMBED_MODEL_NAME}...")
            self._embedder = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embedder

    def build_from_csv(self, csv_path: Path, text_column: str = "search_text"):
        """Build a new FAISS index from a CSV file."""
        print(f"Building index '{self.index_name}' from {csv_path}...")
        df = pd.read_csv(csv_path).fillna("")
        
        texts = df[text_column].tolist()
        embeddings = self.embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        embeddings = np.array(embeddings).astype("float32")
        faiss.normalize_L2(embeddings)

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        self.metadata = df.to_dict(orient="records")

        # Save to disk
        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)
            
        self._loaded = True
        print(f"✅ Successfully built {self.index_name} with {len(self.metadata)} records.")

    def load(self):
        """Load the index and metadata from disk."""
        if self._loaded:
            return
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
            
        self.index = faiss.read_index(str(self.index_path))
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
        self._loaded = True
        print(f"✅ Loaded index '{self.index_name}' ({len(self.metadata)} records).")

    def search(self, query: str, k: int = 5) -> Tuple[List[Dict], List[float]]:
        """Perform semantic search."""
        if not self._loaded:
            self.load()
            
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        query_embedding = np.array(query_embedding).astype("float32")
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append(self.metadata[idx])
                
        return results, scores[0].tolist()
