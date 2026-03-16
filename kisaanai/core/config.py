import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project Root
ROOT_DIR = Path(__file__).parent.parent.parent

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Data Paths
SCHEME_CSV = ROOT_DIR / os.getenv("SCHEME_CSV", "dataset/agri_schemes_full.csv")
DISEASE_CSV = ROOT_DIR / os.getenv("DISEASE_CSV", "dataset/india_top100_new_crops_diseases.csv")

# Model Paths
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
FAISS_INDEX_DIR = ROOT_DIR / os.getenv("FAISS_INDEX_DIR", "models/faiss_indexes")
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

# LangSmith
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
