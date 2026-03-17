from typing import Annotated, Optional, List, Dict, Any
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

def merge_docs(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Helper to merge retrieved documents without duplicates."""
    if not existing:
        return new
    seen = {d.get("scheme_name", d.get("disease_name", "")) for d in existing}
    return existing + [d for d in new if d.get("scheme_name", d.get("disease_name", "")) not in seen]

class UsageStats(BaseModel):
    """Tracks token usage and request counts for free-tier efficiency."""
    total_requests: int = 0
    groq_requests: int = 0
    gemini_requests: int = 0
    total_tokens: int = 0
    last_call_timestamp: Optional[str] = None

def merge_usage(existing: UsageStats, new: UsageStats) -> UsageStats:
    """Updates usage stats cumulatively."""
    if not existing:
        return new
    return UsageStats(
        total_requests=existing.total_requests + new.total_requests,
        groq_requests=existing.groq_requests + new.groq_requests,
        gemini_requests=existing.gemini_requests + new.gemini_requests,
        total_tokens=existing.total_tokens + new.total_tokens,
        last_call_timestamp=new.last_call_timestamp or existing.last_call_timestamp
    )

class BaseAgentState(BaseModel):
    """Common state shared by all agents."""
    messages: Annotated[list[BaseMessage], add_messages]
    
    # RAG results
    retrieved_docs: Annotated[List[Dict[str, Any]], merge_docs] = []
    
    # LLM Efficiency Tracking
    usage: Annotated[UsageStats, merge_usage] = UsageStats()
    
    # Metadata
    intent: Optional[str] = "general"
    language: Optional[str] = "hinglish"
    query_english: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
