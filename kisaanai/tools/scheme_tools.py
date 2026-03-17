from langchain_core.tools import tool

# Lazy loaded instance
_scheme_store = None

def get_scheme_store():
    global _scheme_store
    if _scheme_store is None:
        from kisaanai.utils.vector_store import VectorStore
        from kisaanai.core.config import FAISS_INDEX_DIR
        _scheme_store = VectorStore(index_name="scheme", index_dir=FAISS_INDEX_DIR)
    return _scheme_store

@tool
def search_schemes(query: str) -> str:
    """
    Search for government agricultural schemes, subsidies, and yojanas.
    """
    try:
        results, scores = get_scheme_store().search(query, k=4)
        if not results:
            return "Koi matching scheme nahi mili. Kripya thoda detail mein bataiye."
        
        formatted = []
        for i, (res, score) in enumerate(zip(results, scores), 1):
            formatted.append(
                f"[Scheme {i} - Relevance: {score:.2f}]\n"
                f"Name: {res.get('scheme_name')}\n"
                f"State: {res.get('state')}\n"
                f"Benefits: {res.get('benefits', 'N/A')[:400]}\n"
                f"Eligibility: {res.get('eligibility', 'N/A')[:300]}\n"
                f"Documents: {res.get('documents_required', 'N/A')[:200]}\n"
                f"Apply: {res.get('url', 'N/A')}"
            )
        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {str(e)}"

@tool
def get_scheme_by_state(state_name: str) -> str:
    """
    Lists major agricultural schemes for a specific Indian state.
    """
    try:
        store = get_scheme_store()
        store.load()
        import pandas as pd
        df = pd.DataFrame(store.metadata)
        
        mask = df['state'].str.lower().str.contains(state_name.lower(), na=False)
        filtered = df[mask].head(10)
        
        if filtered.empty:
            return f"{state_name} ke liye koi special scheme record mein nahi mili."
        
        lines = [f"**{state_name} ke liye schemes:**"]
        for _, row in filtered.iterrows():
            lines.append(f"- {row['scheme_name']}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Filter error: {str(e)}"

# Function to get tools list lazily
def get_scheme_tools():
    return [search_schemes, get_scheme_by_state]
