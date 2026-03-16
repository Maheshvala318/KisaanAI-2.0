# 🌾 KisaanAI 2.0 — Complete Production Blueprint

---

## 📋 MASTER CONTEXT BLOCK
### *(Read this first — designed so any AI model understands the full project in one pass)*

---

### What This Project Is

**KisaanAI 2.0** is an AI-powered agricultural assistant built for **Indian farmers**. It answers farming questions in **Hindi, Hinglish, and English** through a multi-agent system. Each agent is a specialist — one knows crop diseases, one knows government schemes, one recommends crops, one tracks market prices. A central orchestrator routes every farmer query to the right specialist automatically.

The entire system is built using **LangGraph** — a graph-based agent orchestration framework by LangChain. Every major LangGraph concept (subgraphs, streaming, human-in-the-loop, Send API, persistent memory, tool calling, structured output) is deliberately used in this project. This is both a real-world production system and a comprehensive LangGraph learning project.

---

### The Problem Being Solved

India has 140 million farmers. They struggle to access three types of critical information:

| Problem | Example | Agent That Solves It |
|---------|---------|----------------------|
| Crop diseases destroying yield | "Mere tamatar ke patte peele ho rahe hain" | Disease Agent |
| Government subsidies going unclaimed | "Koi yojana hai meri category ke liye?" | Scheme Agent |
| Growing wrong crops for the season/soil | "Is mausam mein kya ugaoon?" | Crop Rec Agent |
| Selling crops at the wrong time/price | "Aaj mandi mein rate kya hai?" | Price Agent |

Information exists but is scattered across dozens of government portals, agricultural websites, and extension offices — all in formal English or complex Hindi. KisaanAI brings it together in one simple conversational interface.

---

### Technical Identity — What Kind of System This Is

```
Type:           Multi-agent AI system with RAG (Retrieval-Augmented Generation)
Framework:      LangGraph (agent orchestration) + LangChain (LLM interface)
LLM:            Groq API — Llama 3.1 70B (responses) + Llama 3.1 8B (routing/classification)
Vector Search:  FAISS + SentenceTransformers (all-MiniLM-L6-v2)
Memory:         LangGraph checkpointer — InMemorySaver (dev) / PostgreSQL (production)
API Layer:      FastAPI with Server-Sent Events streaming
Language:       Python 3.11+
Deployment:     Docker + Railway/Render → LangGraph Platform
Data Pipeline:  MyScheme.gov.in API + Kaggle CSV + Groq LLM generation + AgMarkNet API
```

---

### The Four Agents — What Each One Does

#### Agent 1 — Disease Agent
- **Purpose**: Identifies crop diseases from symptoms, gives treatment and prevention advice
- **Approach**: RAG — farmer describes symptoms → FAISS finds matching disease records → LLM explains in Hinglish
- **Data**: CSV with 1,500+ rows of (crop, disease, symptoms, treatment, prevention) records
- **LangGraph pattern used**: Standard subgraph with sequential nodes (embed → search → validate → respond → safety_check)

#### Agent 2 — Scheme Agent
- **Purpose**: Helps farmers find government subsidies and schemes they qualify for
- **Approach**: RAG + Tool Calling — FAISS finds relevant schemes → LLM uses tools to check live deadlines and calculate subsidy amounts
- **Data**: 500+ government schemes scraped from MyScheme.gov.in API (all Indian states)
- **LangGraph pattern used**: Subgraph with ToolNode + tools_condition (LLM ↔ tools loop)

#### Agent 3 — Crop Recommendation Agent
- **Purpose**: Recommends what crops to grow based on soil type, weather, and season
- **Approach**: RAG-as-Classifier — no ML model needed. Kaggle crop CSV (2,200 rows) stored in FAISS. Farmer's soil/weather params are matched to nearest-neighbor examples. LLM votes + explains.
- **Data**: Kaggle "Crop Recommendation Dataset" — N, P, K, temperature, humidity, pH, rainfall → crop label
- **LangGraph pattern used**: Subgraph with structured LLM output (Pydantic) for param extraction + rule-based filter node

#### Agent 4 — Price Agent
- **Purpose**: Tells farmers today's mandi prices and whether to sell now or wait
- **Approach**: Live API + statistics + LLM reasoning — no ML forecasting model needed. Tools fetch live AgMarkNet data, calculate 7-day arithmetic trend, look up seasonal patterns. LLM synthesizes into advice.
- **Data**: Live from AgMarkNet via free data.gov.in API (real-time, no static dataset)
- **LangGraph pattern used**: Subgraph with ToolNode — LLM decides which tools to call, ToolNode executes them, LLM synthesizes results

---

### The Master Orchestrator — How Routing Works

Every farmer message goes through the orchestrator first. It has 5 nodes:

```
[START]
   ↓
[language_detect]     → Detects Hindi / Hinglish / English (rule-based, fast, no LLM cost)
   ↓
[intent_classify]     → LLM with Pydantic structured output → returns route + confidence + english_query
   ↓
[safety_gate]         → interrupt() if query involves critical safety topics (human-in-the-loop)
   ↓
[conditional router]  → routes to disease_agent / scheme_agent / crop_rec_agent / price_agent
                        OR uses Send API for parallel execution if query spans multiple agents
   ↓
[format_response]     → adds disclaimer, source citation, formats final answer
   ↓
[END]
```

Routing uses **3 layers**:
1. Rule-based keyword detection (fast, zero LLM cost for obvious queries)
2. LLM classification with Pydantic structured output (never returns invalid route)
3. Send API for parallel multi-agent execution when one query needs multiple specialists

---

### LangGraph Concepts — Full Coverage Map

This project deliberately uses every major LangGraph concept. Here is what is used and where:

| Concept | Where Used |
|---------|-----------|
| `StateGraph` | Every agent and the orchestrator |
| `TypedDict` with `Annotated` | `OrchestratorState`, `AgentState` |
| `add_messages` reducer | All states — message history accumulation |
| Custom reducer function | `merge_docs` — merges retrieved docs from parallel agents |
| `add_node` | Every processing step in every graph |
| `add_edge` (direct) | Sequential nodes within each agent |
| `add_conditional_edges` | Orchestrator routing + tools_condition |
| `START` / `END` | All graphs |
| `compile()` | All graphs |
| Subgraphs | Each agent is an independently compiled subgraph used as a node |
| `InMemorySaver` checkpointer | Development environment |
| `AsyncPostgresSaver` | Production — conversations persist across restarts |
| `thread_id` config | Per-farmer conversation isolation |
| `Send` API | Parallel execution when query needs disease + scheme agents simultaneously |
| `Command` API | Resuming graph after human-in-the-loop interrupt |
| `interrupt()` | Safety gate before sending critical pesticide/medical advice |
| `ToolNode` | Scheme Agent (deadline/subsidy tools) + Price Agent (API tools) |
| `tools_condition` | Routes LLM output → ToolNode or END |
| `astream_events` | FastAPI SSE endpoint for token-level streaming |
| `stream_mode="messages"` | Frontend real-time token display |
| `stream_mode="updates"` | Debug/monitoring — see each node's output |
| `MessagesState` | Simplified state for agents that only need messages |
| `with_structured_output` (Pydantic) | Intent classification (returns guaranteed valid JSON) |
| Retry logic on nodes | Handles Groq API rate limits gracefully |
| `aget_state` / `aget_state_history` | Conversation history API endpoint |
| LangSmith tracing | Full production observability |

---

### Data Sources — Where All Data Comes From

| Agent | Data Source | How to Get It | Cost |
|-------|------------|---------------|------|
| Disease Agent | LLM-generated (Groq) using 55+ crop-disease seed pairs | Run `generate_disease_dataset.py` | Free (Groq free tier) |
| Disease Agent | Existing disease CSV from developer's notebook | Already available | Done |
| Scheme Agent | MyScheme.gov.in public API | No key needed, run `collect_schemes.py` | Free |
| Scheme Agent | Gujarat Ikhedut Portal (existing data) | Already available | Done |
| Crop Rec Agent | Kaggle "Crop Recommendation Dataset" (2,200 rows) | Download from Kaggle or GitHub mirror | Free |
| Price Agent | AgMarkNet via data.gov.in API | Register at data.gov.in for free API key | Free |

**No paid data sources. No manual data entry. No web scraping of protected sites.**

---

### Current State of the Project (What Exists vs. What Needs Building)

**Already built (in `models.ipynb`):**
- ✅ Scheme Agent — FAISS + SentenceTransformers + Groq, working RAG pipeline
- ✅ Disease Agent — FAISS + SentenceTransformers + Groq, working RAG pipeline
- ✅ Master Orchestrator — keyword routing + LLM fallback + conditional edges
- ✅ Multi-turn memory — InMemorySaver with thread_id
- ✅ Hinglish responses — working in production
- ✅ Gujarat scheme dataset — ~30 schemes from Ikhedut Portal
- ✅ Disease dataset — ~350 rows

**Needs to be built (production upgrade):**
- ❌ Refactor agents from notebook functions → proper LangGraph subgraphs in separate files
- ❌ Replace plain-text LLM routing → Pydantic structured output
- ❌ Replace InMemorySaver → PostgreSQL persistent checkpointer
- ❌ Crop Recommendation Agent (FAISS index from Kaggle CSV)
- ❌ Price Agent (AgMarkNet API tools + ToolNode graph)
- ❌ Human-in-the-loop safety gate with `interrupt()`
- ❌ Token streaming with `astream_events`
- ❌ Parallel execution with `Send` API
- ❌ FastAPI server with streaming endpoint
- ❌ LangSmith tracing integration
- ❌ Data collection scripts to expand scheme and disease datasets
- ❌ Docker deployment

---

### Folder Structure (Target)

```
kisaanai/
├── kisaanai/
│   ├── state/          → TypedDict state definitions for all graphs
│   ├── agents/         → disease_agent.py, scheme_agent.py, crop_rec_agent.py, price_agent.py
│   ├── orchestrator/   → master graph, intent classifier, routing logic
│   ├── rag/            → FAISS index builder, embedder, document loader
│   ├── memory/         → checkpointer setup (dev + prod)
│   └── tools/          → AgMarkNet tool, MyScheme tool, weather tool
├── api/                → FastAPI app with streaming + history endpoints
├── scripts/            → data collection, FAISS index building, validation
├── dataset/            → CSVs (schemes, diseases, crop_rec)
├── models/faiss_indexes/ → pre-built FAISS indexes (committed to repo)
├── notebooks/          → development notebooks including original models.ipynb
└── tests/              → agent unit tests + evaluation dataset
```

---

### Key Design Decisions & Why

| Decision | What Was Chosen | Why |
|----------|----------------|-----|
| LLM Provider | Groq (Llama 3.1) | Free tier, fastest inference, Hinglish works well |
| Routing method | Pydantic structured output | Never returns invalid route unlike plain text |
| Crop rec approach | FAISS over CSV (not sklearn model) | No training pipeline, immediate setup, LLM explains reasoning |
| Price approach | Live API + stats (not ML forecast) | Always current, no retraining, honest uncertainty |
| Memory | PostgreSQL checkpointer | Conversations survive restarts, farmer-specific history |
| Language | Hinglish output | Farmers in Gujarat/Maharashtra comfortable with this mix |
| Embeddings | all-MiniLM-L6-v2 | Fast, small (90MB), works offline, good multilingual support |

---

### How to Give This File to an AI Model

When starting a new conversation about this project with any AI model (Claude, GPT-4, Gemini, etc.), paste the content from **this entire MASTER CONTEXT BLOCK section** (everything between the two `---` lines above). The AI model will have complete context about:
- What the project does and why
- All 4 agents and how they work
- Which LangGraph concepts are used where
- What is already built vs. what needs building
- Where all data comes from
- Every architectural decision and its rationale

This avoids repeating yourself across conversations and ensures the AI gives advice consistent with your existing architecture.

---

> **A production-ready, LangGraph-native, multi-agent AI system for Indian farmers**  
> Every LangGraph concept covered. Dataset sources included. Deployment-grade architecture.

> ### 🚫 No ML Models Required
> All four agents work **without any pre-trained machine learning models**.
>
> | Agent | Approach | What you need |
> |-------|----------|---------------|
> | Disease Agent | RAG (FAISS + LLM) | Disease CSV (you already have it) |
> | Scheme Agent | RAG + Tool Calling | Scheme CSV + free data.gov.in API key |
> | Crop Recommendation | RAG-as-Classifier (FAISS + LLM reasoning) | Free Kaggle CSV download |
> | Price Agent | Live API + Stats + LLM | Free data.gov.in API key |
>
> The Crop Recommendation Agent uses the **Kaggle dataset as a knowledge base** searched by FAISS — no sklearn/XGBoost training needed. The Price Agent uses **arithmetic trend statistics** (7-day moving average) + LLM seasonal reasoning — no ARIMA or LSTM needed.

