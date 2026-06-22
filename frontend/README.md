# Phase 8 Frontend Demo

This folder contains a small Streamlit demo for the Phase 8 backend.

## Files

- `app.py`: landing page
- `pages/1__Chat.py`: streaming chat demo
- `pages/2__RAG.py`: upload and ask over one document
- `pages/3__Research.py`: run research modes and inspect steps
- `pages/4__Observability.py`: traces, agent runs, and cost summary
- `utils/api_client.py`: shared HTTP client
- `utils/streaming.py`: small streaming helper

## Run

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

## Backend URL

The app reads `BACKEND_URL` and defaults to `http://localhost:8000`.

Examples:

```bash
BACKEND_URL=http://localhost:8002 streamlit run frontend/app.py
```
