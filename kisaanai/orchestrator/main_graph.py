from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from kisaanai.core.state import BaseAgentState
from kisaanai.orchestrator.router import node_classify_intent, route_to_agent
from kisaanai.agents.scheme_agent import scheme_agent
from langchain_core.messages import AIMessage
from kisaanai.core.llm import llm_main, track_usage

# --- Nodes ---

def node_final_response(state: BaseAgentState):
    """
    Handling for general queries or formatting the final output.
    If an agent has already responded, we just pass it through.
    If it's a general query, we let Gemini answer.
    """
    # If the last message is already an AI message from a specialist agent,
    # we don't need to generate a new one, but we could add a disclaimer here.
    if isinstance(state.messages[-1], AIMessage) and not state.messages[-1].tool_calls:
        return {"messages": []}
    
    # Otherwise, it's a general query (Namaste, etc.)
    system_msg = SystemMessage(content="Tu KisaanAI hai. Bina tools ke general queries ka Hinglish mein jawab de.")
    response = llm_main.invoke([system_msg] + state.messages[-3:])
    
    # Track usage
    usage_update = track_usage("gemini", response)
    
    return {
        "messages": [response],
        "usage": usage_update
    }

# --- Main Graph ---

def build_kisaan_graph():
    """Compiles the master KisaanAI graph."""
    # We use BaseAgentState which includes our usage tracking
    builder = StateGraph(BaseAgentState)
    
    # Add Nodes
    builder.add_node("router", node_classify_intent)
    builder.add_node("scheme_agent", scheme_agent)
    builder.add_node("final_response", node_final_response)
    # Add other agents (disease, etc.) here in future
    
    # Define Edges
    builder.add_edge(START, "router")
    
    builder.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "scheme_agent": "scheme_agent",
            "disease_agent": "final_response", # Placeholder
            "final_response": "final_response"
        }
    )
    
    builder.add_edge("scheme_agent", "final_response")
    builder.add_edge("final_response", END)
    
    # Persistence (InMemory for dev)
    checkpointer = InMemorySaver()
    
    return builder.compile(checkpointer=checkpointer)

# Master Instance
kisaan_ai = build_kisaan_graph()
