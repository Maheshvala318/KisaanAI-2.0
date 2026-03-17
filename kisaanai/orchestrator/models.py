from typing import Literal, Optional
from pydantic import BaseModel, Field

class IntentResult(BaseModel):
    """Structured output for the KisaanAI orchestrator router."""
    
    language: Literal["hindi", "hinglish", "english", "gujarati", "mixed"] = Field(
        description="The detected language of the user's message."
    )
    
    intent: Literal["scheme", "disease", "crop_recommendation", "price", "general", "out_of_scope"] = Field(
        description="The categorised intent of the user's message."
    )
    
    confidence: float = Field(
        description="Confidence score for the intent (0.0 to 1.0)."
    )
    
    query_english: str = Field(
        description="The user's query rephrased into clear, concise English for database search."
    )
    
    is_followup: bool = Field(
        description="Whether this query is a follow-up to a previous part of the conversation."
    )
