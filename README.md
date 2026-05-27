# 🚀 AI Audio/Video RAG Assistant

> A production-grade AI-powered media intelligence platform that transforms YouTube videos, audio, and uploaded media into an interactive timestamp-aware conversational experience.

---

## ✨ Overview

AI Audio/Video RAG Assistant allows users to:

- 🎥 Process YouTube videos
- 🎵 Upload audio/video files
- 🧠 Transcribe media using AI
- 🔍 Perform timestamp-aware semantic retrieval
- 💬 Chat with media content using RAG
- ⏱️ Get answers with exact timestamps
- 📚 Manage chat history and processed sources
- 🤖 Use Ollama-powered local LLM inference

---

# 🌟 Features

## 🎥 YouTube Processing

- Paste YouTube URL
- Fetch thumbnail, title, duration, channel
- Download audio using `yt-dlp`
- Handle long-duration videos
- Background processing support
- Real-time processing progress

---

## 📁 Audio & Video Upload

### Supported Formats

- mp3
- wav
- m4a
- aac
- flac
- mp4
- mov
- mkv
- webm

### Features

- Drag & drop upload
- Audio extraction from video
- Background indexing
- Processing persistence

---

## 🧠 AI Transcription

Powered by:

- `faster-whisper`

### Features

- Fast transcription
- Timestamp generation
- Multi-language support
- Long-video handling
- CPU/GPU support

---

## 🔍 Hybrid RAG Pipeline

Uses:

- Semantic + timestamp chunking
- ChromaDB vector storage
- Sentence-transformer embeddings
- Ollama LLM inference

### Capabilities

- Context-aware retrieval
- Timestamp-based answers
- Grounded AI responses
- No hallucinated responses

---

## 💬 AI Chat Experience

Users can ask:

- “Summarize this video”
- “Where does he explain APIs?”
- “What mistakes are discussed?”
- “Show timestamps for evaluation metrics”

The chatbot:

- Retrieves relevant transcript chunks
- Generates grounded responses
- Returns timestamp references
- Opens media directly at timestamps

---

## 📚 Chat History

- Persistent conversations
- Rename chat
- Delete chat
- Continue existing sessions
- Filter conversations

---

## ⚡ Background Job System

Supports:

- Long-duration media
- Real-time progress tracking
- Page refresh recovery
- Persistent processing state
- Cancellation support

---

# 🧩 Tech Stack

## Frontend

- React
- Vite
- TailwindCSS
- Framer Motion
- Axios

---

## Backend

- FastAPI
- SQLAlchemy
- SQLite/PostgreSQL-ready
- JWT Authentication
- Background Tasks

---

## AI & RAG

- Ollama
- ChromaDB
- Sentence Transformers
- faster-whisper

---

## Media Processing

- FFmpeg
- yt-dlp

---

# 🏗️ System Architecture

```text
User Input
   │
   ├── Upload File
   │
   └── YouTube URL
           │
           ▼
Background Processing Job
           │
           ▼
Audio Extraction (FFmpeg)
           │
           ▼
Transcription (Whisper)
           │
           ▼
Hybrid Timestamp Chunking
           │
           ▼
Embedding Generation
           │
           ▼
ChromaDB Vector Storage
           │
           ▼
RAG Retrieval Pipeline
           │
           ▼
Ollama LLM Response
           │
           ▼
Timestamp-Based AI Answers
```

---

# 📂 Project Structure

```text
transcriber/
│
├── backend/
│   ├── app/
│   ├── storage/
│   ├── chroma_storage/
│   ├── requirements.txt
│   └── .env.local
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
└── README.md
```

---

# 🔥 Core AI Pipeline

## 1️⃣ Media Processing

- Upload or YouTube ingestion
- Metadata extraction
- Audio conversion

---

## 2️⃣ Transcription

- Whisper transcription
- Timestamp alignment
- Language detection

---

## 3️⃣ Hybrid Chunking

Combines:

- Semantic chunking
- Timestamp chunking

