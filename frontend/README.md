# AI Audio/Video Q&A Assistant Frontend

React + Vite client for the timestamp-based RAG backend.

## Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The app runs at `http://127.0.0.1:5173` and expects the backend at `VITE_API_BASE_URL`.
The `dev` script builds the React app and serves `dist/` with a small Python static server. This avoids Vite's dependency optimizer issue on some Windows OneDrive folders with Node 24.

## Features

- Signup and login with JWT stored in `localStorage`
- Protected app routes
- Profile and settings forms
- Audio/video upload workflow
- YouTube link workflow
- Source selection before chat
- Timestamped answers
- Chat history and source deletion
- Responsive Tailwind UI
