# 🧠 Internalized Search Engine - Backend (Python)

Welcome to the architectural core of the **Knowledge Vault**. This backend is designed for high-precision semantic retrieval, secure session management, and AI-driven synthesis.

---

## 🏗️ 1. Core Architecture

The backend is built using **FastAPI** for high-speed asynchronous processing and **ChromaDB** for vector storage.

### 🧩 A. Semantic Ingestion (`app/ingest.py`)
This module handles the physical-to-digital transformation of your library.
*   **Recursive Chunking**: Splits documents into 200-word windows.
*   **Vectorization**: Uses `sentence-transformers/all-MiniLM-L6-v2` to map text into 384-dimensional mathematical space.
*   **Atomic Re-indexing**: Automatically deletes outdated file fragments before inserting new ones to prevent "phantom results."

### 🧠 B. Hybrid Search Engine (`app/main.py`)
Our retrieval logic doesn't just look for keywords; it understands intent.
*   **Semantic Score (70%)**: Distance-based similarity using AI vectors.
*   **Keyword Boost (30%)**: Exact match amplification to pinpoint names/proper nouns.
*   **Recency Decay**: Automatically prioritizes newer documents based on file timestamps.
*   **Line-Level Snippets**: Extracts the exact matching lines you need.

---

## 🔒 2. Security & State Management

The Knowledge Vault is now protected by a multi-layered security system.

### 🍪 Cookie-Based Sessions (State Management)
Instead of standard headers, we use **HTTP-Only Session Cookies**.
*   **Stateful Entry**: When you login, the backend issues a Signed JWT inside a cookie called `vault_session`.
*   **Protection**: The browser handles the cookie automatically, but Javascript cannot touch it, protecting you from XSS attacks.
*   **Verification**: Every sensitive request ([/search, /ask, /upload]) is wrapped in a `Depends(get_current_user)` check.

### 🛡️ OAuth & JWT Logic
*   **JWT Algorithm**: `HS256` ensures that session tokens cannot be forged.
*   **Password Security**: Managed via `Passlib (BCrypt)`, ensuring your vault password is encrypted with modern salting standards.

---

## 🤖 3. RAG & Synthesis (Gemini)

The `/ask` endpoint transforms the engine from "Search" to "Dialogue".
*   **Context Injection**: The engine takes the Top 5 most relevant fragments from your private vault.
*   **System Prompting**: Instructs Gemini to answer *strictly* based on the provided context, preventing hallucinations.

---

## 🚀 4. Setup & Deployment

### 🔑 Environment Variables (.env)
```env
GEMINI_API_KEY=your_google_ai_key
SECRET_KEY=generate_a_long_random_string
```

### 📥 Dependency Management
We use `uv` for ultra-fast, pinned installations.
```powershell
cd Backend
uv sync
uv run uvicorn app.main:app --reload
```

### 🧪 API Testing (Mock Admin)
*   **Default Username**: `admin`
*   **Default Password**: `vault-pass-123`
*(Change these in `app/main.py` before production).*
