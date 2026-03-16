import asyncio
import uuid
from kisaanai.orchestrator.main_graph import kisaan_ai
from kisaanai.core.llm import llm_main, llm_fast
from langchain_core.messages import HumanMessage
import sys

async def run_cli():
    """Interactive CLI to chat with the modular KisaanAI system."""
    session_id = str(uuid.uuid4())[:8]
    config = {"configurable": {"thread_id": session_id}}
    
    print("\n" + "="*50)
    print(f"🌾 KisaanAI 2.0 (Modular) - Session: {session_id}")
    # ChatGroq uses model_name, ChatGoogleGenerativeAI uses model
    fast_model = getattr(llm_fast, "model_name", "Unknown")
    main_model = getattr(llm_main, "model", "Unknown")
    print(f"🤖 Models: {fast_model} (Fast) | {main_model} (Main)")
    print("Type 'exit' to quit, 'stats' to see LLM usage.")
    print("="*50 + "\n")
    
    while True:
        try:
            user_input = input("Farmer: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDhanyavaad! 👋")
            break
            
        if not user_input:
            continue
            
        if user_input.lower() == "exit":
            print("KisaanAI: Dhanyavaad! 👋")
            break
            
        if user_input.lower() == "stats":
            state = kisaan_ai.get_state(config)
            usage = state.values.get("usage")
            if usage:
                print(f"\n📊 [LLM Stats]")
                print(f"   Total Requests: {usage.total_requests}")
                print(f"   Groq (Fast):    {usage.groq_requests}")
                print(f"   Gemini (Main):  {usage.gemini_requests}")
                print(f"   Total Tokens:   {usage.total_tokens}")
                print(f"   Last Call:      {usage.last_call_timestamp}\n")
            else:
                print("\nNo stats available yet.\n")
            continue

        print("\nAI is thinking...", end="\r")
        
        # Invoke the graph
        try:
            result = await kisaan_ai.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config
            )
            
            # The last message is the final response
            raw_response = result["messages"][-1].content
            
            # Clean up response if it's a list (some newer SDKs return structured blocks)
            if isinstance(raw_response, list):
                response_text = ""
                for block in raw_response:
                    if isinstance(block, dict) and 'text' in block:
                        response_text += block['text']
                    else:
                        response_text += str(block)
            else:
                response_text = str(raw_response)
                
            print(f"KisaanAI: {response_text}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        pass
