# Personal Search Engine — Knowledge Vault

A self-hosted, private semantic search engine for your personal documents. Upload PDFs, Markdown files, or plain-text notes and search through them using natural-language queries powered by vector embeddings. An optional AI synthesis feature uses Google Gemini to generate direct answers from your retrieved content.

## What It Does

- **Upload** PDF, Markdown (`.md`), and plain-text (`.txt`) documents into your personal vault.
- **Semantic search** — queries are matched by meaning, not just keywords, using sentence embeddings and a vector database.
- **Keyword boosting** — results are re-ranked to surface exact keyword matches alongside semantic ones.
- **Recency filtering** — optionally limit results to documents modified within a chosen number of days.
- **AI synthesis** — send the top results to Google Gemini and get a concise natural-language answer to your question.
- **Document browser** — see a list of all indexed files directly in the UI.

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
