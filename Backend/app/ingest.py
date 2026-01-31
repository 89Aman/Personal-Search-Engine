from pathlib import Path
from typing import List
import time

import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from app.config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME


# Persistent Chroma client
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(COLLECTION_NAME)
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)


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
    # We'll use the filename as a prefix to prevent duplicate chunks per re-ingestion
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

            try:
                # 1. Deduplicate: Delete existing documents from THIS specific file
                # This prevents bloat when re-running ingestion or uploading same file
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
                embeddings = embedder.encode(chunks).tolist()
                
                # Use a stable ID format: filenamehash_chunkindex
                file_hash = str(abs(hash(path.name)))
                ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
                
                metadatas = [
                    {
                        "source": path.name,
                        "path": str(path),
                        "type": doc_type,
                        "mtime": path.stat().st_mtime,
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