### Chunk Configuration

- Chunk size: 30–60 seconds
- Overlap: 5–10 seconds

---

## 4️⃣ Embeddings

Generated using:

```bash
sentence-transformers/all-MiniLM-L6-v2
```

---

## 5️⃣ Vector Search

Stored in:

- ChromaDB

Supports:

- similarity search
- semantic retrieval
- timestamp metadata filtering

---

## 6️⃣ RAG Chat

Workflow:

- Retrieve relevant chunks
- Build grounded prompt
- Query Ollama
- Return timestamp-based answer

---

# 🎯 Example Chat

## User

```text
Where does he explain APIs?
```

## AI Response

```text
The speaker explains APIs around:

⏱️ 12:14 - 14:32

He discusses:
- REST APIs
- FastAPI routing
- Request handling
- API integration workflow
```

---

# 🛠️ Installation

## 1️⃣ Clone Repository

```bash
git clone <your-repo-url>
cd transcriber
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

#### Windows

```bash
.venv\Scripts\activate
```

---

## 3️⃣ Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## 4️⃣ Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

---

# ⚙️ Environment Variables

Create:

```text
backend/.env.local
```

Example:

```env
DATABASE_URL=sqlite:///./app.db

SECRET_KEY=your-secret-key

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

WHISPER_MODEL=tiny
WHISPER_DEVICE=cpu

YTDLP_COOKIES_FILE=
```

---

# 🎥 Install FFmpeg

Download FFmpeg and add:

```text
ffmpeg/bin
```

to system PATH.

Verify:

```bash
ffmpeg -version
```

---

# 🤖 Install Ollama

Install Ollama and pull model:

```bash
ollama pull llama3.2:3b
```

Run:

```bash
ollama serve
```

---

# 🚀 Run Application

## Backend

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

⚠️ IMPORTANT:

Do NOT use:

```bash
uvicorn app.main:app --reload
```

for long YouTube processing.

---

## Frontend

```bash
cd frontend
npm run dev
```

---

# 📡 API Endpoints

## Authentication

- POST `/api/auth/signup`
- POST `/api/auth/login`
- GET `/api/auth/me`

---

## YouTube

- POST `/api/youtube/metadata`
- POST `/api/youtube/process`

---

## Upload

- POST `/api/upload/process`

---

## Jobs

- GET `/api/jobs/{job_id}`
- GET `/api/jobs/active`
- POST `/api/jobs/{job_id}/cancel`

---

## Sources

- GET `/api/sources`
- GET `/api/sources/{source_id}/media`

---

## Chat

- POST `/api/chat`
- GET `/api/chat/history`

---

# 🧪 Testing

## Test YouTube

- Short video
- Long-duration course
- Public video
- Bot-blocked video

---

## Test Upload

- Audio upload
- Video upload
- Large files

---

## Test Chat

- Timestamp retrieval
- Summaries
- Topic-based questions

---

# 🔐 Security Features

- JWT Authentication
- Protected APIs
- User-specific vector filtering
- No cross-user data leakage
- Grounded RAG responses

---

# 🎨 UI/UX Highlights

- Cinematic AI interface
- Animated transitions
- Modern gradient system
- Real-time progress UI
- Immersive chat experience
- Timestamp jump navigation

---

# 📈 Future Improvements

- Multi-source chat
- Live meeting transcription
- Real-time streaming transcription
- Team collaboration
- PDF + media hybrid RAG
- GPU acceleration
- Multi-modal embeddings

---

# 👩‍💻 Author

## Subiksha Thangavel

AI & Data Science Enthusiast focused on:

- RAG Systems
- AI Engineering
- Backend Development
- Media Intelligence Systems
- LLM Applications

---

# ⭐ Final Note

This project is designed as a real-world AI engineering system that combines:

- AI transcription
- Vector databases
- Retrieval-Augmented Generation
- Semantic search
- Timestamp intelligence
- Local LLM orchestration

into a complete production-grade AI media assistant.
