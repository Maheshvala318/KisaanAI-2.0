from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
from kisaanai.orchestrator.main_graph import kisaan_ai
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="KisaanAI 2.0 API", description="Modular Multi-Agent Assistant for Indian Farmers")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    usage: Optional[dict] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Invokes the KisaanAI modular graph."""
    session_id = req.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        # Run the graph
        result = await kisaan_ai.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config
        )
        
        # Extract the last message (final response)
        final_msg = result["messages"][-1]
        
        # Extract metadata from state
        state = kisaan_ai.get_state(config)
        
        return ChatResponse(
            response=final_msg.content,
            session_id=session_id,
            intent=state.values.get("intent"),
            usage=state.values.get("usage").dict() if state.values.get("usage") else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "system": "KisaanAI 2.0", "version": "Modular-v1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
