# 🌾 KisaanAI 2.0: Modular Agentic Farming Assistant

KisaanAI 2.0 is a state-of-the-art, modular AI assistant designed to help Indian farmers navigate government schemes, farming best practices, and agricultural queries using a hybrid **LangGraph** architecture.

---

## 🚀 Key Features

- **Modular Agentic Design**: Built with LangGraph, separating logic into specialized agents (e.g., Scheme Agent).
- **Hybrid LLM Strategy**: 
  - **Groq (Llama-3.1-8B)**: Used for ultra-fast intent classification and routing.
  - **Gemini 1.5 Flash**: Leveraged for high-quality, nuanced generation in Hinglish.
- **Lazy-Loaded RAG**: Heavy machine learning models (SentenceTransformers) are loaded on-demand, ensuring near-instant startup for general queries.
- **Usage Tracking**: Built-in monitoring for token usage and provider-specific request counts.
- **Production-Ready Observability**: Fully integrated with **LangSmith** for deep trace analysis.

---

## 🏗️ Architecture Overview

KisaanAI 2.0 uses a "Router-Worker" pattern:
1. **Router**: Analyzes the farmer's query using Groq.
2. **Workers**: specialized agents like the **Scheme Agent** handle specific domains using RAG (Retrieval-Augmented Generation) with a FAISS vector store.
3. **Response Node**: Synthesizes the final answer in natural, friendly Hinglish.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### 1. Clone the Repository
```bash
git clone https://github.com/Maheshvala318/KisaanAI-2.0.git
cd KisaanAI-2.0
```

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
# LLM API Keys
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# LangSmith (Optional but Recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=KisaanAI-2.0
```

### 3. Install Dependencies
```bash
uv sync  # or pip install -r requirements.txt
```

### 4. Build the Knowledge Index
```bash
$env:PYTHONPATH="."
python scripts/build_scheme_index.py
```

### 5. Run the CLI
```bash
python main.py
```

---

## ✅ Production Readiness Checklist

As development continues, we are tracking these production requirements:

- [x] **Modular codebase** (Separation of core logic and agents)
- [x] **Performance Optimization** (Lazy model loading)
- [x] **Usage Tracking** (Token and request monitoring)
- [x] **Error Handling** (Retry logic for Gemini API)
- [ ] **Scalable Data Sync** (Automatic updates for scheme CSVs)
- [ ] **Multi-user Support** (Persistent database for thread history)
- [ ] **Deployment** (Containerization with Docker)
- [ ] **Security** (API Gateway for rate limiting)

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request or open an issue for new feature suggestions.

---

## 👤 Author

**Mahesh Vala**
- GitHub: [@Maheshvala318](https://github.com/Maheshvala318)
