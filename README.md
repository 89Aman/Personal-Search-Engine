# Personal Search Engine — Knowledge Vault

A self-hosted, private semantic search engine for your personal documents. Upload PDFs, Markdown files, or plain-text notes and search through them using natural-language queries powered by vector embeddings. An optional AI synthesis feature uses Google Gemini to generate direct answers from your retrieved content.

## What It Does

- **Upload** PDF, Markdown (`.md`), and plain-text (`.txt`) documents into your personal vault.
- **Semantic search** — queries are matched by meaning, not just keywords, using sentence embeddings and a vector database.
- **Keyword boosting** — results are re-ranked to surface exact keyword matches alongside semantic ones.
- **Recency filtering** — optionally limit results to documents modified within a chosen number of days.
- **AI synthesis** — send the top results to Google Gemini and get a concise natural-language answer to your question.
- **Document browser** — see a list of all indexed files directly in the UI.

## Tech Stack

### Backend
| Technology | Role |
|---|---|
| **Python 3.12** | Runtime |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **ChromaDB** | Persistent vector database for storing embeddings |
| **Sentence Transformers** (`all-MiniLM-L6-v2`) | Generates text embeddings for semantic search |
| **Google Gemini** (`gemini-2.0-flash`) | AI answer synthesis |
| **pypdf** | PDF text extraction |
| **python-dotenv** | Environment variable management |
| **uv** | Fast Python dependency management |

### Frontend
| Technology | Role |
|---|---|
| **React 19** | UI framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Build tool and dev server |
| **Tailwind CSS** | Utility-first styling |
| **Axios** | HTTP client for API calls |
| **Lucide React** | Icon library |
| **Nginx** | Serves the built frontend in production |

### Infrastructure
| Technology | Role |
|---|---|
| **Docker** | Containerization for both frontend and backend |
| **Google Cloud Build** | CI/CD pipeline |
| **Google Cloud Run** | Serverless container hosting |

## Project Structure

```
Personal-Search-Engine/
├── Backend/          # FastAPI application
│   ├── app/
│   │   ├── main.py   # API routes (search, upload, ask, documents)
│   │   ├── ingest.py # Document ingestion & chunking pipeline
│   │   └── config.py # Environment & path configuration
│   ├── Dockerfile
│   └── pyproject.toml
└── Frontend/         # React + TypeScript application
    ├── src/
    │   └── App.tsx   # Main UI component
    ├── Dockerfile
    └── package.json
```

## Getting Started

### Prerequisites
- Docker (recommended), or Python 3.12+ and Node.js 20+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (optional — only needed for AI synthesis)

### Running Locally

**Backend**
```bash
cd Backend
cp .env.example .env   # add your GEMINI_API_KEY
pip install uv
uv pip install .
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd Frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

The UI will be available at `http://localhost:5173`.

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for AI synthesis | *(empty — feature disabled)* |
| `FRONTEND_URL` | Allowed CORS origin for the frontend | *(all origins allowed)* |
| `ENV` | `development` or `production` | Auto-detected |
| `VITE_API_BASE_URL` | Backend URL used by the frontend | `http://localhost:8000` |
