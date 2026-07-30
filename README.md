# 🚀 AI Nexus RAG Engine

A production-grade, multi-user **Retrieval-Augmented Generation (RAG)** engine built with **FastAPI**, **LangGraph**, **ChromaDB**, **Local Cross-Encoder Reranking**, and **React + Vite + TypeScript**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![React](https://img.shields.io/badge/React-18-cyan.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.30+-purple.svg)

---

## ✨ Features

- **🔒 Secure JWT Authentication:** Multi-user isolation for vectors, SQLite parent pages, and chat sessions using bcrypt password hashing and signed JWT Bearer tokens.
- **📁 Multimodal Document Ingestion:** Supports **PDF, DOCX, XLSX, TXT, and Markdown**.
- **🖼️ Image Intelligence & Cost Guardrails:** Extracts images from PDFs/Office files, describes them with Vision LLMs, and uses **3KB minimum size filtering** plus **SHA-256 SQLite hash caching** to prevent API rate limit exhaustion.
- **⚡ Two-Stage Retrieval & Reranking:**
  - **Stage 1 (Bi-Encoder):** ChromaDB retrieves top $k=15$ candidate chunks using local CPU embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
  - **Stage 2 (Cross-Encoder):** `cross-encoder/ms-marco-MiniLM-L-6-v2` re-ranks candidates down to top 5 parent documents.
- **🛡️ 3-Way Decision Gate & Anti-Hallucination Fallback (FR-10):**
  - **`synthesize` ($\ge 0.0$):** High confidence ➔ grounded LLM answer with parent citations.
  - **`clarify` ($-2.0$ to $0.0$):** Partial match ➔ asks user to clarify query.
  - **`fallback` ($< -2.0$):** Low match ➔ deterministic fallback message (**0 LLM calls, $0 cost, 0 hallucination risk**).
- **🧠 Multi-Session & Long-Term User Memory:**
  - **Short-Term:** Per-session conversation history via LangGraph `MemorySaver` checkpointer.
  - **Long-Term:** SQLite key-value store (`memory.sqlite`) storing user facts/preferences across sessions with automatic prompt recall and periodic fact extraction.
- **🎨 Glassmorphism React UI Harness:** Built with Vite, TypeScript, and dark-mode styling.

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 18+

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# Run FastAPI server
uvicorn app.main:app --reload
```
Swagger API docs will be available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run the comprehensive unit test suite (13 passing tests across auth, ingestion, workflow, and memory):

```bash
cd backend
pytest tests/
```

---

## 🐳 Docker Deployment

Run both backend and frontend via Docker Compose:

```bash
docker-compose up --build
```

---

## 📜 License
MIT License. Built for AI Nexus.
