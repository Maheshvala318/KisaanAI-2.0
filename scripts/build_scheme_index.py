from kisaanai.utils.vector_store import VectorStore
from kisaanai.core.config import SCHEME_CSV, FAISS_INDEX_DIR

def build():
    """Build the FAISS index for agricultural schemes."""
    if not SCHEME_CSV.exists():
        print(f"❌ Scheme dataset not found at {SCHEME_CSV}")
        return

    # Initialize VectorStore for schemes
    store = VectorStore(index_name="scheme", index_dir=FAISS_INDEX_DIR)
    
    # Build from CSV
    # The 'search_text' column was pre-calculated in the dataset preparation step
    store.build_from_csv(csv_path=SCHEME_CSV, text_column="search_text")
    
    print("\n✅ Scheme index build complete.")

if __name__ == "__main__":
    build()
