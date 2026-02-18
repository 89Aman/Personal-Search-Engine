import logging
import time
from typing import List, Optional
from datetime import datetime

import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import shutil
from app.config import (
    CHROMA_DIR,
    EMBEDDING_MODEL_NAME,
    COLLECTION_NAME,
    DATA_DIR,
    BASE_DIR,
    FRONTEND_URL,
    GEMINI_API_KEY,
    ENV,
)

from app.ingest import ingest_folder, get_collection, get_embedder
from contextlib import asynccontextmanager

# --- Setup & Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vault-backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initializes resources on startup
    logger.info("Lifespan: Initializing resources...")
    
    # Pre-load embedding model and vector DB
    get_embedder()
    get_collection()

    # --- Startup Data Seeding (Cloud Run) ---
    if ENV == "production":
        logger.info("Production environment detected. Checking for baked-in data...")
        baked_data = BASE_DIR / "data"
        if baked_data.exists():
            for category in ["pdfs", "markdown", "notes"]:
                src_dir = baked_data / category
                dst_dir = DATA_DIR / category
                dst_dir.mkdir(parents=True, exist_ok=True)
                
                if src_dir.exists():
                    for item in src_dir.glob("*"):
                        if item.is_file() and not (dst_dir / item.name).exists():
                            try:
                                shutil.copy2(item, dst_dir / item.name)
                                logger.info(f"Seeded {item.name} to {dst_dir}")
                            except Exception as e:
                                logger.error(f"Failed to seed {item.name}: {e}")
        else:
            logger.warning(f"Baked data directory {baked_data} not found.")

    logger.info(f"Vector DB initialized using {EMBEDDING_MODEL_NAME}")
    yield
    # Cleanup if needed
    logger.info("Lifespan: Shutting down...")

app = FastAPI(title="Personal Semantic Search Engine", lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI Setup ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini AI initialized.")
else:
    model = None
    logger.warning("GEMINI_API_KEY not found. AI synthesis disabled.")

# --- Schemas ---

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    types: Optional[List[str]] = None
    max_age_days: Optional[int] = None
    recency_boost: float = 0.3

class AskRequest(BaseModel):
    query: str
    context: List[str]

# --- Core Logic ---

def compute_recency_weight(mtime: float, max_age_days: Optional[int]) -> float:
    if max_age_days is None: return 1.0
    now = time.time()
    age_days = (now - mtime) / 86400
    if age_days < 0: return 1.0
    if age_days > max_age_days: return 0.2
    return 1.0 - (age_days / (max_age_days + 1e-6)) * 0.8

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "operational", "timestamp": datetime.now().isoformat(), "env": ENV}

@app.post("/search")
def search(req: SearchRequest):
    logger.info(f"Search request: {req.query}")
    embedder = get_embedder()
    collection = get_collection()
    
    q_emb = embedder.encode(req.query)
    where = {}
    if req.types: where["type"] = {"$in": req.types}
    if req.max_age_days:
        cutoff = time.time() - req.max_age_days * 86400
        where["mtime"] = {"$gte": cutoff}

    result = collection.query(
        query_embeddings=[q_emb.tolist()],
        n_results=req.top_k,
        where=where or None,
        include=["documents", "metadatas", "distances"]
    )

    ids, docs, metas, dists = result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    q_words = set(req.query.lower().split())
    
    seen_texts = set()
    scored = []
    for i, d, m, dist in zip(ids, docs, metas, dists):
        if d in seen_texts:
            continue
        seen_texts.add(d)
        base_score = 1.0 / (1.0 + dist)
        keyword_boost = min(sum(1 for w in q_words if w in d.lower()) / (len(q_words) + 1), 0.5)
        recency = compute_recency_weight(m.get("mtime", time.time()), req.max_age_days)
        final_score = ((base_score * 0.7) + (keyword_boost * 0.3)) * recency

        lines = [l.strip() for l in d.split("\n") if len(l.strip()) > 5]
        snippets = [l for l in lines if any(w in l.lower() for w in q_words)][:3]

        scored.append({
            "id": i, "text": d, "snippets": snippets, "source": m["source"],
            "type": m["type"], "path": m["path"], "score": final_score
        })

    return {"results": sorted(scored, key=lambda x: x["score"], reverse=True)}

@app.post("/ask")
def ask_ai(req: AskRequest):
    if not model: raise HTTPException(status_code=400, detail="Gemini key missing")
    context_str = "\n\n".join(req.context[:5])
    prompt = f"Use context to answer concisely: {context_str}\n\nQuestion: {req.query}"
    try:
        response = model.generate_content(prompt)
        return {"answer": response.text}
    except Exception as e:
        logger.error(f"AI Synthesis Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

from fastapi import BackgroundTasks

@app.post("/upload")
async def upload_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    paths = []
    for f in files:
        target_dir = DATA_DIR / ("pdfs" if f.filename.endswith(".pdf") else "markdown" if f.filename.endswith(".md") else "notes")
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f.filename
        path.write_bytes(await f.read())
        paths.append(path)
    
    logger.info(f"Uploaded {len(paths)} files. Triggering background re-ingestion.")
    background_tasks.add_task(ingest_folder)
    return {"status": "ok", "message": "Ingestion started in background", "files": [p.name for p in paths]}

@app.get("/documents")
def list_documents():
    """Returns a list of all documents stored in the system."""
    files = []
    # DATA_DIR is a pathlib.Path object
    if DATA_DIR.exists():
        for file_path in DATA_DIR.rglob("*"):
            if file_path.is_file():
                # Get relative path to DATA_DIR so users see "pdfs/file.pdf" etc.
                try:
                    relative_path = file_path.relative_to(DATA_DIR)
                    files.append(str(relative_path))
                except ValueError:
                    logger.warning(f"Could not determine relative path for {file_path}")
    return {"documents": sorted(files)}