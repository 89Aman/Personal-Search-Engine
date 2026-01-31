import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Path Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Model Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "personal_docs"

# Security & Global Settings
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-vault-key-3000")
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Auto-detect Environment: If K_SERVICE exists, we are on Google Cloud Run
ENV = os.getenv("ENV", "production" if os.getenv("K_SERVICE") else "development")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