---

## Table of Contents

- [📋 MASTER CONTEXT BLOCK](#-master-context-block) ← **Start here. Paste this into any AI model.**
1. [Project Vision](#1-project-vision)
2. [Current Implementation Analysis](#2-current-implementation-analysis)
3. [Production Architecture Overview](#3-production-architecture-overview)
4. [LangGraph Concepts Coverage Map](#4-langgraph-concepts-coverage-map)
5. [Dataset Acquisition — Complete Guide](#5-dataset-acquisition--complete-guide)
6. [State Design — The Foundation](#6-state-design)
7. [Agent Deep Dives](#7-agent-deep-dives)
8. [Orchestrator & Routing Graph](#8-orchestrator--routing-graph)
9. [LangGraph Advanced Patterns](#9-langgraph-advanced-patterns)
10. [Project Structure](#10-project-structure)
11. [Tech Stack & Dependencies](#11-tech-stack--dependencies)
12. [API Layer — FastAPI Backend](#12-api-layer)
13. [Deployment Strategy](#13-deployment-strategy)
14. [Evaluation & Monitoring](#14-evaluation--monitoring)
15. [Roadmap & Milestones](#15-roadmap--milestones)

---

## 1. Project Vision

KisaanAI 2.0 is a **production-grade agricultural intelligence system** that acts as a digital farming advisor for Indian farmers. The system answers questions in Hindi, Hinglish, and English — making AI accessible to farmers who may not be comfortable with formal English.

### Core Questions KisaanAI Answers

```
"Mere fasal mein kya bimari hai?" → Disease Agent
"Sarkar ki koi yojana hai?"       → Scheme Agent
"Kaunsi fasal ugaoon is mausam?"  → Crop Recommendation Agent
"Aaj mandi mein rate kya hai?"    → Price Prediction Agent
```

### What Makes This Production-Ready

| Aspect | Basic (Current) | Production (Target) |
|--------|-----------------|---------------------|
| Memory | InMemorySaver (lost on restart) | PostgreSQL/Redis persistent checkpointer |
| Routing | Keyword + simple LLM | Structured LLM output + semantic fallback |
| State | Simple TypedDict | Rich TypedDict with full audit trail |
| Deployment | Jupyter notebook | FastAPI + Docker + LangGraph Platform |
| Streaming | Not implemented | Token-level streaming via SSE |
| Monitoring | None | LangSmith tracing + custom metrics |
| Error Handling | Minimal | Retry nodes, graceful fallback agents |
| Human-in-loop | Not implemented | Interrupt + review for critical advice |

---

## 2. Current Implementation Analysis

### What You've Built (models.ipynb)

Your notebook already has a solid foundation:

```
✅ Scheme Agent (Gujarat Ikhedut Portal data, FAISS + SentenceTransformers + Groq)
✅ Disease Agent (crop disease CSV, FAISS + embeddings + Groq)
✅ Master Orchestrator (keyword routing → LLM fallback → conditional edges)
✅ Conversation memory (InMemorySaver with thread_id)
✅ Hinglish output from LLM
✅ Multi-turn context (follow-up questions work)
```

### What's Missing for Production

```
❌ Proper dataset (current disease data is small; scheme data is only Gujarat)
❌ Persistent checkpointer (conversations lost on restart)
❌ Streaming responses (farmers on slow connections need token streaming)
❌ Human-in-the-loop (interrupt before sending medical advice)
❌ Subgraph architecture (agents are functions, not independent subgraphs)
❌ Parallel agent execution (Send API for multi-agent fanout)
❌ Structured routing output (LLM should return JSON, not plain text)
❌ Tool-calling nodes (ToolNode pattern for web search, mandi API)
❌ Crop Recommendation Agent (not built yet)
❌ Price Prediction Agent (not built yet)
❌ API layer (no FastAPI/deployment)
❌ Error handling & retry logic
❌ LangSmith integration
```

---

## 3. Production Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                        │
│  WhatsApp Bot | Web App | Mobile App | Voice (future)              │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────────────────────────┐
│                    FASTAPI GATEWAY LAYER                            │
│  /chat (streaming SSE)  |  /chat/invoke  |  /health                │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATION LAYER                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               MASTER ORCHESTRATOR GRAPH                      │  │
│  │                                                              │  │
│  │  [START] → [language_detect] → [intent_classify]            │  │
│  │               ↓                        ↓                    │  │
│  │        [query_rewrite]       [Conditional Router]           │  │
│  │                              ↙  ↙   ↘  ↘                   │  │
│  │  [disease_subgraph] [scheme_subgraph]                       │  │
│  │  [crop_rec_subgraph] [price_subgraph]                       │  │
│  │              ↘  ↘   ↙  ↙                                    │  │
│  │           [response_formatter] → [END]                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │Disease Agent│ │Scheme Agent │ │Crop Rec.   │ │Price Predict │  │
│  │ (Subgraph)  │ │ (Subgraph)  │ │ (Subgraph) │ │ (Subgraph)   │  │
│  └─────────────┘ └─────────────┘ └────────────┘ └──────────────┘  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     PERSISTENCE LAYER                               │
│  PostgreSQL (checkpointer)  |  Redis (cache)  |  S3 (FAISS index)  │
└─────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     EXTERNAL SERVICES                               │
│  Groq API (LLM)  |  AgMarkNet API (prices)  |  LangSmith (traces)  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. LangGraph Concepts Coverage Map

This table maps every LangGraph concept to where it is used in KisaanAI:

| LangGraph Concept | Used In | Why |
|---|---|---|
| `StateGraph` | All agents + orchestrator | Foundation of every graph |
| `TypedDict` State | `KisaanAIState`, `AgentState` | Structured state management |
| `Annotated` + `add_messages` reducer | Message history in all states | Append-only message accumulation |
| Custom state reducer | `retrieved_docs`, `confidence_scores` | Merge docs from multiple agents |
| `add_node` | Every node in every graph | Register processing functions |
| `add_edge` (direct) | Sequential steps within agents | Fixed processing order |
| `add_conditional_edges` | Orchestrator routing | Dynamic agent selection |
| `START` / `END` constants | All graphs | Graph entry/exit points |
| `compile()` | All graphs | Finalize and validate graph |
| `InMemorySaver` checkpointer | Development/testing | Fast iteration |
| `AsyncPostgresSaver` checkpointer | Production | Persistent cross-session memory |
| `thread_id` config | Every invocation | Per-farmer conversation isolation |
| Subgraphs | Each agent is a compiled subgraph | Modularity + independent testing |
| `Send` API | Parallel multi-agent queries | Fan-out when query matches multiple agents |
| `Command` API | Human-in-the-loop resume | After human reviews critical advice |
| `interrupt()` | Before sending pesticide/medical advice | Safety checkpoint |
| `ToolNode` | Web search, mandi price API | Structured tool execution |
| `tools_condition` | After LLM tool calls | Route to tool execution or END |
| Streaming (`astream`) | FastAPI SSE endpoint | Token-by-token response to user |
| `stream_mode="updates"` | Debugging/monitoring | See each node's output |
| `stream_mode="messages"` | Frontend token streaming | Real-time UI updates |
| `MessagesState` | Simplified agent states | Built-in message reducer |
| `add_messages` | Orchestrator state | Proper message deduplication |
| Retry on node error | LLM call nodes | Handle Groq API rate limits |
| `RunnableConfig` | Thread ID, callbacks | Pass metadata through graph |
| LangSmith tracing | All graphs | Production observability |

---

## 5. Dataset Acquisition — Complete Guide

> **This section answers: "I have no data. How do I get it, right now, today?"**  
> Every method below is free. Every script is copy-paste ready. No manual data entry needed.

---

### Data Sources Overview

| Dataset | Target Size | Method | Time to Acquire | Cost |
|---------|-------------|--------|-----------------|------|
| Government Schemes | 500+ rows | Official API (myscheme.gov.in) | ~30 min | Free |
| Crop Diseases | 1,500+ rows | Kaggle CSV + LLM augmentation | ~2 hours | Free |
| Crop Recommendation | 2,200 rows | Direct Kaggle download | ~5 min | Free |
| Mandi Prices | Live / real-time | Free government API (data.gov.in) | ~15 min setup | Free |

---

### 5.1 Government Scheme Dataset

#### Step 1 — Use MyScheme.gov.in Official API (Easiest, Most Reliable)

MyScheme.gov.in is the **official Government of India portal** that aggregates 700+ schemes across all states. It has a public API — no API key needed, no registration.

```python
# scripts/collect_schemes.py
# Run this script ONCE to build your full scheme dataset
# pip install requests pandas

import requests
import pandas as pd
import time
import json
from datetime import date

# All Indian state codes for the API
STATES = {
    "GJ": "Gujarat", "MH": "Maharashtra", "RJ": "Rajasthan",
    "UP": "Uttar Pradesh", "HR": "Haryana", "KA": "Karnataka",
    "TN": "Tamil Nadu", "AP": "Andhra Pradesh", "MP": "Madhya Pradesh",
    "WB": "West Bengal", "PB": "Punjab", "OR": "Odisha",
    "BR": "Bihar", "AS": "Assam", "GH": "Jharkhand"
}

AGRICULTURE_KEYWORDS = [
    "farmer", "agriculture", "krishi", "kisan", "crop",
    "irrigation", "soil", "horticulture", "fishery", "livestock"
]

def fetch_schemes_by_state(state_code: str) -> list:
    """
    Fetch all agriculture schemes for a state from myscheme.gov.in
    No API key required — completely free public API
    """
    all_schemes = []
    
    for keyword in AGRICULTURE_KEYWORDS:
        url = "https://api.myscheme.gov.in/search/v4/schemes"
        params = {
            "keyword": keyword,
            "state": state_code,
            "lang": "en",
            "limit": 100
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                schemes = data.get("data", {}).get("schemes", [])
                all_schemes.extend(schemes)
                print(f"  {state_code} + '{keyword}': {len(schemes)} schemes")
        except Exception as e:
            print(f"  Failed {state_code}/{keyword}: {e}")
        time.sleep(0.5)  # Be polite to the API
    
    return all_schemes

def parse_scheme(raw: dict, state_name: str) -> dict:
    """
    Extract and flatten fields from the API response.
    Field names may vary — this handles the most common structure.
    """
    return {
        "scheme_id":           raw.get("schemeId", ""),
        "scheme_name":         raw.get("schemeName", raw.get("title", "")),
        "state":               state_name,
        "ministry":            raw.get("nodeName", raw.get("ministry", "")),
        "category":            raw.get("tag", ""),
        "scheme_details":      raw.get("schemeShortTitle", raw.get("description", "")),
        "benefits":            raw.get("benefit", ""),
        "eligibility":         raw.get("eligibility", ""),
        "application_process": raw.get("applicationProcess", ""),
        "documents_required":  json.dumps(raw.get("documents", [])),
        "url":                 raw.get("schemeUrl", raw.get("url", "")),
        "is_active":           True,
        "last_verified":       str(date.today()),
        # Combined field for FAISS embedding
        "search_text": " ".join(filter(None, [
            raw.get("schemeName", ""),
            raw.get("schemeShortTitle", ""),
            raw.get("benefit", ""),
            raw.get("eligibility", ""),
            state_name
        ]))
    }

def build_scheme_dataset():
    all_rows = []
    seen_ids = set()
    
    for state_code, state_name in STATES.items():
        print(f"\nFetching schemes for {state_name}...")
        schemes = fetch_schemes_by_state(state_code)
        
        for raw in schemes:
            sid = raw.get("schemeId", raw.get("title", ""))
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                all_rows.append(parse_scheme(raw, state_name))
    
    df = pd.DataFrame(all_rows)
    df = df[df["scheme_name"].str.len() > 5]  # Remove empty rows
    df.drop_duplicates(subset=["scheme_name", "state"], inplace=True)
    
    df.to_csv("dataset/schemes_india.csv", index=False, encoding="utf-8")
    print(f"\n✅ Saved {len(df)} unique schemes to dataset/schemes_india.csv")
    return df

if __name__ == "__main__":
    df = build_scheme_dataset()
    print(df[["scheme_name", "state", "benefits"]].head(10))
```

#### Step 2 — Supplement with Your Existing Gujarat Data

You already have ~20-30 Gujarat Ikhedut schemes in your notebook. Merge them:

```python
# scripts/merge_existing_data.py
import pandas as pd

# Load your existing notebook data (export to CSV first)
existing = pd.read_csv("dataset/Book(Sheet1).csv", encoding="latin1")
existing_clean = pd.DataFrame({
    "scheme_name":         existing["Scheme Name"],
    "state":               "Gujarat",
    "scheme_details":      existing["Scheme Details"],
    "benefits":            existing["Benifits"],
    "eligibility":         existing["Elligibility"],
    "application_process": existing["Application processs"],
    "documents_required":  existing["documents required"],
    "url":                 existing["url"],
    "is_active":           True,
    "search_text": existing["Scheme Name"].fillna("") + " " +
                   existing["Benifits"].fillna("") + " " +
                   existing["Elligibility"].fillna("")
})

# Load API data + merge
api_data = pd.read_csv("dataset/schemes_india.csv")
merged = pd.concat([api_data, existing_clean], ignore_index=True)
merged.drop_duplicates(subset=["scheme_name"], inplace=True)

merged.to_csv("dataset/schemes_india_final.csv", index=False)
print(f"Final scheme count: {len(merged)}")
```

#### Step 3 — LLM Gap-Filler for Missing Fields

Sometimes the API returns schemes with empty `application_process` or `documents_required`. Fill them with LLM:

```python
# scripts/fill_scheme_gaps.py
from langchain_groq import ChatGroq
import pandas as pd

llm = ChatGroq(model="llama-3.1-8b-instant")  # Fast + cheap model for this

df = pd.read_csv("dataset/schemes_india_final.csv")
empty_process = df[df["application_process"].isna() | (df["application_process"] == "")]

print(f"Filling gaps for {len(empty_process)} schemes...")

for idx, row in empty_process.iterrows():
    prompt = f"""
    For this Indian government agricultural scheme, generate a realistic 
    step-by-step application process. Be specific and practical.
    
    Scheme: {row['scheme_name']}
    State: {row['state']}
    Benefits: {row['benefits']}
    
    Return ONLY the steps, no preamble. Start with "Step 1:".
    """
    try:
        result = llm.invoke(prompt).content
        df.at[idx, "application_process"] = result
    except Exception as e:
        print(f"  Skipped {row['scheme_name']}: {e}")

df.to_csv("dataset/schemes_india_final.csv", index=False)
print("Done filling gaps.")
```

---

### 5.2 Crop Disease Dataset

#### Method A — Download from Kaggle (Fastest — Use This First)

These datasets are ready to download right now:

```bash
# Install Kaggle CLI
pip install kaggle

# Set up Kaggle credentials:
# 1. Go to kaggle.com → Account → Create API Token → downloads kaggle.json
# 2. Place it at ~/.kaggle/kaggle.json (Linux/Mac) or C:\Users\YOU\.kaggle\kaggle.json (Windows)

# Dataset 1 — Plant Disease (38 crops, 87,000+ images, includes disease metadata)
kaggle datasets download -d vipoooool/new-plant-diseases-dataset

# Dataset 2 — Crop Disease Information (structured text, 50+ crops)
kaggle datasets download -d mexwell/crop-disease-information

# Dataset 3 — Rice Leaf Disease (specific, detailed)
kaggle datasets download -d tedisetiadi/rice-leaf-disease

# Dataset 4 — Indian Crop Disease (closest to your use case)
kaggle datasets download -d nirmalsankalana/crop-disease-image-dataset
```

> **No Kaggle account?** Go to `kaggle.com/datasets/mexwell/crop-disease-information` → "Download" button → no login needed for small CSVs.

#### Method B — Hugging Face Datasets (No CLI Needed, Just pip)

```python
# pip install datasets
from datasets import load_dataset

# PlantVillage — 54,000 images but also has structured disease metadata
dataset = load_dataset("sasha/plantvillage", split="train")
# Extract unique disease names and crop names from the dataset
disease_df = pd.DataFrame({
    "crop": [d["label"].split("___")[0].replace("_", " ") for d in dataset],
    "disease_name": [d["label"].split("___")[1].replace("_", " ") for d in dataset],
})
disease_df = disease_df.drop_duplicates()
print(disease_df.head(20))
```

#### Method C — LLM Synthetic Generation (The Most Powerful Method)

This is the main data generation approach for this project. You use Groq's free tier to generate hundreds of rich, structured disease records in a few hours.

```python
# scripts/generate_disease_dataset.py
# This script generates your ENTIRE disease dataset using LLM
# Groq free tier: 14,400 requests/day — enough for 500+ disease records

import json
import pandas as pd
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.2)

# ── SEED DATA: Crop × Disease combinations to generate ──
# These are real combinations from agricultural literature
CROP_DISEASE_SEEDS = [
    # Format: (crop_english, crop_hindi, disease_name, severity)
    # WHEAT (Gehun)
    ("Wheat", "गेहूं", "Yellow Rust",           "high"),
    ("Wheat", "गेहूं", "Brown Rust",             "medium"),
    ("Wheat", "गेहूं", "Loose Smut",             "medium"),
    ("Wheat", "गेहूं", "Powdery Mildew",         "low"),
    ("Wheat", "गेहूं", "Karnal Bunt",            "high"),
    ("Wheat", "गेहूं", "Root Rot",               "high"),
    # RICE (Chawal/Dhan)
    ("Rice",  "धान",  "Blast",                   "critical"),
    ("Rice",  "धान",  "Brown Spot",              "medium"),
    ("Rice",  "धान",  "Bacterial Leaf Blight",   "high"),
    ("Rice",  "धान",  "Sheath Blight",           "high"),
    ("Rice",  "धान",  "False Smut",              "medium"),
    ("Rice",  "धान",  "Neck Rot",                "high"),
    # TOMATO (Tamatar)
    ("Tomato","टमाटर","Early Blight",            "medium"),
    ("Tomato","टमाटर","Late Blight",             "critical"),
    ("Tomato","टमाटर","Leaf Curl Virus",         "high"),
    ("Tomato","टमाटर","Fusarium Wilt",           "critical"),
    ("Tomato","टमाटर","Bacterial Canker",        "high"),
    ("Tomato","टमाटर","Damping Off",             "medium"),
    # COTTON (Kapas)
    ("Cotton","कपास","Bacterial Blight",         "high"),
    ("Cotton","कपास","Alternaria Leaf Spot",     "medium"),
    ("Cotton","कपास","Root Rot",                 "critical"),
    ("Cotton","कपास","Fusarium Wilt",            "critical"),
    ("Cotton","कपास","Pink Bollworm",            "high"),
    # MAIZE (Makka)
    ("Maize", "मक्का","Downy Mildew",            "high"),
    ("Maize", "मक्का","Leaf Blight",             "medium"),
    ("Maize", "मक्का","Stalk Rot",               "high"),
    ("Maize", "मक्का","Northern Corn Leaf Blight","medium"),
    # POTATO (Aloo)
    ("Potato","आलू",  "Late Blight",             "critical"),
    ("Potato","आलू",  "Early Blight",            "medium"),
    ("Potato","आलू",  "Black Scurf",             "low"),
    ("Potato","आलू",  "Common Scab",             "low"),
    # GROUNDNUT (Moongfali)
    ("Groundnut","मूंगफली","Tikka Leaf Spot",    "high"),
    ("Groundnut","मूंगफली","Rust",               "medium"),
    ("Groundnut","मूंगफली","Stem Rot",           "critical"),
    ("Groundnut","मूंगफली","Collar Rot",         "high"),
    # SUGARCANE (Ganna)
    ("Sugarcane","गन्ना","Red Rot",              "critical"),
    ("Sugarcane","गन्ना","Smut",                 "high"),
    ("Sugarcane","गन्ना","Wilt",                 "high"),
    ("Sugarcane","गन्ना","Grassy Shoot Disease", "medium"),
    # SOYBEAN (Soya)
    ("Soybean","सोयाबीन","Rust",                 "high"),
    ("Soybean","सोयाबीन","Charcoal Rot",         "critical"),
    ("Soybean","सोयाबीन","Yellow Mosaic Virus",  "high"),
    # ONION (Pyaz)
    ("Onion",  "प्याज","Purple Blotch",          "medium"),
    ("Onion",  "प्याज","Stemphylium Blight",     "medium"),
    ("Onion",  "प्याज","Fusarium Basal Rot",     "high"),
    # MANGO (Aam)
    ("Mango",  "आम",  "Powdery Mildew",          "medium"),
    ("Mango",  "आम",  "Anthracnose",             "high"),
    ("Mango",  "आम",  "Mango Malformation",      "high"),
    ("Mango",  "आम",  "Bacterial Canker",        "high"),
    # CHILLI (Mirchi)
    ("Chilli", "मिर्ची","Anthracnose",           "high"),
    ("Chilli", "मिर्ची","Leaf Curl",             "high"),
    ("Chilli", "मिर्ची","Powdery Mildew",        "medium"),
    # BAJRA / PEARL MILLET
    ("Pearl Millet","बाजरा","Downy Mildew",      "critical"),
    ("Pearl Millet","बाजरा","Rust",              "medium"),
    ("Pearl Millet","बाजरा","Smut",              "medium"),
    # MUSTARD (Sarso)
    ("Mustard","सरसों","White Rust",             "medium"),
    ("Mustard","सरसों","Alternaria Blight",      "high"),
    ("Mustard","सरसों","Downy Mildew",           "medium"),
]

SYSTEM_PROMPT = """
You are an agricultural expert AI. Generate disease data for Indian farmers.
You MUST return ONLY a valid JSON object — no preamble, no explanation, no markdown.
All text must be accurate agronomic information. Be specific with chemical names and doses.
"""

def generate_one_record(crop_en, crop_hi, disease, severity):
    prompt = f"""
Generate a complete disease record for:
- Crop: {crop_en} ({crop_hi})
- Disease: {disease}
- Severity: {severity}

Return ONLY this JSON structure (no other text):
{{
    "farmer_symptoms": "Simple Hinglish description of what farmer sees (2-3 sentences)",
    "farmer_symptoms_hindi": "Same symptoms in pure Hindi",
    "technical_symptoms": "Pathological/technical description for agronomists",
    "treatment": "Specific fungicide/pesticide with exact dose (e.g., Mancozeb 2g per litre water)",
    "treatment_products": "2-3 specific product names available in Indian market",
    "prevention": "3-4 prevention methods, practical for Indian farmers",
    "recovery_time": "Expected recovery duration (e.g., '2-3 weeks')",
    "affected_regions": "Indian states/regions most affected",
    "season": "kharif / rabi / zaid / all",
    "image_description": "What this disease looks like visually (for future image detection)"
}}
"""
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    return json.loads(response.content)

def generate_full_dataset(seeds=CROP_DISEASE_SEEDS, output_path="dataset/diseases_india.csv"):
    """
    Generates 1 record per seed. At 50+ seeds above = 50+ records.
    Run multiple times with more seeds to build up to 500+.
    Groq free tier: 14,400 req/day → can generate ~1000 records per day.
    """
    records = []
    failed = []
    
    for i, (crop_en, crop_hi, disease, severity) in enumerate(seeds):
        print(f"[{i+1}/{len(seeds)}] Generating: {crop_en} — {disease}")
        try:
            record = generate_one_record(crop_en, crop_hi, disease, severity)
            record.update({
                "crop": crop_en,
                "crop_hindi": crop_hi,
                "disease_name": disease,
                "severity": severity,
                "search_text": f"{crop_en} {disease} {record.get('farmer_symptoms','')} {record.get('treatment','')}",
                "source": "llm_generated",
                "verified": False  # Mark for expert review
            })
            records.append(record)
            
            # Save after every 10 records (in case of crash)
            if (i + 1) % 10 == 0:
                pd.DataFrame(records).to_csv(output_path, index=False)
                print(f"  💾 Checkpoint saved — {len(records)} records so far")
            
            time.sleep(0.3)  # Respect rate limits
            
        except Exception as e:
            print(f"  ❌ Failed: {crop_en} / {disease} — {e}")
            failed.append((crop_en, disease, str(e)))
    
    # Final save
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✅ Generated {len(df)} disease records → {output_path}")
    if failed:
        print(f"⚠️  {len(failed)} failed — retry these: {failed}")
    return df

if __name__ == "__main__":
    # Step 1: Merge your existing CSV with new generated data
    existing = pd.read_csv("dataset/your_existing_disease_data.csv")
    
    # Step 2: Generate new records for crops not in your existing data
    new_df = generate_full_dataset()
    
    # Step 3: Merge and deduplicate
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["crop", "disease_name"], inplace=True)
    combined.to_csv("dataset/diseases_india_final.csv", index=False)
    print(f"Final: {len(combined)} unique crop-disease combinations")
```

> ⚠️ **Important about synthetic data**: Mark all LLM-generated records as `verified=False`. For production, get a KVK agronomist to review 20-30 random records to validate the chemical names and doses are correct. Wrong pesticide advice can harm farmers.

#### Method D — Combine with Your Existing Data

Your notebook already has ~350 disease records. These are real, verified data — **keep them as your gold standard**. The LLM data supplements gaps.

```python
# Check what crops you already have covered
existing = pd.read_csv("your_existing_disease_data.csv")
covered = set(existing["Crop"].unique())
print("Already covered:", covered)

# Only generate for crops NOT already in your data
seeds_to_generate = [
    (crop, crop_hi, disease, sev)
    for crop, crop_hi, disease, sev in CROP_DISEASE_SEEDS
    if crop not in covered
]
print(f"Will generate for: {len(seeds_to_generate)} new crop-disease pairs")
```

---

### 5.3 Crop Recommendation Dataset

This is the **simplest dataset to get** — it already exists on Kaggle, perfectly clean, 2,200 rows.

#### Download (3 ways)

**Way 1 — Direct browser download (no account needed)**
```
Go to: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset
Click: "Download" button → Crop_recommendation.csv
Put it in: dataset/crop_recommendation.csv
```

**Way 2 — Kaggle CLI**
```bash
pip install kaggle
# Place kaggle.json in ~/.kaggle/
kaggle datasets download -d atharvaingle/crop-recommendation-dataset -p dataset/
unzip dataset/crop-recommendation-dataset.zip -d dataset/
```

**Way 3 — Python direct (no Kaggle account)**
```python
# scripts/download_crop_data.py
import requests, zipfile, io, os

# Alternative mirrors on GitHub (many people re-host this dataset)
MIRRORS = [
    "https://raw.githubusercontent.com/Gladiator07/Harvestify/master/Data-raw/crop_recommendation.csv",
    "https://raw.githubusercontent.com/dsrscientist/dataset1/master/crop_recommendation.csv",
]

for url in MIRRORS:
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            os.makedirs("dataset", exist_ok=True)
            with open("dataset/crop_recommendation.csv", "wb") as f:
                f.write(resp.content)
            print("✅ Downloaded crop_recommendation.csv")
            break
    except:
        continue
```

#### What the Dataset Looks Like

```
N     P     K   temperature  humidity  ph    rainfall  label
90    42    43   20.87        82.0      6.5   202.9     rice
85    58    41   21.77        80.3      7.0   226.6     rice
60    55    44   23.00        82.3      7.8   263.9     rice
74    35    40   26.49        80.1      6.9   242.8     rice
...
```

22 crops covered: rice, maize, chickpea, kidneybeans, pigeonpeas, mothbeans, mungbean, blackgram, lentil, pomegranate, banana, mango, grapes, watermelon, muskmelon, apple, orange, papaya, coconut, cotton, jute, coffee.

#### Build FAISS Index from This CSV (one-time setup)

```python
# scripts/build_crop_rec_index.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, json

df = pd.read_csv("dataset/crop_recommendation.csv")

# Convert each row to searchable text — this is the key step
df["search_text"] = df.apply(lambda r:
    f"N={r['N']:.0f} P={r['P']:.0f} K={r['K']:.0f} "
    f"temperature={r['temperature']:.1f} humidity={r['humidity']:.0f} "
    f"ph={r['ph']:.1f} rainfall={r['rainfall']:.0f} crop={r['label']}", axis=1
)

model = SentenceTransformer("all-MiniLM-L6-v2")
print("Encoding 2,200 crop records...")
embeddings = model.encode(df["search_text"].tolist(), show_progress_bar=True)
embeddings = np.array(embeddings, dtype="float32")

import os
os.makedirs("models/faiss_indexes", exist_ok=True)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "models/faiss_indexes/crop_rec.index")
df.to_json("models/faiss_indexes/crop_rec_metadata.json", orient="records")
print(f"✅ Crop rec FAISS index built — {len(df)} records")
```

---

### 5.4 Mandi Price Data

Price data is **live** — you fetch it at query time, no static dataset needed.

#### Step 1 — Get Free data.gov.in API Key (5 minutes)

```
1. Go to: https://data.gov.in/
2. Click "Register" (top right)
3. Fill form with name, email, password
4. Verify email
5. Go to: https://data.gov.in/user → "API Keys" → Generate Key
6. Copy the key → add to .env as DATAGOV_API_KEY=your_key_here
```

#### Step 2 — Test the API

```python
# scripts/test_price_api.py
import requests, os
from dotenv import load_dotenv
load_dotenv()

def test_agmarknet(commodity="Tomato", state="Gujarat"):
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": os.getenv("DATAGOV_API_KEY"),
        "format": "json",
        "filters[State]": state,
        "filters[Commodity]": commodity,
        "limit": 5
    }
    resp = requests.get(url, params=params).json()
    records = resp.get("records", [])
    
    if records:
        print(f"✅ API working! Sample data for {commodity} in {state}:")
        for r in records[:3]:
            print(f"  {r.get('Market')}: Min ₹{r.get('Min_Price')} "
                  f"Max ₹{r.get('Max_Price')} Modal ₹{r.get('Modal_Price')}")
    else:
        print(f"⚠️  No data for {commodity}/{state}. Try different date or commodity name.")
        print("API response:", resp)

test_agmarknet()
```

#### Step 3 — Build a Small Historical Cache (Optional but Useful)

If you want offline price data for testing (so you don't need internet during dev):

```python
# scripts/cache_historical_prices.py
import requests, pandas as pd, time, os
from datetime import datetime, timedelta

API_KEY = os.getenv("DATAGOV_API_KEY")

# Top 20 commodities × last 30 days = ~600 API calls (takes ~5 min)
COMMODITIES = [
    "Tomato", "Onion", "Potato", "Wheat", "Rice", "Maize",
    "Cotton", "Soybean", "Groundnut", "Mustard", "Chilli",
    "Brinjal", "Cauliflower", "Cabbage", "Garlic", "Ginger",
    "Turmeric", "Coriander", "Cumin", "Bajra"
]

TARGET_STATES = ["Gujarat", "Maharashtra", "Rajasthan", "Uttar Pradesh", "Punjab"]

def fetch_prices_for_date(commodity, state, date_str):
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": API_KEY, "format": "json",
        "filters[State]": state,
        "filters[Commodity]": commodity,
        "filters[Arrival_Date]": date_str,
        "limit": 20
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json().get("records", [])

all_records = []
for commodity in COMMODITIES[:5]:   # Start with 5, expand later
    for state in TARGET_STATES[:2]: # Start with 2 states
        for days_ago in range(30):
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%b/%Y")
            records = fetch_prices_for_date(commodity, state, date)
            for r in records:
                r["commodity"] = commodity
                r["query_state"] = state
            all_records.extend(records)
            time.sleep(0.2)
        print(f"  Fetched {commodity}/{state}")

df = pd.DataFrame(all_records)
df.to_csv("dataset/mandi_prices_historical.csv", index=False)
print(f"✅ Cached {len(df)} price records")
```

---

### 5.5 Complete Data Pipeline — Run In This Order

```bash
# 1. Create dataset directory
mkdir -p dataset models/faiss_indexes

# 2. Download crop recommendation data (5 min, no account needed)
python scripts/download_crop_data.py

# 3. Merge your existing scheme data + fetch from MyScheme API (30 min)
python scripts/collect_schemes.py
python scripts/merge_existing_data.py

# 4. Generate disease dataset using LLM (2 hours, uses Groq free tier)
python scripts/generate_disease_dataset.py

# 5. Build FAISS indexes for all three RAG agents (15 min, one-time)
python scripts/build_faiss_index.py      # Schemes + Diseases
python scripts/build_crop_rec_index.py   # Crop recommendation

# 6. Test the price API (5 min)
python scripts/test_price_api.py

# Done! All 4 agents are now ready to run.
```

### 5.6 Data Quality Checklist

Before using any dataset in production, verify:

```python
# scripts/validate_datasets.py
import pandas as pd

def validate_schemes(path="dataset/schemes_india_final.csv"):
    df = pd.read_csv(path)
    print(f"Schemes: {len(df)} total")
    print(f"  States covered: {df['state'].nunique()}")
    print(f"  Missing scheme_name: {df['scheme_name'].isna().sum()}")
    print(f"  Missing benefits: {df['benefits'].isna().sum()}")
    print(f"  Empty search_text: {(df['search_text'].str.len() < 20).sum()}")
    assert len(df) > 100, "Too few scheme records"
    print("✅ Schemes dataset OK")

def validate_diseases(path="dataset/diseases_india_final.csv"):
    df = pd.read_csv(path)
    print(f"Diseases: {len(df)} total")
    print(f"  Crops covered: {df['crop'].nunique()}")
    print(f"  Missing treatment: {df['treatment'].isna().sum()}")
    print(f"  Unverified (LLM-generated): {(df.get('verified', True) == False).sum()}")
    assert len(df) > 50, "Too few disease records"
    print("✅ Disease dataset OK")

def validate_crop_rec(path="dataset/crop_recommendation.csv"):
    df = pd.read_csv(path)
    print(f"Crop rec: {len(df)} rows, {df['label'].nunique()} crops")
    assert len(df) >= 2200, "Crop rec dataset incomplete"
    print("✅ Crop rec dataset OK")

validate_schemes()
validate_diseases()
validate_crop_rec()
```

---

## 6. State Design — The Foundation

State is the most important design decision in LangGraph. Get this right first.

### 6.1 Master Orchestrator State

```python
# kisaanai/state.py
from typing import TypedDict, Annotated, Optional, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# Custom reducer for retrieved docs (merge, not overwrite)
def merge_docs(existing: list, new: list) -> list:
    """Merge retrieved docs, avoiding duplicates"""
    if not existing:
        return new
    existing_ids = {d.get("id") for d in existing}
    return existing + [d for d in new if d.get("id") not in existing_ids]

class OrchestratorState(TypedDict):
    # MESSAGES — uses LangGraph's built-in add_messages reducer
    # This APPENDS new messages instead of overwriting
    messages: Annotated[list[BaseMessage], add_messages]
    
    # ROUTING — which agent handles this query
    route: Optional[Literal["disease", "scheme", "crop_rec", "price", "general"]]
    
    # INTENT METADATA
    detected_language: Optional[str]      # "hindi", "hinglish", "english"
    query_rewritten: Optional[str]         # English version of query for FAISS
    confidence: Optional[float]            # Routing confidence 0-1
    
    # AGENT RESULTS
    retrieved_docs: Annotated[list[dict], merge_docs]
    agent_response: Optional[str]
    
    # HUMAN-IN-THE-LOOP
    requires_human_review: Optional[bool]  # Trigger for interrupt
    review_reason: Optional[str]           # Why review is needed
    human_approved: Optional[bool]         # Result of review
    
    # AUDIT TRAIL
    session_id: Optional[str]             # farmer's session
    farmer_id: Optional[str]              # persistent farmer ID
    timestamp: Optional[str]
    nodes_visited: Annotated[list[str], lambda x, y: x + y]  # Track execution path
```

### 6.2 Individual Agent State (Subgraph State)

```python
class AgentState(TypedDict):
    """Shared state for all agent subgraphs"""
    messages: Annotated[list[BaseMessage], add_messages]
    query: str                         # The specific query for this agent
    retrieved_docs: list[dict]         # Top-k retrieved documents
    response: Optional[str]            # Final generated response
    retrieval_scores: list[float]      # FAISS similarity scores
    fallback_triggered: bool           # True if RAG failed → LLM general knowledge
```

### 6.3 Why This State Design Matters

```python
# BAD — simple dict, loses message history
state = {"query": "...", "response": "..."}

# GOOD — add_messages reducer APPENDS, never overwrites
# Turn 1: messages = [HumanMessage("What is PM Kisan?")]
# Turn 2: messages = [HumanMessage("What is PM Kisan?"), 
#                     AIMessage("PM Kisan is..."), 
#                     HumanMessage("Documents needed?")]
# The full history is preserved automatically!
```

---

## 7. Agent Deep Dives

### 7.1 Disease Agent Subgraph (Refactored)

```
[START] → [embed_query] → [faiss_search] → [validate_results] 
       → [generate_response] → [safety_check] → [END]
```

```python
# kisaanai/agents/disease_agent.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

def build_disease_agent(faiss_index, embedder, llm) -> CompiledGraph:
    
    def embed_query(state: AgentState) -> dict:
        """Node 1: Convert query to vector"""
        query = state["messages"][-1].content
        # Rewrite to English if Hinglish (better FAISS performance)
        english_query = translate_to_english(query, llm) if detect_non_english(query) else query
        embedding = embedder.encode([english_query])
        return {"query": english_query, "embedding": embedding}
    
    def faiss_search(state: AgentState) -> dict:
        """Node 2: Retrieve top-k disease records"""
        scores, indices = faiss_index.search(state["embedding"], k=5)
        docs = [disease_df.iloc[i].to_dict() for i in indices[0] if i != -1]
        return {
            "retrieved_docs": docs,
            "retrieval_scores": scores[0].tolist()
        }
    
    def validate_results(state: AgentState) -> dict:
        """Node 3: Check if retrieved docs are relevant"""
        max_score = max(state["retrieval_scores"]) if state["retrieval_scores"] else 0
        # Cosine similarity threshold — tune this
        if max_score < 0.3:
            return {"fallback_triggered": True}
        return {"fallback_triggered": False}
    
    def generate_response(state: AgentState) -> dict:
        """Node 4: LLM generates farmer-friendly response"""
        if state.get("fallback_triggered"):
            context = "Koi specific disease record nahi mila. General farming knowledge se jawab do."
        else:
            context = "\n\n".join([
                f"Fasal: {d['crop']}\nBimari: {d['disease_name']}\n"
                f"Lakshan: {d['farmer_symptoms']}\nIlaaj: {d['treatment']}\n"
                f"Bachav: {d['prevention']}\nSamay: {d['recovery_time']}"
                for d in state["retrieved_docs"][:3]
            ])
        
        system = """
        Tum KisaanAI ho — Indian farmers ke liye ek expert agricultural AI assistant.
        
        Rules:
        1. Jawab Hinglish mein do (Hindi + English mix) — simple aur seedha
        2. Sirf diye gaye context se jawab do
        3. Agar kuch pata nahi, clearly batao
        4. Chemical names ke saath dose bhi batao (e.g., "Mancozeb 2g/L paani")
        5. Hamesha "Doctor/KVK se verify karo" mention karo for serious diseases
        
        Context:
        {context}
        """.format(context=context)
        
        response = llm.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [AIMessage(content=response.content)], "response": response.content}
    
    def safety_check(state: AgentState) -> dict:
        """Node 5: Flag responses that need expert review"""
        dangerous_keywords = ["systemic fungicide", "highly toxic", "Class I pesticide", "restricted use"]
        response = state.get("response", "")
        needs_review = any(kw.lower() in response.lower() for kw in dangerous_keywords)
        return {"requires_human_review": needs_review}
    
    # Build the subgraph
    graph = StateGraph(AgentState)
    graph.add_node("embed_query", embed_query)
    graph.add_node("faiss_search", faiss_search)
    graph.add_node("validate_results", validate_results)
    graph.add_node("generate_response", generate_response)
    graph.add_node("safety_check", safety_check)
    
    graph.add_edge(START, "embed_query")
    graph.add_edge("embed_query", "faiss_search")
    graph.add_edge("faiss_search", "validate_results")
    graph.add_edge("validate_results", "generate_response")
    graph.add_edge("generate_response", "safety_check")
    graph.add_edge("safety_check", END)
    
    return graph.compile()
```

### 7.2 Scheme Agent Subgraph (Refactored + Enhanced)

New addition: **Tool calling** for live scheme status check

```python
# kisaanai/agents/scheme_agent.py
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def check_scheme_deadline(scheme_name: str) -> str:
    """Check if a government scheme is still accepting applications.
    Use when farmer asks 'kya abhi apply kar sakte hain' or deadline questions."""
    # Call MyScheme API or return from cache
    response = requests.get(f"https://api.myscheme.gov.in/schemes/{scheme_name}/status")
    return response.json().get("status", "Status unavailable")

@tool  
def calculate_subsidy_amount(scheme_name: str, farmer_category: str, item_cost: float) -> str:
    """Calculate exact subsidy amount for a farmer.
    farmer_category: general / SC / ST / small / marginal"""
    # Lookup subsidy rates from dataset
    rate = SUBSIDY_RATES.get((scheme_name, farmer_category), 0.5)
    amount = min(item_cost * rate, MAX_SUBSIDY.get(scheme_name, 100000))
    return f"Aapko approximately ₹{amount:,.0f} ka subsidy milega ({rate*100:.0f}% of ₹{item_cost:,.0f})"

tools = [check_scheme_deadline, calculate_subsidy_amount]
tool_node = ToolNode(tools)
llm_with_tools = llm.bind_tools(tools)

def llm_node(state: AgentState) -> dict:
    system = """You are KisaanAI's scheme expert. Help farmers understand government schemes.
    Use tools to check live deadlines and calculate subsidy amounts when asked."""
    response = llm_with_tools.invoke([SystemMessage(content=system)] + state["messages"])
    return {"messages": [response]}

# Graph with tool calling
graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieval_node)
graph.add_node("llm", llm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "llm")
graph.add_conditional_edges("llm", tools_condition)  # Routes to "tools" or END
graph.add_edge("tools", "llm")  # After tool execution, back to LLM
```

### 7.3 Crop Recommendation Agent (No ML Model Required)

> ✅ **No pre-trained ML model needed.** This agent uses a **RAG + Rule-Based + LLM reasoning** approach that works immediately with just a CSV dataset.

#### Why No ML Model?

Training a crop recommendation model requires labelled soil data from your target region, model validation, and deployment infrastructure. Instead, this approach uses the **Kaggle crop recommendation CSV (2,200 rows) as a searchable knowledge base** — each row is a reference example that the LLM reasons over. This actually gives *better explanations* than a black-box ML model because the LLM can see the matching examples and explain *why*.

#### How It Works

```
[START] 
   → [extract_params]      ← LLM pulls soil/weather from farmer's natural language
   → [fill_missing]        ← Rule-based: fill unknown params from state/season averages
   → [faiss_search]        ← Find top-10 similar crop records from the knowledge base
   → [rule_filter]         ← Hard filter: keep only crops valid for farmer's season/state
   → [llm_recommend]       ← LLM reasons over filtered examples → ranked recommendations
   → [END]
```

```python
# kisaanai/agents/crop_rec_agent.py
from pydantic import BaseModel, Field
from typing import Optional

# --- Pydantic model for structured param extraction ---
class SoilWeatherParams(BaseModel):
    N: Optional[float] = Field(None, description="Nitrogen in soil (ppm)")
    P: Optional[float] = Field(None, description="Phosphorus in soil (ppm)")
    K: Optional[float] = Field(None, description="Potassium in soil (ppm)")
    temperature: Optional[float] = Field(None, description="Avg temperature (°C)")
    humidity: Optional[float] = Field(None, description="Humidity (%)")
    ph: Optional[float] = Field(None, description="Soil pH (1-14)")
    rainfall: Optional[float] = Field(None, description="Annual rainfall (mm)")
    state: Optional[str] = Field(None, description="Indian state name")
    season: Optional[str] = Field(None, description="kharif / rabi / zaid")

# --- District/State average fallbacks (no ML needed) ---
# Source: ICAR soil health cards + IMD climate normals
STATE_AVERAGES = {
    "Gujarat":     {"N": 240, "P": 50,  "K": 200, "temperature": 27, "humidity": 58, "ph": 7.5, "rainfall": 800},
    "Maharashtra": {"N": 280, "P": 60,  "K": 220, "temperature": 26, "humidity": 65, "ph": 7.2, "rainfall": 900},
    "Punjab":      {"N": 300, "P": 80,  "K": 250, "temperature": 22, "humidity": 70, "ph": 7.8, "rainfall": 600},
    "Rajasthan":   {"N": 180, "P": 35,  "K": 160, "temperature": 30, "humidity": 40, "ph": 8.0, "rainfall": 400},
    "UP":          {"N": 260, "P": 55,  "K": 210, "temperature": 25, "humidity": 72, "ph": 7.6, "rainfall": 1000},
    # Add more states as needed
    "DEFAULT":     {"N": 250, "P": 55,  "K": 205, "temperature": 25, "humidity": 65, "ph": 7.5, "rainfall": 800},
}

# Season × State → crops that are physically possible (hard constraints)
SEASON_CROP_FILTER = {
    "kharif":  ["Rice", "Maize", "Cotton", "Soybean", "Groundnut", "Bajra", "Jowar", "Tur Dal"],
    "rabi":    ["Wheat", "Mustard", "Gram", "Lentil", "Potato", "Pea", "Barley"],
    "zaid":    ["Watermelon", "Muskmelon", "Cucumber", "Moong Dal", "Sugarcane"],
}

def build_crop_rec_agent(crop_faiss_index, crop_df, embedder, llm):
    
    # LLM with structured output for param extraction
    extractor_llm = llm.with_structured_output(SoilWeatherParams)
    
    def extract_params(state: AgentState) -> dict:
        """Node 1: Extract soil/weather from natural language query using structured LLM"""
        query = state["messages"][-1].content
        system = """
        You are extracting agricultural parameters from a farmer's query.
        Extract only what is explicitly mentioned. Use null for anything not stated.
        Common Hinglish mappings:
        - "mitti ka pH" → ph
        - "barish" → rainfall  
        - "garmi" → temperature
        - "nammi" → humidity
        """
        params = extractor_llm.invoke([SystemMessage(content=system), HumanMessage(content=query)])
        return {"extracted_params": params.model_dump()}
    
    def fill_missing_params(state: AgentState) -> dict:
        """Node 2: Fill null params using state/season averages — NO ML model needed"""
        params = state["extracted_params"].copy()
        state_name = params.get("state") or "DEFAULT"
        averages = STATE_AVERAGES.get(state_name, STATE_AVERAGES["DEFAULT"])
        
        # Only fill what is missing (null/None)
        for key, avg_val in averages.items():
            if params.get(key) is None:
                params[key] = avg_val
                params[f"{key}_is_estimated"] = True  # Flag so LLM knows this was estimated
        
        return {"extracted_params": params}
    
    def faiss_search_crops(state: AgentState) -> dict:
        """Node 3: Find similar crop records using FAISS
        
        The Kaggle dataset rows are embedded as text like:
        'N=90 P=42 K=43 temperature=20.8 humidity=82 ph=6.5 rainfall=202 → Rice'
        We embed the farmer's params the same way and find nearest neighbors.
        """
        p = state["extracted_params"]
        search_text = (
            f"N={p.get('N',250):.0f} P={p.get('P',55):.0f} K={p.get('K',205):.0f} "
            f"temperature={p.get('temperature',25):.1f} humidity={p.get('humidity',65):.0f} "
            f"ph={p.get('ph',7.5):.1f} rainfall={p.get('rainfall',800):.0f}"
        )
        embedding = embedder.encode([search_text])
        scores, indices = crop_faiss_index.search(embedding, k=15)
        
        similar_records = [crop_df.iloc[i].to_dict() for i in indices[0] if i != -1]
        return {
            "retrieved_docs": similar_records,
            "retrieval_scores": scores[0].tolist()
        }
    
    def rule_filter_crops(state: AgentState) -> dict:
        """Node 4: Hard filter — remove crops that can't grow this season
        This is pure rule-based logic, no model needed."""
        season = state["extracted_params"].get("season")
        docs = state["retrieved_docs"]
        
        if season and season in SEASON_CROP_FILTER:
            valid_crops = SEASON_CROP_FILTER[season]
            # Keep records matching season, but if nothing matches, keep all (don't over-filter)
            filtered = [d for d in docs if d.get("label", "") in valid_crops]
            docs = filtered if len(filtered) >= 3 else docs
        
        return {"retrieved_docs": docs}
    
    def llm_recommend(state: AgentState) -> dict:
        """Node 5: LLM reasons over retrieved examples to produce ranked recommendation.
        This replaces a predict_proba() call — the LLM IS the prediction engine."""
        p = state["extracted_params"]
        examples = state["retrieved_docs"][:10]
        
        # Count crop frequency in retrieved neighbors — simple voting
        from collections import Counter
        crop_votes = Counter(d.get("label", "") for d in examples)
        top_crops = crop_votes.most_common(5)
        
        estimated_fields = [k.replace("_is_estimated", "") 
                            for k, v in p.items() if k.endswith("_is_estimated") and v]
        
        system = f"""
        Tu KisaanAI ka crop expert hai. Ek farmer ke liye best crop recommend karo.

        Farmer ke parameters:
        - Nitrogen (N): {p.get('N')} ppm {"(estimated)" if 'N' in estimated_fields else ""}
        - Phosphorus (P): {p.get('P')} ppm {"(estimated)" if 'P' in estimated_fields else ""}
        - Potassium (K): {p.get('K')} ppm {"(estimated)" if 'K' in estimated_fields else ""}
        - Temperature: {p.get('temperature')}°C {"(estimated)" if 'temperature' in estimated_fields else ""}
        - Humidity: {p.get('humidity')}% {"(estimated)" if 'humidity' in estimated_fields else ""}
        - Soil pH: {p.get('ph')} {"(estimated)" if 'ph' in estimated_fields else ""}
        - Rainfall: {p.get('rainfall')} mm/year {"(estimated)" if 'rainfall' in estimated_fields else ""}
        - State: {p.get('state') or 'Not specified'}
        - Season: {p.get('season') or 'Not specified'}

        Similar farmers ke data mein in crops ka success hai: {top_crops}

        Karo:
        1. Top 3 crops recommend karo with reasons (soil/weather match explain karo)
        2. Agar koi parameter estimated hai, batao ki actual soil test se better results milenge
        3. Har crop ke liye estimated income/quintal bhi batao (current market se)
        4. Hinglish mein jawab do — simple language use karo

        Note: Ye recommendations general knowledge par based hain. 
        Apne local KVK (Krishi Vigyan Kendra) se confirm zaroor karein.
        """
        
        response = llm.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [AIMessage(content=response.content)], "response": response.content}
    
    # --- Build the subgraph ---
    graph = StateGraph(AgentState)
    graph.add_node("extract_params", extract_params)
    graph.add_node("fill_missing", fill_missing_params)
    graph.add_node("faiss_search", faiss_search_crops)
    graph.add_node("rule_filter", rule_filter_crops)
    graph.add_node("llm_recommend", llm_recommend)
    
    graph.add_edge(START, "extract_params")
    graph.add_edge("extract_params", "fill_missing")
    graph.add_edge("fill_missing", "faiss_search")
    graph.add_edge("faiss_search", "rule_filter")
    graph.add_edge("rule_filter", "llm_recommend")
    graph.add_edge("llm_recommend", END)
    
    return graph.compile()
```

#### Building the Crop FAISS Index (from Kaggle CSV)

```python
# scripts/build_crop_rec_index.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, json

df = pd.read_csv("dataset/crop_recommendation.csv")  # Kaggle dataset

# Convert each row into a searchable text string
# This is what gets embedded — no ML training needed, just FAISS similarity
df["search_text"] = df.apply(lambda r: 
    f"N={r['N']:.0f} P={r['P']:.0f} K={r['K']:.0f} "
    f"temperature={r['temperature']:.1f} humidity={r['humidity']:.0f} "
    f"ph={r['ph']:.1f} rainfall={r['rainfall']:.0f} crop={r['label']}", axis=1
)

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(df["search_text"].tolist(), show_progress_bar=True)
embeddings = np.array(embeddings, dtype="float32")

# Build FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "models/faiss_indexes/crop_rec.index")

# Save metadata
df.to_json("models/faiss_indexes/crop_rec_metadata.json", orient="records")
print(f"Built crop FAISS index with {len(df)} records")
```

### 7.4 Price Agent (No ML Model Required)

> ✅ **No time-series ML model needed.** This agent uses **live AgMarkNet API data + simple statistical trend analysis + LLM reasoning** about seasonal patterns. The LLM already knows historical price seasonality for Indian crops — we just give it live data to ground its reasoning.

#### Why No ML Model?

Price forecasting models (ARIMA, LSTM) require years of clean historical data, feature engineering, and frequent retraining. Instead, this agent:
1. Fetches **live prices** from the official free AgMarkNet API
2. Calculates **simple trend statistics** (7-day average, direction, % change) — just arithmetic, no model
3. Lets the **LLM reason** about whether to sell now or wait, using its existing knowledge of crop seasonality + the live stats as grounding

This is more honest and just as useful. A farmer asking "kab bechu?" gets a reasoning-based answer, not a falsely precise percentage.

#### Agent Flow

```
[START] 
   → [extract_intent]      ← What commodity? Which state? Sell-now or price-check?
   → [fetch_live_prices]   ← AgMarkNet API → today's min/max/modal price
   → [calculate_trend]     ← Last 7 days prices → direction + % change (pure math)
   → [fetch_season_context]← RAG: retrieve seasonal price pattern for this crop
   → [llm_advice]          ← LLM synthesizes all 3 signals → "sell now or wait"
   → [END]
```

```python
# kisaanai/agents/price_agent.py
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from datetime import datetime, timedelta
import requests, os, statistics

# ── Tools (called by LLM via ToolNode) ──

@tool
def get_current_mandi_price(commodity: str, state: str) -> str:
    """
    Fetch today's mandi (wholesale market) price for a crop.
    Use when farmer asks: 'aaj rate kya hai', 'mandi mein kya chal raha hai'
    """
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    today = datetime.now().strftime("%d/%b/%Y")
    params = {
        "api-key": os.getenv("DATAGOV_API_KEY"),  # Free key from data.gov.in
        "format": "json",
        "filters[State]": state,
        "filters[Commodity]": commodity,
        "filters[Arrival_Date]": today,
        "limit": 25
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        records = data.get("records", [])
        if not records:
            return f"Aaj {commodity} ka price {state} mein unavailable hai. AgMarkNet try karo: agmarknet.gov.in"
        
        modal_prices = [float(r["Modal_Price"]) for r in records if r.get("Modal_Price")]
        min_p = min(float(r["Min_Price"]) for r in records if r.get("Min_Price"))
        max_p = max(float(r["Max_Price"]) for r in records if r.get("Max_Price"))
        avg_modal = statistics.mean(modal_prices)
        mandis = [r.get("Market", "") for r in records[:3]]
        
        return (
            f"📊 {commodity} aaj ka price ({state}):\n"
            f"  Min: ₹{min_p:.0f}/quintal\n"
            f"  Max: ₹{max_p:.0f}/quintal\n"
            f"  Average Modal: ₹{avg_modal:.0f}/quintal\n"
            f"  Mandis covered: {', '.join(mandis)}"
        )
    except Exception as e:
        return f"Price fetch karne mein dikkat aayi: {str(e)}. Seedha agmarknet.gov.in check karo."

@tool
def get_price_trend(commodity: str, state: str) -> str:
    """
    Get last 7 days price trend — is price going up or down?
    Use when farmer asks 'kab bechu', 'price badhega kya', 'abhi sahi time hai?'
    No ML model needed — this is just arithmetic on 7 API calls.
    """
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    prices_by_day = {}
    
    for days_ago in range(7):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%b/%Y")
        params = {
            "api-key": os.getenv("DATAGOV_API_KEY"),
            "format": "json",
            "filters[State]": state,
            "filters[Commodity]": commodity,
            "filters[Arrival_Date]": date,
            "limit": 10
        }
        try:
            data = requests.get(url, params=params, timeout=8).json()
            records = data.get("records", [])
            if records:
                day_prices = [float(r["Modal_Price"]) for r in records if r.get("Modal_Price")]
                if day_prices:
                    prices_by_day[date] = statistics.mean(day_prices)
        except:
            continue
    
    if len(prices_by_day) < 3:
        return f"7 din ka data insufficient. Sirf {len(prices_by_day)} din ka data mila."
    
    price_values = list(prices_by_day.values())
    oldest = price_values[-1]
    newest = price_values[0]
    change_pct = ((newest - oldest) / oldest) * 100
    
    # Simple linear trend direction
    if change_pct > 3:
        trend = "📈 UPAR ja raha hai"
    elif change_pct < -3:
        trend = "📉 NEECHE aa raha hai"
    else:
        trend = "➡️ STABLE hai"
    
    return (
        f"📆 {commodity} — 7 din ka trend ({state}):\n"
        f"  7 din pehle: ₹{oldest:.0f}/q\n"
        f"  Aaj: ₹{newest:.0f}/q\n"
        f"  Change: {change_pct:+.1f}%\n"
        f"  Direction: {trend}\n"
        f"  Data points: {len(prices_by_day)} din"
    )

@tool
def get_seasonal_advice(commodity: str, current_month: int) -> str:
    """
    Get seasonal price pattern advice for a crop based on historical knowledge.
    This is a rule-based lookup — no ML model needed.
    Use when farmer asks 'is season mein price acha hoga kya?'
    """
    # Seasonal knowledge base — encoded from ICAR and historical AgMarkNet patterns
    # Peak = months when prices are historically highest
    SEASONAL_PATTERNS = {
        "Tomato":    {"peak": [12, 1, 2], "low": [9, 10], "note": "Summer tomatoes fetch best price"},
        "Onion":     {"peak": [4, 5, 6],  "low": [11, 12], "note": "Post-kharif harvest causes price drop"},
        "Wheat":     {"peak": [10, 11],   "low": [3, 4], "note": "Prices lowest right after rabi harvest"},
        "Rice":      {"peak": [6, 7],     "low": [10, 11], "note": "Kharif harvest brings prices down"},
        "Cotton":    {"peak": [6, 7, 8],  "low": [11, 12], "note": "Summer cotton demand from mills is high"},
        "Maize":     {"peak": [5, 6],     "low": [11, 12], "note": "Feed demand peaks before monsoon"},
        "Potato":    {"peak": [7, 8],     "low": [2, 3],   "note": "Rabi harvest depresses prices Feb-March"},
        "Soybean":   {"peak": [4, 5, 6],  "low": [11, 12], "note": "Kharif harvest Nov-Dec causes low prices"},
        "Groundnut": {"peak": [5, 6],     "low": [12, 1],  "note": "Oil demand drives summer prices"},
        "Sugarcane": {"peak": [11, 12],   "low": [4, 5],   "note": "Crushing season determines mill prices"},
    }
    
    pattern = SEASONAL_PATTERNS.get(commodity)
    if not pattern:
        return f"{commodity} ke liye historical seasonal pattern available nahi hai."
    
    if current_month in pattern["peak"]:
        timing = "✅ YE SAHI SAMAY HAI bechne ka — historically price peak par hota hai"
    elif current_month in pattern["low"]:
        timing = "⚠️ ABHI LOW SEASON hai — agar ho sake to thoda wait karo ya storage use karo"
    else:
        timing = "🔄 Average season hai — trend dekh ke decide karo"
    
    return (
        f"📅 {commodity} — Seasonal Pattern:\n"
        f"  {timing}\n"
        f"  Peak months: {pattern['peak']}\n"
        f"  Low months: {pattern['low']}\n"
        f"  Note: {pattern['note']}"
    )


def build_price_agent(llm):
    """
    Price agent uses tools + LLM reasoning.
    LLM decides WHICH tools to call based on farmer's question.
    ToolNode executes them. LLM synthesizes the results into advice.
    """
    tools = [get_current_mandi_price, get_price_trend, get_seasonal_advice]
    tool_node = ToolNode(tools)
    llm_with_tools = llm.bind_tools(tools)
    
    def llm_node(state: AgentState) -> dict:
        system = """
        Tu KisaanAI ka price advisor hai. Indian farmers ko mandi price aur selling timing advice do.
        
        Available tools:
        - get_current_mandi_price: Aaj ka live price fetch karo AgMarkNet se
        - get_price_trend: 7 din ka trend dekho (price upar ja raha hai ya neeche)
        - get_seasonal_advice: Is season mein historically price kaisa hota hai
        
        Farmer ka state aur commodity pehchano query se. 
        Agar state nahi pata, assume karo Gujarat.
        Agar commodity nahi pata, farmer se seedha pucho.
        
        Multiple tools use karo agar comprehensive advice chahiye.
        Hinglish mein jawab do. Specific numbers cite karo tools se.
        """
        response = llm_with_tools.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [response]}
    
    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", tools_condition)  # → "tools" if tool call, → END if done
    graph.add_edge("tools", "llm")   # After tool result, LLM synthesizes and responds
    
    return graph.compile()
```

#### Example Conversation This Enables

```
Farmer: "Aaj tomato ka rate kya hai Gujarat mein? Bechu ya ruko?"

Agent calls: get_current_mandi_price("Tomato", "Gujarat")
             get_price_trend("Tomato", "Gujarat")  
             get_seasonal_advice("Tomato", current_month=3)

LLM synthesizes:
"Aaj Gujarat mein tomato ₹1,240/q par chal raha hai (Ahmedabad mandi).
Pichle 7 din mein price 8% upar gaya hai 📈
March historically tomato ke liye average season hai.
Meri advice: Aaj bechen — price upar hai aur March ke baad
April-May mein naya crop aata hai jisse price gir sakta hai."
```

---

## 8. Orchestrator & Routing Graph

### 8.1 Structured Intent Classification (Better Than Current)

The current approach: `llm.invoke(prompt).content.strip().lower()` — fragile, can return anything.

The production approach: **Structured output with Pydantic**

```python
# kisaanai/orchestrator/intent.py
from pydantic import BaseModel, Field
from typing import Literal

class IntentClassification(BaseModel):
    """Structured output for query classification"""
    route: Literal["disease", "scheme", "crop_rec", "price", "general"] = Field(
        description="Which agent should handle this query"
    )
    confidence: float = Field(
        description="Confidence score 0-1", ge=0, le=1
    )
    detected_language: Literal["hindi", "hinglish", "english"] = Field(
        description="Primary language of the query"
    )
    query_english: str = Field(
        description="Query translated to English for better FAISS search"
    )
    needs_multi_agent: bool = Field(
        description="True if query needs multiple agents (e.g., disease + scheme both)"
    )

# Use structured output
classifier_llm = llm.with_structured_output(IntentClassification)

def intent_classify_node(state: OrchestratorState) -> dict:
    query = state["messages"][-1].content
    
    system = """
    You are a routing classifier for KisaanAI, an Indian agricultural assistant.
    
    Routes:
    - "disease": Crop diseases, pests, symptoms, treatment (bimari, rog, pest, yellow leaves)
    - "scheme": Government schemes, subsidies, yojana, PM Kisan, documents
    - "crop_rec": What to grow, crop suggestion, soil type, season recommendation
    - "price": Mandi price, rate, when to sell, market price
    - "general": Greetings, general farming tips, anything else
    
    Language detection:
    - "hindi": Pure Devanagari text
    - "hinglish": Mix of Hindi words in Roman script (e.g., "mera khet")
    - "english": Primarily English
    """
    
    result = classifier_llm.invoke([SystemMessage(content=system), HumanMessage(content=query)])
    
    return {
        "route": result.route,
        "confidence": result.confidence,
        "detected_language": result.detected_language,
        "query_rewritten": result.query_english,
        "nodes_visited": ["intent_classify"]
    }
```

### 8.2 Full Orchestrator Graph with All LangGraph Patterns

```python
# kisaanai/orchestrator/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command, interrupt

def build_orchestrator(agents: dict, checkpointer) -> CompiledGraph:
    
    # ── Node: Language Detection ──
    def language_detect(state: OrchestratorState) -> dict:
        # Fast rule-based detection (no LLM cost)
        query = state["messages"][-1].content
        hindi_chars = sum(1 for c in query if '\u0900' <= c <= '\u097F')
        if hindi_chars > len(query) * 0.3:
            lang = "hindi"
        elif any(w in query.lower() for w in ["mera", "meri", "kya", "kaise", "aur", "hai"]):
            lang = "hinglish"
        else:
            lang = "english"
        return {"detected_language": lang, "nodes_visited": ["language_detect"]}
    
    # ── Node: Intent Classification ──
    def intent_classify(state: OrchestratorState) -> dict:
        return intent_classify_node(state)
    
    # ── Node: Safety / Interrupt Check ──
    def safety_gate(state: OrchestratorState) -> dict:
        """
        HUMAN-IN-THE-LOOP: Interrupt before responding if query involves
        critical pesticide recommendations or complex medical advice.
        This is a LangGraph 'interrupt' — pauses execution for human review.
        """
        query = state["messages"][-1].content.lower()
        critical_terms = ["systemic poison", "highly toxic", "suicide", "emergency"]
        
        if any(term in query for term in critical_terms):
            # interrupt() pauses the graph and returns control to the caller
            # The graph RESUMES when .update_state() is called with human_approved=True
            human_decision = interrupt({
                "reason": "Query involves critical safety topic",
                "query": query,
                "action_required": "Review and approve or modify response"
            })
            return {"human_approved": human_decision.get("approved", False)}
        
        return {"human_approved": True}
    
    # ── Node: Route to Single Agent ──
    def route_to_agent(state: OrchestratorState):
        """
        CONDITIONAL ROUTING using Send API for parallel execution
        when query needs multiple agents.
        """
        route = state["route"]
        
        # If query needs multiple agents (e.g., "disease se related koi scheme hai?")
        if state.get("needs_multi_agent"):
            return [
                Send("disease_agent", {"messages": state["messages"]}),
                Send("scheme_agent", {"messages": state["messages"]})
            ]
        
        # Single agent routing via conditional edges (defined below)
        return route
    
    # ── Node: Response Formatter ──
    def format_response(state: OrchestratorState) -> dict:
        """Final formatting — add source citations, disclaimers"""
        response = state.get("agent_response", "")
        
        # Add appropriate disclaimer based on route
        disclaimers = {
            "disease": "\n\n⚠️ *Ye general advice hai. Serious disease ke liye apne KVK ya agriculture officer se milein.*",
            "scheme": "\n\n📋 *Scheme details change ho sakti hain. Apply karne se pehle official website zaroor check karein.*",
            "price": "\n\n📊 *Prices live market data par based hain. Final decision apni local mandi se verify karein.*"
        }
        
        route = state.get("route", "general")
        disclaimer = disclaimers.get(route, "")
        final_response = response + disclaimer
        
        return {
            "messages": [AIMessage(content=final_response)],
            "nodes_visited": ["format_response"]
        }
    
    # ── Build the Graph ──
    graph = StateGraph(OrchestratorState)
    
    # Add all nodes
    graph.add_node("language_detect", language_detect)
    graph.add_node("intent_classify", intent_classify)
    graph.add_node("safety_gate", safety_gate)
    graph.add_node("disease_agent", agents["disease"])   # Subgraph as node
    graph.add_node("scheme_agent", agents["scheme"])     # Subgraph as node
    graph.add_node("crop_rec_agent", agents["crop_rec"]) # Subgraph as node
    graph.add_node("price_agent", agents["price"])       # Subgraph as node
    graph.add_node("format_response", format_response)
    
    # Add edges — sequential flow
    graph.add_edge(START, "language_detect")
    graph.add_edge("language_detect", "intent_classify")
    graph.add_edge("intent_classify", "safety_gate")
    
    # Conditional routing AFTER safety gate
    graph.add_conditional_edges(
        "safety_gate",
        route_to_agent,  # Returns route name or list of Send objects
        {
            "disease": "disease_agent",
            "scheme": "scheme_agent",
            "crop_rec": "crop_rec_agent",
            "price": "price_agent",
            "general": "format_response"  # No specialized agent needed
        }
    )
    
    # All agents lead to formatter
    graph.add_edge("disease_agent", "format_response")
    graph.add_edge("scheme_agent", "format_response")
    graph.add_edge("crop_rec_agent", "format_response")
    graph.add_edge("price_agent", "format_response")
    graph.add_edge("format_response", END)
    
    # Compile with persistent checkpointer
    return graph.compile(checkpointer=checkpointer, interrupt_before=["safety_gate"])
```

---

## 9. LangGraph Advanced Patterns

### 9.1 Persistent Checkpointer (Production Memory)

```python
# kisaanai/memory/checkpointer.py

# Development
from langgraph.checkpoint.memory import InMemorySaver
dev_checkpointer = InMemorySaver()

# Production — PostgreSQL
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_prod_checkpointer():
    """PostgreSQL checkpointer for production — persists across restarts"""
    conn_string = os.getenv("DATABASE_URL")  # postgresql://user:pass@host/db
    checkpointer = AsyncPostgresSaver.from_conn_string(conn_string)
    await checkpointer.setup()  # Creates required tables
    return checkpointer

# This enables:
# - Conversations that survive server restarts
# - Farmer-specific history: "Kal aapne tomato disease ke baare mein poocha tha"
# - Multi-device conversation continuity
# thread_id = farmer's phone number or unique ID
```

### 9.2 Streaming (Token-by-Token Response)

```python
# kisaanai/api/streaming.py
from fastapi.responses import StreamingResponse
import json

async def stream_response(orchestrator, query: str, thread_id: str):
    """Stream LangGraph tokens to frontend via SSE"""
    config = {"configurable": {"thread_id": thread_id}}
    
    async def event_generator():
        async for event in orchestrator.astream_events(
            {"messages": [HumanMessage(content=query)]},
            config=config,
            version="v2",
            stream_mode="messages"  # Stream individual message tokens
        ):
            kind = event["event"]
            
            # Emit token chunks as they arrive
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
            
            # Emit node transitions for UI loading indicators
            elif kind == "on_chain_start":
                node_name = event.get("name", "")
                if node_name in ["disease_agent", "scheme_agent", "crop_rec_agent"]:
                    yield f"data: {json.dumps({'status': f'Searching {node_name}...'})}\n\n"
            
            # Signal completion
            elif kind == "on_chain_end" and event.get("name") == "format_response":
                yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 9.3 Human-in-the-Loop — Resume After Review

```python
# kisaanai/api/hitl.py

async def handle_interrupt(orchestrator, thread_id: str):
    """When graph is interrupted at safety_gate, admin reviews and approves"""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get current state (paused at interrupt)
    state = await orchestrator.aget_state(config)
    interrupted_at = state.next  # Which node is waiting
    
    print(f"Graph paused at: {interrupted_at}")
    print(f"Pending data: {state.tasks[0].interrupts[0].value}")
    
    # Admin/moderator reviews and approves
    admin_decision = {"approved": True, "modified_query": None}
    
    # Resume the graph with human decision using Command
    result = await orchestrator.ainvoke(
        Command(resume=admin_decision),
        config=config
    )
    return result
```

### 9.4 Send API — Parallel Multi-Agent Queries

```python
# When a farmer asks something that spans multiple agents:
# "Mere tamatar mein bimari hai, koi scheme bhi batao"
# → Run Disease Agent AND Scheme Agent in PARALLEL

from langgraph.types import Send

def parallel_router(state: OrchestratorState):
    """Fan-out: send query to multiple agents simultaneously"""
    route = state["route"]
    
    if state.get("needs_multi_agent"):
        agents_to_call = detect_relevant_agents(state["messages"][-1].content)
        # Send creates parallel branches that execute simultaneously
        return [Send(agent, {"messages": state["messages"]}) for agent in agents_to_call]
    
    return route  # Single agent routing

def detect_relevant_agents(query: str) -> list[str]:
    """Detect if multiple agents are needed"""
    agents = []
    if any(k in query.lower() for k in ["bimari", "disease", "lakshan"]):
        agents.append("disease_agent")
    if any(k in query.lower() for k in ["scheme", "yojana", "subsidy"]):
        agents.append("scheme_agent")
    return agents if agents else ["disease_agent"]
```

### 9.5 Graph Visualization (Development Tool)

```python
# Save graph diagram for documentation
from IPython.display import Image, display

def visualize_graph(graph, filename="graph.png"):
    """Generate Mermaid diagram of the graph"""
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)
    print(f"Graph saved to {filename}")
    return Image(png_data)

# In Jupyter:
# visualize_graph(orchestrator, "docs/orchestrator_graph.png")
# visualize_graph(disease_workflow, "docs/disease_agent_graph.png")
```

---

## 10. Project Structure

```
kisaanai/
│
├── 📁 kisaanai/                    # Main package
│   ├── __init__.py
│   │
│   ├── 📁 state/
│   │   ├── __init__.py
│   │   ├── orchestrator_state.py   # OrchestratorState TypedDict
│   │   └── agent_state.py         # AgentState TypedDict
│   │
│   ├── 📁 agents/
│   │   ├── __init__.py
│   │   ├── disease_agent.py        # Disease subgraph
│   │   ├── scheme_agent.py         # Scheme subgraph  
│   │   ├── crop_rec_agent.py       # Crop recommendation subgraph
│   │   └── price_agent.py          # Price prediction subgraph
│   │
│   ├── 📁 orchestrator/
│   │   ├── __init__.py
│   │   ├── graph.py               # Master orchestrator graph
│   │   ├── intent.py              # Intent classification (Pydantic)
│   │   └── routing.py             # Routing logic + Send API
│   │
│   ├── 📁 rag/
│   │   ├── __init__.py
│   │   ├── embedder.py            # SentenceTransformer wrapper
│   │   ├── faiss_store.py         # FAISS index build + query
│   │   └── document_loader.py    # Load and chunk datasets
│   │
│   ├── 📁 memory/
│   │   ├── __init__.py
│   │   ├── checkpointer.py        # Dev + Prod checkpointer setup
│   │   └── session.py             # Session/thread management
│   │
│   ├── 📁 tools/
│   │   ├── __init__.py
│   │   ├── agmarknet.py           # Mandi price API tool
│   │   ├── myscheme.py            # Government scheme API tool
│   │   └── weather.py             # Weather API tool (IMD)
│   │
│   └── 📁 utils/
│       ├── __init__.py
│       ├── language.py            # Language detection + translation
│       └── formatting.py         # Response formatting helpers
│
├── 📁 api/                        # FastAPI application
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, routes
│   ├── schemas.py                 # Pydantic request/response models
│   └── streaming.py              # SSE streaming endpoint
│
├── 📁 scripts/                    # Data collection & setup scripts
│   ├── collect_schemes.py         # Scrape/fetch scheme data
│   ├── augment_diseases.py       # LLM-augment disease dataset
│   ├── build_faiss_index.py      # Build and save FAISS indexes (schemes + diseases + crop_rec)
│   └── build_crop_rec_index.py   # Embed Kaggle crop CSV into FAISS (see Section 7.3)
│
├── 📁 dataset/
│   ├── schemes_india.csv          # 500+ schemes (to be built)
│   ├── diseases_india.csv         # 1500+ disease records (to be built)
│   ├── crop_recommendation.csv    # Kaggle dataset
│   └── mandi_prices_sample.csv   # Sample historical prices
│
├── 📁 models/
│   └── 📁 faiss_indexes/
│       ├── schemes.index          # FAISS index for schemes
│       ├── schemes_metadata.json  # Doc metadata (id → full record)
│       ├── diseases.index         # FAISS index for diseases
│       ├── diseases_metadata.json
│       ├── crop_rec.index         # FAISS index for crop records (from Kaggle CSV)
│       └── crop_rec_metadata.json # All 2,200 crop rows as searchable records
│
├── 📁 notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_scheme_agent_dev.ipynb
│   ├── 03_disease_agent_dev.ipynb
│   ├── 04_orchestrator_dev.ipynb
│   └── models.ipynb               # Your existing notebook ← Start here
│
├── 📁 tests/
│   ├── test_disease_agent.py
│   ├── test_scheme_agent.py
│   ├── test_orchestrator.py
│   └── test_routing.py
│
├── 📁 docs/
│   ├── orchestrator_graph.png     # Auto-generated graph diagrams
│   ├── disease_agent_graph.png
│   └── api_docs.md
│
├── 📁 docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .env                           # API keys (never commit)
├── .env.example                   # Template for env vars
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 11. Tech Stack & Dependencies

### Core Dependencies

```txt
# requirements.txt

# LangGraph & LangChain
langgraph>=0.2.0
langchain>=0.3.0
langchain-groq>=0.2.0
langchain-community>=0.3.0
langsmith>=0.1.0

# LLM
groq>=0.11.0

# Vector Search & Embeddings
faiss-cpu>=1.8.0              # Use faiss-gpu if you have CUDA
sentence-transformers>=3.0.0   # all-MiniLM-L6-v2 model

# Statistics (for price trend — built-in Python, no ML model)
# statistics module is part of Python standard library — no install needed

# Data
pandas>=2.2.0
numpy>=1.26.0

# API
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0

# Database (for PostgreSQL checkpointer in production)
psycopg[binary,pool]>=3.2.0
langgraph-checkpoint-postgres>=2.0.0

# Cache
redis>=5.0.0

# HTTP
httpx>=0.27.0
requests>=2.32.0

# Language detection
langdetect>=1.0.9
deep-translator>=1.11.0       # For Hindi→English translation

# Dev tools
python-dotenv>=1.0.0
jupyter>=1.1.0
```

### Environment Variables

```bash
# .env

# LLM
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-70b-versatile        # Best quality
GROQ_MODEL_FAST=llama-3.1-8b-instant     # For routing/classification

# LangSmith (Production Tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_key_here
LANGCHAIN_PROJECT=KisaanAI-Production

# Database (Production)
DATABASE_URL=postgresql://user:pass@localhost:5432/kisaanai

# Cache
REDIS_URL=redis://localhost:6379

# External APIs
DATAGOV_API_KEY=your_datagov_key          # Free from data.gov.in
OPENWEATHER_API_KEY=your_owm_key          # For weather data

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu                       # or cuda

# FAISS Index Paths
SCHEMES_FAISS_PATH=models/faiss_indexes/schemes.index
DISEASES_FAISS_PATH=models/faiss_indexes/diseases.index
```

---

## 12. API Layer

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid

app = FastAPI(title="KisaanAI API", version="2.0.0")

class ChatRequest(BaseModel):
    query: str
    farmer_id: str = None      # Optional persistent farmer ID
    session_id: str = None     # Optional session continuity
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    route: str                  # Which agent handled it
    session_id: str            # For continuing the conversation
    confidence: float

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Standard (non-streaming) chat endpoint"""
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = await orchestrator.ainvoke(
            {"messages": [HumanMessage(content=request.query)]},
            config=config
        )
        
        return ChatResponse(
            response=result["messages"][-1].content,
            route=result.get("route", "general"),
            session_id=session_id,
            confidence=result.get("confidence", 1.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint — returns Server-Sent Events"""
    session_id = request.session_id or str(uuid.uuid4())
    return await stream_response(orchestrator, request.query, session_id)

@app.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get full conversation history for a session"""
    config = {"configurable": {"thread_id": session_id}}
    state = await orchestrator.aget_state(config)
    messages = [
        {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
        for m in state.values.get("messages", [])
    ]
    return {"session_id": session_id, "messages": messages}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
```

---

## 13. Deployment Strategy

### Phase 1: Local Development

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Build FAISS indexes from your datasets
python scripts/build_faiss_index.py

# Run in notebook first
jupyter notebook notebooks/models.ipynb

# Then run as API
uvicorn api.main:app --reload --port 8000
```

### Phase 2: Docker Deployment

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-built FAISS indexes
COPY models/ models/
COPY dataset/ dataset/
COPY kisaanai/ kisaanai/
COPY api/ api/

# Download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker/docker-compose.yml
version: '3.8'
services:
  kisaanai-api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis
    
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: kisaanai
      POSTGRES_USER: kisaanai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Phase 3: Cloud Deployment (Recommended Path)

```
Option A: LangGraph Platform (Easiest)
  → langgraph deploy (official LangChain managed platform)
  → Auto-handles scaling, checkpointing, API

Option B: Railway / Render (Simple cloud)
  → Connect GitHub repo → auto-deploy on push
  → Add PostgreSQL + Redis as managed services

Option C: AWS / GCP (Full control)
  → EC2/Cloud Run for API
  → RDS PostgreSQL for checkpointer
  → ElastiCache Redis for cache
  → S3 for FAISS indexes

Recommended for KisaanAI: Start with Railway (cheapest, simplest)
Then graduate to AWS when user count grows.
```

---

## 14. Evaluation & Monitoring

### LangSmith Tracing (Must-Have for Production)

```python
# Enable in .env
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls__...
# LANGCHAIN_PROJECT=KisaanAI-Production

# Every graph invocation is automatically traced:
# - Which nodes executed
# - How long each took
# - What the LLM received and returned
# - Token usage and costs
# - Errors and retries
```

### Evaluation Dataset

Create a golden test set of 100 question-answer pairs:

```python
# tests/eval_dataset.json
[
  {
    "query": "PM Kisan scheme kya hai?",
    "expected_route": "scheme",
    "expected_contains": ["6000", "kisan", "per year", "3 installment"]
  },
  {
    "query": "Mere tamatar ke patte peele ho rahe hain",
    "expected_route": "disease",
    "expected_contains": ["early blight", "yellow", "fungicide", "treatment"]
  },
  {
    "query": "Is mausam mein kaunsi fasal ugaoon?",
    "expected_route": "crop_rec",
    "expected_contains": ["kharif", "crop", "recommendation"]
  }
]

# Run evaluation
def evaluate_kisaanai(orchestrator, eval_dataset):
    results = []
    for test in eval_dataset:
        result = orchestrator.invoke({"messages": [HumanMessage(content=test["query"])]})
        
        route_correct = result["route"] == test["expected_route"]
        content_correct = all(k.lower() in result["messages"][-1].content.lower() 
                              for k in test["expected_contains"])
        
        results.append({
            "query": test["query"],
            "route_accuracy": route_correct,
            "content_accuracy": content_correct
        })
    
    route_acc = sum(r["route_accuracy"] for r in results) / len(results)
    content_acc = sum(r["content_accuracy"] for r in results) / len(results)
    print(f"Route Accuracy: {route_acc:.1%}")
    print(f"Content Accuracy: {content_acc:.1%}")
```

---

## 15. Roadmap & Milestones

### Phase 1: Foundation (Week 1-2) — Start Here
- [ ] Fix current notebook: Use structured Pydantic output for routing
- [ ] Build dataset collection scripts (`collect_schemes.py`, verify disease CSV quality)
- [ ] Refactor agents into proper subgraphs (separate files)
- [ ] Add PostgreSQL checkpointer (replace InMemorySaver)
- [ ] Add LangSmith tracing

### Phase 2: Core Agents (Week 3-4)
- [ ] Build Crop Recommendation Agent (download Kaggle CSV → build FAISS index → RAG + LLM, no ML training)
- [ ] Build Price Agent (register free data.gov.in API key → implement 3 tools → ToolNode graph)
- [ ] Add Human-in-the-Loop with `interrupt()` for safety
- [ ] Add streaming with `astream_events`
- [ ] Add parallel execution with `Send` API

### Phase 3: API & Deployment (Week 5-6)
- [ ] Build FastAPI application
- [ ] Dockerize the application
- [ ] Deploy to Railway/Render
- [ ] Add basic frontend (Streamlit or simple HTML)

### Phase 4: Enhancement (Week 7-8)
- [ ] Add image-based disease detection (ResNet50 + LangGraph image input)
- [ ] WhatsApp integration (via Twilio or Meta Cloud API)
- [ ] Hindi TTS for voice output
- [ ] Expand to 5 states' scheme data

### Phase 5: Production Hardening (Ongoing)
- [ ] Add retry logic for Groq API failures
- [ ] Add rate limiting
- [ ] Add user feedback loop (thumbs up/down)
- [ ] Run LangSmith evaluations weekly
- [ ] Add A/B testing for different LLM prompts

---

## Quick Reference: LangGraph Patterns Used

```python
# Pattern 1: State with reducer
class State(TypedDict):
    messages: Annotated[list, add_messages]     # append-only
    docs: Annotated[list, merge_docs]            # custom merge

# Pattern 2: Subgraph as node
orchestrator.add_node("disease_agent", disease_subgraph)  # compiled graph as node

# Pattern 3: Conditional routing  
graph.add_conditional_edges("router", route_fn, {"disease": "disease_agent", ...})

# Pattern 4: Tool calling
llm_with_tools = llm.bind_tools(tools)
graph.add_conditional_edges("llm", tools_condition)  # routes to "tools" or END

# Pattern 5: Interrupt (human-in-loop)
human_input = interrupt({"question": "Approve this response?"})

# Pattern 6: Parallel execution
return [Send("disease_agent", state), Send("scheme_agent", state)]

# Pattern 7: Persistent memory
checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
graph.compile(checkpointer=checkpointer)

# Pattern 8: Streaming
async for event in graph.astream_events(input, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        yield event["data"]["chunk"].content

# Pattern 9: Resume after interrupt
result = await graph.ainvoke(Command(resume={"approved": True}), config)

# Pattern 10: State inspection
state = await graph.aget_state(config)
history = await graph.aget_state_history(config)
```

---

*KisaanAI 2.0 — Built with LangGraph, for India's 140 million farmers* 🌾
