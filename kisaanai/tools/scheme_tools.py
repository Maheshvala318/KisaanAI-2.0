from kisaanai.utils.vector_store import VectorStore
from kisaanai.core.config import FAISS_INDEX_DIR
from langchain_core.tools import tool
import pandas as pd

# Load the vector store once (global instance for the agent)
scheme_store = VectorStore(index_name="scheme", index_dir=FAISS_INDEX_DIR)

@tool
def search_schemes(query: str) -> str:
    """
    Search for government agricultural schemes, subsidies, and yojanas.
    Use this when the farmer asks about financial help, support, or specific scheme names.
    Input should be a clear search query in English or Hinglish.
    """
    try:
        results, scores = scheme_store.search(query, k=4)
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
    Lists major agricultural schemes for a specific Indian state (e.g., Gujarat, Punjab).
    Use this when the farmer asks 'Mere state mein kaunsi schemes hain?'.
    """
    try:
        scheme_store.load()
        df = pd.DataFrame(scheme_store.metadata)
        
        # Simple string match for state
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

# Export tools list for the graph
SCHEME_TOOLS = [search_schemes, get_scheme_by_state]
