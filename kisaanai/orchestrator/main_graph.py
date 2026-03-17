import sqlite3

# --- Nodes ---

def node_final_response(state):
    """
    Handling for general queries or formatting the final output.
    """
    from langchain_core.messages import AIMessage, SystemMessage
    from kisaanai.core.llm import get_llm_main, track_usage

    if isinstance(state.messages[-1], AIMessage) and not state.messages[-1].tool_calls:
        return {"messages": []}
    
    lang = state.language or "hinglish"
    system_msg = SystemMessage(content=f"Tu KisaanAI hai. Bina tools ke general queries ka {lang} mein jawab de. If language is 'gujarati', reply in pure Gujarati. If 'hindi', use pure Hindi. If 'hinglish', use mixed.")
    response = get_llm_main().invoke([system_msg] + state.messages[-3:])
    
    usage_update = track_usage("gemini", response)
    
    return {
        "messages": [response],
        "usage": usage_update
    }

# --- Main Graph ---

# Global instances to keep connection alive
_checkpointer = None
_kisaan_ai = None

def get_kisaan_ai():
    global _kisaan_ai, _checkpointer
    if _kisaan_ai is None:
        from langgraph.checkpoint.sqlite import SqliteSaver
        
        db_path = "kisaanai_memory.db"
        # Manual connection for synchronous SqliteSaver
        conn = sqlite3.connect(db_path, check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
        _checkpointer.setup()
        
        _kisaan_ai = build_kisaan_graph(_checkpointer)
    return _kisaan_ai

def build_kisaan_graph(checkpointer):
    """Compiles the master KisaanAI graph."""
    from langgraph.graph import StateGraph, START, END
    from kisaanai.state import BaseAgentState
    from kisaanai.orchestrator.router import node_classify_intent, route_to_agent
    from kisaanai.agents.scheme_agent import get_scheme_agent

    builder = StateGraph(BaseAgentState)
    
    # Add Nodes
    builder.add_node("router", node_classify_intent)
    builder.add_node("scheme_agent", get_scheme_agent())
    builder.add_node("final_response", node_final_response)
    
    # Define Edges
    builder.add_edge(START, "router")
    
    builder.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "scheme_agent": "scheme_agent",
            "disease_agent": "final_response", 
            "final_response": "final_response"
        }
    )
    
    builder.add_edge("scheme_agent", "final_response")
    builder.add_edge("final_response", END)
    
    return builder.compile(checkpointer=checkpointer)

def list_threads():
    """Returns a list of unique thread IDs stored in the SQLite memory."""
    db_path = "kisaanai_memory.db"
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = [row[0] for row in cursor.fetchall()]
        conn.close()
        return threads
    except Exception:
        return []
