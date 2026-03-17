from typing import Any
from kisaanai.core.config import GROQ_API_KEY, GEMINI_API_KEY
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from kisaanai.state import UsageStats
from datetime import datetime

# 1. Fast LLM (Groq - Llama 3.1 8B)
llm_fast = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=GROQ_API_KEY,
    temperature=0.0
)

# 2. Main Generation LLM (Gemini Flash - Latest)
llm_main = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
    convert_system_message_to_human=True,
    max_retries=2 # Built-in LangChain retry logic
)

def track_usage(provider: str, response: Any) -> UsageStats:
    """Extracts usage data from LLM response and returns a UsageStats object."""
    # Note: Exact token extraction varies by provider in LangChain
    tokens = 0
    try:
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = response.usage_metadata.get("total_tokens", 0)
    except:
        pass
    
    return UsageStats(
        total_requests=1,
        groq_requests=1 if provider == "groq" else 0,
        gemini_requests=1 if provider == "gemini" else 0,
        total_tokens=tokens,
        last_call_timestamp=datetime.now().isoformat()
    )

# Shared tool-enabled LLM
def get_llm_with_tools(tools):
    return llm_main.bind_tools(tools)
