from pathlib import Path
from typing import List
import time

import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from .config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME


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
    chunk_size: int = 512,
    overlap: int = 64,
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
        if chunk:
            chunks.append(chunk)
        i += step

    return chunks


def ingest_folder() -> None:
    """Index all PDFs / markdown / notes under data/."""
    doc_id_counter = int(time.time())

    for sub in ["pdfs", "markdown", "notes"]:
        folder = DATA_DIR / sub
        if not folder.exists():
            continue

        for path in folder.glob("*"):
            if not path.is_file():
                continue

            suffix = path.suffix.lower()

            if suffix == ".pdf":
                raw = read_pdf(path)
                doc_type = "pdf"
            else:
                raw = read_text_file(path)
                doc_type = "markdown" if suffix == ".md" else "notes"

            # Chunk and clean
            chunks = chunk_text(raw)
            chunks = [
                c for c in chunks
                if isinstance(c, str) and c.strip()
            ]
            if not chunks:
                print(f"Skipping {path} (no valid chunks)")
                continue

            # Final safety: ensure all are strings
            chunks = [str(c) for c in chunks]

            # Encode
            embeddings = embedder.encode(chunks)

            # Make sure embeddings are plain Python lists
            if hasattr(embeddings, "tolist"):
                embeddings_list = embeddings.tolist()
            else:
                embeddings_list = [list(vec) for vec in embeddings]

            ids = [f"{doc_id_counter}_{i}" for i in range(len(chunks))]
            doc_id_counter += 1

            metadatas = [
                {
                    "source": path.name,
                    "path": str(path),
                    "type": doc_type,
                    "mtime": path.stat().st_mtime,  # for recency bias
                }
                for _ in chunks
            ]

            collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings_list,
                metadatas=metadatas,
            )


if __name__ == "__main__":
    ingest_folder()
    print("Ingestion complete.")
