# PSE - Personal Semantic Search Engine

A full-stack semantic search application that allows you to upload, index, and search through your personal documents using AI-powered embeddings and vector similarity search.

## 🚀 Features

- **Semantic Search**: Intelligent search using sentence transformers and vector embeddings
- **Multi-Format Support**: Upload and search PDFs, Markdown, and text files
- **Recency Boosting**: Prioritize newer documents in search results
- **Type Filtering**: Filter results by document type (PDF, Markdown, Notes)
- **Modern UI**: Clean, responsive React frontend with Tailwind CSS
- **Fast & Efficient**: ChromaDB vector database for quick similarity searches

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.13+
- **Vector Database**: ChromaDB for persistent vector storage
- **Embeddings**: Sentence Transformers for semantic encoding
- **Document Processing**: PyPDF2 for PDF extraction, text chunking with overlap
- **API Endpoints**:
  - `POST /search` - Semantic search with filters and recency boost
  - `POST /upload` - Upload and auto-index documents

### Frontend (React + TypeScript)
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **UI Components**: Lucide React icons

## 📦 Installation

### Prerequisites
- Python 3.13+
- Node.js 16+
- uv (Python package manager)

### Backend Setup

```bash
cd Backend
uv venv
uv pip install -e .
```

### Frontend Setup

```bash
cd Frontend
npm install
```

## 🚀 Running the Application

### Start Backend Server

```bash
cd Backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd Frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📖 Usage

1. **Upload Documents**: Use the upload interface to add PDFs, Markdown, or text files
2. **Search**: Enter your query in the search box
3. **Filter**: Apply filters by document type or recency
4. **Adjust Recency Boost**: Control how much weight is given to newer documents

## 🔧 Configuration

Backend configuration is managed in `Backend/app/config.py`:
- Embedding model selection
- ChromaDB directory
- Data storage paths
- Collection settings

## 📁 Project Structure

```
PSE/
├── Backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application & endpoints
│   │   ├── ingest.py        # Document ingestion & chunking
│   │   └── config.py        # Configuration settings
│   ├── data/                # Document storage
│   │   ├── pdfs/
│   │   ├── markdown/
│   │   └── notes/
│   ├── chroma_db/           # Vector database storage
│   └── pyproject.toml       # Python dependencies
│
└── Frontend/
    ├── src/
    │   ├── App.tsx          # Main application component
    │   └── main.tsx         # Entry point
    ├── package.json         # Node dependencies
    └── vite.config.ts       # Vite configuration
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- ChromaDB
- Sentence Transformers
- PyPDF2
- LangChain

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Axios


