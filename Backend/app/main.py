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

from app.config import (
    CHROMA_DIR,
    EMBEDDING_MODEL_NAME,
    COLLECTION_NAME,
    DATA_DIR,
    FRONTEND_URL,
    GEMINI_API_KEY,
    ENV,
)
from app.ingest import ingest_folder

# --- Setup & Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vault-backend")

app = FastAPI(title="Personal Semantic Search Engine")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI & Vector DB ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini AI initialized.")
else:
    model = None
    logger.warning("GEMINI_API_KEY not found. AI synthesis disabled.")

client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(COLLECTION_NAME)
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
logger.info(f"Vector DB initialized using {EMBEDDING_MODEL_NAME}")

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
    
    scored = []
    for i, d, m, dist in zip(ids, docs, metas, dists):
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

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    paths = []
    for f in files:
        target_dir = DATA_DIR / ("pdfs" if f.filename.endswith(".pdf") else "markdown" if f.filename.endswith(".md") else "notes")
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f.filename
        path.write_bytes(await f.read())
        paths.append(path)
    
    logger.info(f"Uploaded {len(paths)} files. Triggering re-ingestion.")
    ingest_folder()
    return {"status": "ok", "files": [p.name for p in paths]}


