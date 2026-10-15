# Radha Krishna - Portfolio + talking 3D avatar

Black-and-grey portfolio with a 3D avatar visitors can talk to. The avatar answers from my profile with RAG and speaks with lip-sync. Everything used is free.

## Run it
Double-click `start.bat`, or:

    cd backend
    .venv\Scripts\python -m uvicorn app:app --port 8000

Then open http://localhost:8000 and click **Talk to me** (bottom right).
Open it through the server, not by double-clicking `index.html`: the 3D model and the API need it.

## How it works
| Part | What it uses | Cost |
|---|---|---|
| 3D avatar + lip-sync | TalkingHead (three.js), `frontend/avatars/model.glb` (my Avaturn T2 avatar) | Free |
| Voice in | Browser speech recognition (Chrome / Edge / Safari) | Free |
| Retrieval | BM25 over `backend/knowledge/*.md` (`backend/rag.py`) | Free |
| Answer | Google Gemini (`GEMINI_API_KEY` in `backend/.env`) | Free tier |
| Voice out | Microsoft Edge neural voice `en-IN-PrabhatNeural` via `edge-tts`, with word timings for lip-sync | Free |

## Change things
- **What the bot knows:** edit `backend/knowledge/profile.md`. Each `# Heading` is one retrievable chunk. Add more `.md` files if you like. Restart the server.
- **Page content:** edit the `ME` object at the top of the first `<script>` in `frontend/index.html`.
- **Voice:** `TTS_VOICE` in `backend/.env` (list them with `.venv\Scripts\edge-tts --list-voices`).
- **Model:** `GEMINI_MODEL` in `backend/.env` (default `gemini-flash-latest`).
- **Your own face:** make an avatar from a selfie at avaturn.me (free for non-commercial use), export the GLB, put it in `frontend/avatars/`, and change `AVATAR.url` in `index.html`.
- **Abuse limit:** `MAX_REQUESTS_PER_HOUR` per visitor IP (default 40).

## Deploying
The frontend is static, but the bot needs the backend running somewhere (Render, Railway, a VPS). Set the `.env` values as environment variables there. Never commit `backend/.env`.

Avatar made at avaturn.me (free for non-commercial use).
