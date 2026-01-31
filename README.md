# Knowledge Vault: Personal Semantic Search Engine

Knowledge Vault is a high-performance, private semantic intelligence system designed for indexing and querying personal documents (PDFs, Markdown, Notes). It leverages state-of-the-art Embeddings, Vector Databases, and Large Language Models (LLMs) to provide a "Google-like" search experience over your private data.

---

## 🚀 Key Features

- **Semantic Search**: Understands the *meaning* of your queries, not just keywords.
- **RAG Pipeline**: Retrieval-Augmented Generation using Google Gemini for context-aware answering.
- **Hybrid Scoring**: Combines vector proximity with keyword density and recency-based boosting.
- **Visual Excellence**: Premium dark-mode interface with glassmorphic accents and smooth micro-animations.
- **Secure Access**: JWT-based session management with Google and GitHub OAuth integration.
- **Multi-Format Support**: Native processing for PDFs, Markdown, and plaintext notes.

---

## 🛠 Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Running locally)
- **AI Synthesis**: [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **Auth**: JWT via `python-jose`, OAuth via `Authlib`

### Frontend
- **Framework**: [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [TailwindCSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)

---

## 🧠 Internal Processes & Architecture

### 1. The Ingestion Pipeline (`ingest.py`)
When a document is uploaded or added to the `data/` directory:
1. **Extraction**: `PyPDF2` (for PDFs) or standard text reading (for `.md`/`.txt`) extracts the raw text.
2. **Chunking**: The text is split into overlapping word-based chunks (size: 200 words, overlap: 40 words). Overlap ensures semantic continuity across chunks.
3. **Embedding**: Each chunk is passed through the `SentenceTransformer` model to generate a 384-dimensional vector representation.
4. **Indexing**: Chunks, vectors, and metadata (source name, file type, modification time) are stored in **ChromaDB**.

### 2. The Retrieval Engine (`main.py -> /search`)
When you search:
1. **Vectorization**: Your query is embedded using the same `SentenceTransformer` model.
2. **Nearest Neighbor Search**: ChromaDB calculates the cosine distance between your query vector and all stored document chunks.
3. **Custom Scoring**:
   - **Base Score**: Inverse of vector distance ($1 / (1 + distance)$).
   - **Keyword Boost**: Direct matching of query words within the chunk (up to 30% weight).
   - **Recency Boost**: Newer documents are weighted higher based on a configurable decay function.
4. **Deduplication**: The engine filters out redundant snippets from the same source to provide a diverse result set.

### 3. AI Synthesis (RAG)
If "Synthesize with AI" is clicked:
1. The top 5 most relevant fragments are gathered.
2. A prompt is constructed: `Use context to answer: [Fragments] \n\n Question: [Query]`.
3. Sent to **Gemini 1.5 Flash** for a concise, grounded response.

---

## 🌐 GCP Deployment Guide

This project is optimized for deployment on **Google Cloud Platform** using **Cloud Run**.

### Prerequisites
1.  GCP Project with billing enabled.
2.  Google AI SDK Key (Gemini).
3.  OAuth Client IDs (from Google Cloud Console -> Credentials).

### Automated Build with Cloud Build
Use the provided `Dockerfile`s to build images.

```bash
# Build Backend
gcloud builds submit --tag gcr.io/[PROJECT_ID]/vault-backend ./Backend

# Build Frontend
gcloud builds submit --tag gcr.io/[PROJECT_ID]/vault-frontend --build-arg VITE_API_BASE_URL=[BACKEND_URL] ./Frontend
```

### Deploying to Cloud Run
1.  **Backend**: Set the following environment variables:
    - `GEMINI_API_KEY`: Your Google AI key.
    - `FRONTEND_URL`: The URL of your deployed frontend.
    - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: For OAuth.
    - `SECRET_KEY`: A long random string.
    - `ENV`: `production`
2.  **Frontend**: Standard Cloud Run deployment (Port 80).

### Data Persistence
ChromaDB uses local storage (`chroma_db/`). On Cloud Run, this is ephemeral. For production:
-   **Option A**: Use **Cloud Storage FUSE** to mount a GCS bucket to `/app/chroma_db`.
-   **Option B**: Swap ChromaDB for **Vertex AI Search** or a managed vector DB.

---

## 💻 Local Setup

1.  **Backend**:
    ```bash
    cd Backend
    uv pip install -r pyproject.toml
    # Set your .env variables
    python -m uvicorn app.main:app --reload
    ```
2.  **Frontend**:
    ```bash
    cd Frontend
    npm install
    npm run dev
    ```

---
*Created as a demonstration of production-grade Backend & Full-stack engineering for Google Cloud roles.*
