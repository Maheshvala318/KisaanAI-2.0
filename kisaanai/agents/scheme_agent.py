from typing import List, Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from kisaanai.state import BaseAgentState
from kisaanai.core.llm import get_llm_main, track_usage, get_llm_with_tools
from kisaanai.tools.scheme_tools import get_scheme_tools
from datetime import datetime

# --- Nodes ---

def node_scheme_agent(state: BaseAgentState):
    """Main LLM node for the Scheme Agent."""
    lang = state.language or "hinglish"
    system_prompt = f"""Tu KisaanAI ka expert Government Scheme Advisor hai.
    RULES:
    1. Language: Reply in {lang}. If 'gujarati', use pure Gujarati. If 'hindi', use pure Hindi. If 'hinglish', use Hindi+English.
    2. Practical Advice: Explain eligibility simply.
    3. Specifics: Mention subsidy amounts whenever available.
    4. Next Steps: Tell them which documents are needed and provide the official link.
    5. Honesty: Agar data nahi hai, toh politely bolo.
    
    Current Date: {datetime.now().strftime('%d %B %Y')}
    """
    # Bind tools lazily
    tools = get_scheme_tools()
    llm_with_tools = get_llm_with_tools(tools)
    
    messages = [SystemMessage(content=system_prompt)] + state.messages[-5:]
    response = llm_with_tools.invoke(messages)
    
    usage_update = track_usage("gemini", response)
    
    return {
        "messages": [response],
        "usage": usage_update
    }

def build_scheme_graph():
    """Compiles the Scheme Agent subgraph."""
    workflow = StateGraph(BaseAgentState)
    from langgraph.prebuilt import ToolNode, tools_condition

    # Add nodes
    workflow.add_node("agent", node_scheme_agent)
    workflow.add_node("tools", ToolNode(get_scheme_tools()))

    # Define edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# Lazy loaded instance
_scheme_agent_graph = None

def get_scheme_agent():
    global _scheme_agent_graph
    if _scheme_agent_graph is None:
        _scheme_agent_graph = build_scheme_graph()
    return _scheme_agent_graph
