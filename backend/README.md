# AI Audio/Video Q&A Assistant Backend

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Profile
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update profile

### Upload
- `POST /api/upload/` - Upload audio/video file

### YouTube
- `POST /api/youtube/process` - Process YouTube URL

### Chat
- `POST /api/chat/` - Ask question
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/history` - Delete chat history

### Sources
- `GET /api/sources` - List media sources
- `DELETE /api/sources/{source_id}` - Delete source

### Health
- `GET /api/health/` - Health check

## Sample API Requests

### Signup
```json
POST /api/auth/signup
{
  "email": "user@example.com",
  "password": "password123"
}
```
Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Login
```json
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```
Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Upload File
```
POST /api/upload/
Content-Type: multipart/form-data
Authorization: Bearer <token>
file: <audio/video file>
```
Response:
```json
{
  "message": "File processed successfully",
  "source_id": 1,
  "segments": 45,
  "chunks_stored": 12
}
```

### Ask Question
```json
POST /api/chat/
Authorization: Bearer <token>
{
  "question": "What was discussed about AI?",
  "source_id": 1
}
```
Response:
```json
{
  "answer": "The speaker discussed the future of AI...",
  "start_time": 45.5,
  "end_time": 60.2,
  "matched_text": "Future of AI includes...",
  "confidence_score": 0.85
}
```
# AI Audio/Video Q&A Assistant Backend

FastAPI backend for authenticated audio/video ingestion, YouTube processing, Whisper transcription, timestamp-aware chunking, ChromaDB retrieval, and chat history.

RAG answers are generated with Ollama. Install Ollama, then run:

```bash
ollama pull llama3.2:3b
ollama serve
```

## Setup

```bash
cd backend
python -m venv ../.venv
../.venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Install FFmpeg separately and make sure `ffmpeg` and `ffprobe` are available on your PATH.

## API Examples

Signup:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"demo@example.com\",\"password\":\"secret123\"}"
```

Chat:

```json
{
  "question": "What did the speaker say about deployment?",
  "source_id": 1
}
```

Response:

```json
{
  "answer": "The login validation is explained in the section about form checks.",
  "timestamps": [
    {
      "start": "03:12",
      "end": "03:57",
      "start_seconds": 192.0,
      "end_seconds": 237.0
    }
  ],
  "source": "React Authentication Tutorial",
  "start_time": 192.0,
  "end_time": 237.0,
  "matched_text": "...",
  "confidence_score": 0.82
}
```

## Routes

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/profile`
- `PUT /api/profile`
- `POST /api/upload`
- `POST /api/youtube`
- `POST /api/chat`
- `GET /api/chat/history`
- `DELETE /api/chat/history`
- `GET /api/sources`
- `DELETE /api/sources/{source_id}`
- `GET /api/health`
