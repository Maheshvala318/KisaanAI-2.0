from langchain_core.messages import SystemMessage, HumanMessage
from kisaanai.core.llm import llm_fast, track_usage
from kisaanai.orchestrator.models import IntentResult
from kisaanai.state import BaseAgentState
import json

# Initialize the structured LLM (Using Groq for speed and cost efficiency)
router_llm = llm_fast.with_structured_output(IntentResult)

def node_classify_intent(state: BaseAgentState):
    """
    Orchestrator Node 1: Classifies user intent using a fast, low-cost model.
    """
    last_msg = state.messages[-1].content if state.messages else ""
    
    system_prompt = """You are the Lead Orchestrator for KisaanAI, an AI system for Indian farmers.
Your job is to classify the user's message intent and translate it to clear English.

INTENTS:
- 'scheme': Questions about government yojanas, subsidies, financial help, or PM-Kisan.
- 'disease': Questions about crop diseases, pests, insects, or yellowing leaves.
- 'crop_recommendation': Questions about what crops to grow in a season or soil.
- 'price': Questions about mandi prices, market rates, or when to sell.
- 'general': Greetings (Namaste), praise, or simple general farming talk.
- 'out_of_scope': Politics, sports, entertainment, or anything not related to farming.

Return a valid structured object with: intent, language, confidence, and query_english.
"""
    
    try:
        # We give only the last message for speed, unless state.messages is long
        result = router_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_msg)
        ])
        
        # Track usage (Groq)
        usage_update = track_usage("groq", result)
        
        return {
            "intent": result.intent,
            "language": result.language,
            "query_english": result.query_english,
            "usage": usage_update
        }
    except Exception as e:
        print(f"Routing Error: {e}")
        # Safe fallback
        return {
            "intent": "general",
            "language": "hinglish"
        }

def route_to_agent(state: BaseAgentState) -> str:
    """Conditional edge logic based on intent."""
    intent = state.intent or "general"
    
    if intent == "scheme":
        return "scheme_agent"
    elif intent == "disease":
        return "disease_agent"
    elif intent == "general":
        return "final_response"
    else:
        return "final_response"
