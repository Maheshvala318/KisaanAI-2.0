import uuid
from kisaanai.orchestrator.main_graph import get_kisaan_ai, list_threads
from kisaanai.core.llm import get_llm_main, get_llm_fast
from langchain_core.messages import HumanMessage
import sys
import os

def select_thread():
    """Menu to select an existing chat thread or start a new one."""
    threads = list_threads()
    
    print("\n" + "="*50)
    print("📜 CHAT HISTORY")
    print("="*50)
    print("0. [NEW] Start a fresh conversation")
    
    for i, tid in enumerate(threads, 1):
        print(f"{i}. [RESUME] {tid}")
    
    print("="*50)
    
    try:
        choice = input("\nSelect a chat (0-{}): ".format(len(threads))).strip()
        if not choice or choice == "0":
            new_id = str(uuid.uuid4())[:8]
            print(f"✨ Starting new chat: {new_id}")
            return new_id
        
        idx = int(choice) - 1
        if 0 <= idx < len(threads):
            tid = threads[idx]
            print(f"🔄 Resuming chat: {tid}")
            return tid
        else:
            new_id = str(uuid.uuid4())[:8]
            print(f"⚠️ Invalid choice. Starting new chat: {new_id}")
            return new_id
    except (ValueError, IndexError, KeyboardInterrupt):
        new_id = str(uuid.uuid4())[:8]
        print(f"\n✨ Starting new chat: {new_id}")
        return new_id

def run_cli():
    """Interactive CLI to chat with the modular KisaanAI system."""
    session_id = select_thread()
    config = {"configurable": {"thread_id": session_id}}
    
    print("\n" + "="*50)
    print(f"🌾 KisaanAI 2.0 (Modular) - Active Session: {session_id}")
    # ChatGroq uses model_name, ChatGoogleGenerativeAI uses model
    fast_llm = get_llm_fast()
    main_llm = get_llm_main()
    fast_model = getattr(fast_llm, "model_name", getattr(fast_llm, "model", "Unknown"))
    main_model = getattr(main_llm, "model", getattr(main_llm, "model_name", "Unknown"))
    print(f"🤖 Models: {fast_model} (Fast) | {main_model} (Main)")
    print("Commands: 'exit' (quit), 'stats' (usage), '/history' (switch), '/new' (fresh start)")
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
            
        if user_input.lower() == "/new":
            session_id = str(uuid.uuid4())[:8]
            config = {"configurable": {"thread_id": session_id}}
            print(f"\n✨ Switched to NEW session: {session_id}\n")
            continue

        if user_input.lower() == "/history":
            session_id = select_thread()
            config = {"configurable": {"thread_id": session_id}}
            print(f"\n🔄 Switched to session: {session_id}\n")
            continue

        if user_input.lower() == "stats":
            kisaan_app = get_kisaan_ai()
            state = kisaan_app.get_state(config)
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
            kisaan_app = get_kisaan_ai()
            result = kisaan_app.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config
            )
            
            raw_response = result["messages"][-1].content
            
            if isinstance(raw_response, list):
                response_text = "".join([str(b.get('text', b)) if isinstance(b, dict) else str(b) for b in raw_response])
            else:
                response_text = str(raw_response)
                
            print(f"KisaanAI: {response_text}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        pass
