from pathlib import Path
from typing import List, Tuple
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from .config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME


client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(COLLECTION_NAME)
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)


def clean_text_for_storage(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: List[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        t = clean_text_for_storage(t)
        if t.strip():
            pages.append(t)
    return "\n".join(pages)


def read_text_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return clean_text_for_storage(raw)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[str]:
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


def encode_single_chunk(chunk: str) -> Tuple[str, List[float] | None]:
    clean_chunk = clean_text_for_storage(chunk)
    if not clean_chunk.strip():
        return clean_chunk, None

    try:
        emb = embedder.encode([clean_chunk])
        vec = emb[0]
        vec_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        return clean_chunk, vec_list
    except Exception as e:
        print("[encode-skip] error:", repr(e))
        print("[encode-skip] preview:", repr(clean_chunk[:160]))
        return clean_chunk, None


def encode_chunks_parallel(
    chunks: List[str],
    max_workers: int = 4,
) -> Tuple[List[str], List[List[float]]]:
    if not chunks:
        return [], []

    final_chunks: List[str] = []
    final_embeddings: List[List[float]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(encode_single_chunk, c): idx for idx, c in enumerate(chunks)}
        for fut in as_completed(futures):
            clean_chunk, embedding = fut.result()
            if embedding is None:
                continue
            final_chunks.append(clean_chunk)
            final_embeddings.append(embedding)

    return final_chunks, final_embeddings


def ingest_folder() -> None:
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
                raw_text = read_pdf(path)
                doc_type = "pdf"
            else:
                raw_text = read_text_file(path)
                doc_type = "markdown" if suffix == ".md" else "notes"

            chunks = chunk_text(raw_text)
            print(f"[ingest] {path} -> {len(chunks)} raw chunks")
            if chunks:
                print(
                    "[ingest] first chunk type:",
                    type(chunks[0]),
                    "preview:",
                    repr(str(chunks[0])[:80]),
                )

            if not chunks:
                print(f"[ingest] Skipping {path} (no chunks)")
                continue

            cleaned_chunks, embeddings_list = encode_chunks_parallel(chunks, max_workers=4)

            if not cleaned_chunks or not embeddings_list:
                print(f"[ingest] Skipping {path} (no embeddings produced)")
                continue

            if len(cleaned_chunks) != len(embeddings_list):
                n = min(len(cleaned_chunks), len(embeddings_list))
                print(
                    f"[ingest] Warning: embeddings={len(embeddings_list)} "
                    f"chunks={len(cleaned_chunks)} -> truncating to {n} for {path}"
                )
                cleaned_chunks = cleaned_chunks[:n]
                embeddings_list = embeddings_list[:n]
                
            if not cleaned_chunks or not embeddings_list:
                print(f"[ingest] Skipping {path} (nothing left after truncation)")
                continue

            docs_safe = [clean_text_for_storage(c) for c in cleaned_chunks]

            ids = [f"{doc_id_counter}_{i}" for i in range(len(docs_safe))]
            doc_id_counter += 1

            metadatas = [
                {
                    "source": path.name,
                    "path": str(path),
                    "type": doc_type,
                    "mtime": path.stat().st_mtime,
                }
                for _ in docs_safe
            ]

            collection.add(
                ids=ids,
                documents=docs_safe,
                embeddings=embeddings_list,
                metadatas=metadatas,
            )
            print(f"[ingest] Indexed {len(docs_safe)} chunks from {path}")


if __name__ == "__main__":
    ingest_folder()
    print("Ingestion complete.")
