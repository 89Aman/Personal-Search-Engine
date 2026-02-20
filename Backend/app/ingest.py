
from pathlib import Path
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from app.config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME

_client = None
_collection = None
_embedder = None

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client

def get_collection():
    global _collection
    if _collection is None:
        _collection = get_client().get_or_create_collection(COLLECTION_NAME)
    return _collection

def get_embedder():
    global _embedder
    if _embedder is None:
        try:
            print(f"Loading '{EMBEDDING_MODEL_NAME}'")
            _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
            print("Model loaded")
        except Exception as e:
            print(f"Downloading model ({e})")
            _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedder

def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t:
            texts.append(t)
    return "\n".join(texts)

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> List[str]:
    if not text: return []
    words = str(text).split()
    if not words: return []
    chunks: List[str] = []
    i = 0
    step = max(chunk_size - overlap, 1)
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words).strip()
        if len(chunk) > 10:
            chunks.append(chunk)
        i += step
    return chunks

def ingest_folder() -> None:
    try:
        collection = get_collection()
        existing_data = collection.get(include=["metadatas"])
        existing_files = {}
        if existing_data and existing_data["metadatas"]:
            for m in existing_data["metadatas"]:
                if m and "source" in m:
                    existing_files[m["source"]] = m.get("mtime", 0.0)
    except Exception as e:
        print(f"Metadata error: {e}")
        existing_files = {}

    print(f"Ingesting. Found {len(existing_files)} files")

    for sub in ["pdfs", "markdown", "notes"]:
        folder = DATA_DIR / sub
        if not folder.exists(): continue

        for path in folder.glob("*"):
            if not path.is_file(): continue
            suffix = path.suffix.lower()
            if suffix not in [".pdf", ".md", ".txt"]: continue
            
            current_mtime = path.stat().st_mtime
            if path.name in existing_files:
                if current_mtime <= existing_files[path.name]: continue
                print(f"Updating {path.name}")
            else:
                print(f"New file: {path.name}")

            try: 
                collection.delete(where={"source": path.name})

                if suffix == ".pdf":
                    raw = read_pdf(path)
                    doc_type = "pdf"
                else:
                    raw = read_text_file(path)
                    doc_type = "markdown" if suffix == ".md" else "notes"

                chunks = chunk_text(raw)
                chunks = [c for c in chunks if isinstance(c, str) and c.strip()]
                
                if not chunks: continue

                embedder = get_embedder()
                embeddings = embedder.encode(chunks).tolist()
                
                file_hash = str(abs(hash(path.name)))
                ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
                
                metadatas = [
                    {"source": path.name, "path": str(path), "type": doc_type, "mtime": current_mtime}
                    for _ in chunks
                ]

                collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
                print(f"Indexed {len(chunks)} chunks: {path.name}")
            except Exception as e:
                print(f"Ingest failed {path.name}: {e}")

if __name__ == "__main__":
    ingest_folder()
    print("Complete")
