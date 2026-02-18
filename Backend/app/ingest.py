from pathlib import Path
from typing import List
import time

import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from app.config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME


# Global placeholders
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


def chunk_text(
    text: str,
    chunk_size: int = 200, # Reduced for better semantic density
    overlap: int = 40,
) -> List[str]:
    """Split text into overlapping word-based chunks."""
    if not text:
        return []

    words = str(text).split()
    if not words:
        return []

    chunks: List[str] = []
    i = 0
    step = max(chunk_size - overlap, 1)

    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words).strip()
        if len(chunk) > 10: # Avoid tiny, meaningless chunks
            chunks.append(chunk)
        i += step

    return chunks


def ingest_folder() -> None:
    """Index all PDFs / markdown / notes under data/."""
    try:
        # 1. Fetch existing file metadata to avoid redundant processing
        # We only need one chunk per file to check mtime, but fetching all metadatas is simpler for now
        # given the scale of a personal search engine.
        collection = get_collection()
        existing_data = collection.get(include=["metadatas"])
        existing_files = {} # filename -> mtime

        if existing_data and existing_data["metadatas"]:
            for m in existing_data["metadatas"]:
                if m and "source" in m:
                    # Store the mtime. If multiple chunks, this overwrites, which is fine
                    # as they should be identical for the same file import.
                    existing_files[m["source"]] = m.get("mtime", 0.0)
    except Exception as e:
        print(f"Error fetching existing metadata: {e}")
        existing_files = {}

    print(f"Starting ingestion. Found {len(existing_files)} files in index.")

    for sub in ["pdfs", "markdown", "notes"]:
        folder = DATA_DIR / sub
        if not folder.exists():
            continue

        for path in folder.glob("*"):
            if not path.is_file():
                continue

            suffix = path.suffix.lower()
            if suffix not in [".pdf", ".md", ".txt"]:
                continue
            
            # Check if file is already indexed and unchanged
            current_mtime = path.stat().st_mtime
            if path.name in existing_files:
                stored_mtime = existing_files[path.name]
                # Allow a small float tolerance or just exact check
                if current_mtime <= stored_mtime:
                    continue
                print(f"Updating {path.name} (modified)...")
            else:
                print(f"New file found: {path.name}")

            try:
                # 1. Deduplicate: Delete existing documents from THIS specific file
                collection.delete(where={"source": path.name})

                if suffix == ".pdf":
                    raw = read_pdf(path)
                    doc_type = "pdf"
                else:
                    raw = read_text_file(path)
                    doc_type = "markdown" if suffix == ".md" else "notes"

                # 2. Chunk and clean
                chunks = chunk_text(raw)
                chunks = [c for c in chunks if isinstance(c, str) and c.strip()]
                
                if not chunks:
                    continue

                # 3. Encode and Add
                embedder = get_embedder()
                embeddings = embedder.encode(chunks).tolist()
                
                # Use a stable ID format: filenamehash_chunkindex
                file_hash = str(abs(hash(path.name)))
                ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
                
                metadatas = [
                    {
                        "source": path.name,
                        "path": str(path),
                        "type": doc_type,
                        "mtime": current_mtime,
                    }
                    for _ in chunks
                ]

                collection.add(
                    ids=ids,
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                print(f"Indexed {len(chunks)} chunks from {path.name}")
            except Exception as e:
                print(f"Error indexing {path.name}: {e}")

if __name__ == "__main__":
    ingest_folder()
    print("Ingestion complete.")
