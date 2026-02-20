import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
ENV = os.getenv("ENV", "production" if os.getenv("K_SERVICE") else "development")

if ENV == "production":
    DATA_DIR = Path("/tmp/data")
    CHROMA_DIR = Path("/tmp/chroma_db")
else:
    DATA_DIR = BASE_DIR / "data"
    CHROMA_DIR = BASE_DIR / "chroma_db"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "personal_docs"

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-vault-key-3000")
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
