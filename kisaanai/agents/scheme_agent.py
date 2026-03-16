from typing import List, Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from kisaanai.core.state import BaseAgentState
from kisaanai.core.llm import llm_main, track_usage, get_llm_with_tools
from kisaanai.tools.scheme_tools import SCHEME_TOOLS
from datetime import datetime

# --- Nodes ---

def node_retrieve_schemes(state: BaseAgentState):
    """Retrieves schemes directly into state before LLM call (optional but efficient)."""
    # This is often handled by the tool, but pre-retrieval can save context space
    # For now, we rely on the tool-calling loop for flexibility.
    return {"messages": []}

def node_scheme_agent(state: BaseAgentState):
    """Main LLM node for the Scheme Agent."""
    system_prompt = f"""Tu KisaanAI ka expert Government Scheme Advisor hai.
Tera kaam hai farmers ko unke kaam ki schemes, subsidies, aur yojanas ke baare mein sahi jaankari dena.

RULES:
1. Always reply in natural Hinglish (Hindi + English mix).
2. Practical Advice: Explain eligibility simply (e.g., '2 hectare se kam zameen').
3. Specifics: Mention subsidy amounts (e.g., ₹6000, 50% discount) whenever available.
4. Next Steps: Tell them which documents are needed and provide the official link.
5. Honesty: Agar data nahi hai, toh politely bolo ki "Is baare mein abhi information available nahi hai".

Current Date: {datetime.now().strftime('%d %B %Y')}
"""
    # Bind tools to the main generation model
    llm_with_tools = get_llm_with_tools(SCHEME_TOOLS)
    
    # We only send the last few messages to save tokens in free tier
    messages = [SystemMessage(content=system_prompt)] + state.messages[-5:]
    
    response = llm_with_tools.invoke(messages)
    
    # Track usage (Gemini)
    usage_update = track_usage("gemini", response)
    
    return {
        "messages": [response],
        "usage": usage_update
    }

# --- Graph Construction ---

def build_scheme_graph():
    """Compiles the Scheme Agent subgraph."""
    workflow = StateGraph(BaseAgentState)

    # Add nodes
    workflow.add_node("agent", node_scheme_agent)
    workflow.add_node("tools", ToolNode(SCHEME_TOOLS))

    # Define edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# Final Agent Instance
scheme_agent = build_scheme_graph()
