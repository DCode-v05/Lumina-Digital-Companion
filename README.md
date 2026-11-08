# Lumina-Digital-Companion

A study companion for students: a chat tutor that remembers facts about you, turns goals into day-by-day tasks, generates quizzes for them, reads the mood of your messages, and runs a small coin and rewards system. FastAPI backend, React and TypeScript frontend.

## What it does

- **Routed chat.** Each message is first classified into one of four modes, and each mode runs on a different Groq model with its own system prompt:

  | Mode | Persona | Model |
  | --- | --- | --- |
  | `primary` | companion | `llama-3.1-8b-instant` |
  | `academic` | research guide | `openai/gpt-oss-120b` |
  | `reasoning` | math, code, logic | `llama-3.3-70b-versatile` |
  | `teaching` | step-by-step tutor | `meta-llama/llama-4-maverick-17b-128e-instruct` |

  If a call fails it retries on the reasoning model (or the primary model if reasoning was the one that failed).
- **Memory and goals from one call.** The chat call asks for a JSON object with the reply, an optional chat title, `new_user_facts` and an optional `suggested_goal`. Facts go into a Redis-backed profile; a suggested goal is created automatically.
- **Goals.** A goal with a timeframe is broken into one task per day or week. Reminders and 5-question quizzes are generated on demand from the stored subtasks.
- **Emotion tracking.** Each message goes through `j-hartmann/emotion-english-distilroberta-base`. The result is logged in `emotion_logs`, and emotions from the last 15 minutes with a score above 0.5 are added to the chat prompt.
- **Coins and rewards.** +50 coins on first login, +20 for each daily check-in. The model generates a catalogue of collectible rewards from the user's favourites, cached per user, which can be redeemed with coins.
- **Integrations.** GitHub (list, count, create, inspect, rename, delete repos) and OneNote through Microsoft Graph (read only). Both work from the Integrations dashboard or from chat phrases like "how many repos do I have". Tokens are stored per provider in the `integrations` table.
- **Auth.** Email and password with bcrypt and JWT.

State is split: PostgreSQL holds users, goals, emotion logs, facts, integrations and purchased rewards; Redis holds chat sessions, message history and the rolling profile.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis, Groq SDK, transformers and torch, python-jose, bcrypt
- Frontend: React 18, Vite, TypeScript, Tailwind, framer-motion, react-router, react-markdown with KaTeX and syntax highlighting, axios

## Setup

You need Python 3, Node, PostgreSQL, Redis and a Groq API key.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env            # fill in GROQ_API_KEY, Postgres, Redis, SECRET_KEY
uvicorn main:app --reload        # http://localhost:8000
```

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Tables are created on startup.

## Project structure

```
backend/
  main.py                FastAPI app and routes (36), chat orchestration
  groq_service.py        model routing, prompts, goal, quiz and reward generation
  emotion_service.py     emotion classification and logging
  github_service.py      GitHub REST calls
  onenote_service.py     Microsoft Graph calls
  integration_service.py re-exports the integration functions
  redis_client.py        sessions, history, profile memory
  models.py, schemas.py, auth.py, database.py, config.py
frontend/src/
  App.tsx                chat UI and profile modal
  api.ts                 axios client with the JWT attached
  components/            GoalDashboard, RewardDashboard, IntegrationDashboard, theme
  pages/                 Login, Register
```

## Notes

- `config.py` falls back to hard-coded Postgres credentials, a default JWT secret and `allow_origins=["*"]` when env vars are missing. Set them in `.env`.
- `google-generativeai` is in `requirements.txt` but nothing in the backend imports it.
