# Lumina — Digital Student Companion

**A full-stack AI study companion: a tutor chat that remembers you, turns goals into day-by-day plans, quizzes you on them, reads your mood, and runs a coin-based reward economy on top.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white) ![React](https://img.shields.io/badge/React_18-61DAFB?style=flat&logo=react&logoColor=black) ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white) ![Groq](https://img.shields.io/badge/Groq-F55036?style=flat&logo=groq&logoColor=white) ![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=flat&logo=huggingface&logoColor=black)

## Overview

Lumina is a study companion app for students. Instead of being one more chatbot, it tries to act like a tutor that keeps track of you. It pulls long-term facts out of your conversations, plans your goals into daily or weekly tasks, checks whether you're keeping up, generates quizzes on what you said you wanted to learn, and reacts to the emotional tone of your messages. There is also a coin economy: you earn coins for showing up and finishing things, and spend them on collectible "rewards" the AI generates around your interests.

It's a full-stack build: a FastAPI backend using PostgreSQL and Redis, a React 18 + TypeScript frontend, four Groq-hosted language models behind a routing layer, a HuggingFace transformer for emotion classification, and live integrations with GitHub and Microsoft OneNote. I wrote all of it: the backend services, the prompts, the React UI and the integrations. It's the largest project in my portfolio, with about 36 routes, a six-table data model and four large frontend dashboards.

## Key Features

- **Routed AI chat with four personas.** Every message is first classified into one of four modes (general companion, research guide, problem solver, tutor). Each mode runs on a different Groq model with its own system prompt and tone.
- **Persistent memory ("user facts").** The model is told to extract durable facts about you ("studying Biology", "visual learner") and skip temporary ones ("I'm hungry"). New facts are de-duplicated against your profile and appended, so the assistant carries context across chats.
- **Goal planning and decomposition.** State a goal with a timeframe ("learn React in 2 weeks") and Lumina creates a goal and splits it into one task per day or week, with an hour-by-hour breakdown for single-day goals.
- **Auto-created goals from chat.** If you mention a goal with a deadline mid-conversation, the chat endpoint picks up the `suggested_goal` in the model's JSON output and creates the goal for you.
- **Accountability reminders.** A reminders endpoint compares days elapsed against the task list and writes a short nudge: encouragement if you're on track, a pointer to the specific pending task if you're behind.
- **Auto-generated quizzes.** For learning goals, Lumina generates a 5-question multiple-choice quiz. It skips quizzes for plain chores ("buy groceries").
- **Emotion tracking.** Each message runs through a DistilRoBERTa emotion classifier. Detected emotions are logged with a confidence score, and the recent emotional summary goes back into the chat context so the assistant can respond to your mood.
- **Coin economy and gamification.** Coins for first login (+50) and daily check-ins (+20), a transaction history, and a redeem flow that tracks purchased rewards.
- **AI-generated, interest-based rewards.** Based on your stated favourites, the model generates a catalogue of collectible items across four rarity tiers (Common / Rare / Epic / Legendary) with coin costs and icons, cached per user.
- **GitHub integration (full CRUD).** Connect a Personal Access Token and list, count, create, inspect, rename, re-describe or delete repositories, either from the Integrations dashboard or by asking in plain English in chat ("how many repos do I have?", "create repo called my-project").
- **OneNote integration (read-only).** Connect a Microsoft Graph token to list pages, count them, browse sections and open a specific page.
- **JWT auth.** Email/password registration and login with bcrypt-hashed passwords and JWT access tokens.
- **Chat UI.** Markdown with GitHub-flavored markdown, KaTeX math and Prism syntax highlighting, framer-motion animations, light/dark theme, and a mode badge on each message so you can see which persona answered.

## How It Works

The backend is FastAPI and holds all the state. The frontend is a React/Vite client for chat, dashboards and auth. State lives in two places: PostgreSQL for durable records (users, goals, emotion logs, facts, integrations, purchases) and Redis for chat sessions, message history and the rolling user profile.

### Request routing and the four-model setup

There is no single model. A small model (`llama-3.1-8b-instant`) first classifies each message into one of four modes, and each mode runs on a model picked for the job:

| Mode | Persona | Model |
| --- | --- | --- |
| `primary` | Companion / emotional support | `llama-3.1-8b-instant` |
| `academic` | Research guide | `openai/gpt-oss-120b` |
| `reasoning` | Problem solver (math/code/logic) | `llama-3.3-70b-versatile` |
| `teaching` | Step-by-step tutor | `meta-llama/llama-4-maverick-17b-128e-instruct` |

If a model call fails, it retries on the reasoning model (or the primary model if reasoning was the one that failed), so one bad call doesn't kill the response.

### Structured JSON outputs

Every chat call uses Groq's JSON-object response format with a strict schema instruction. The model returns one object holding the `response` text, an optional chat `title` (first message only), `new_user_facts` for memory, and an optional `suggested_goal` with title, duration, unit and priority. The backend parses it, trims to the first `{`…`}` it finds, and falls back to raw text if parsing fails. That is how memory updates and goal creation happen as a side effect of an ordinary chat turn, without separate calls.

### Memory and context assembly

Before each model call the backend builds context from three sources: the user's stored profile (accumulated facts), a summary of recent emotions (last 15 minutes, only those scored above 0.5), and the trimmed chat history (last ~10 messages). After the reply, new facts are appended to the Redis-backed profile and expired temporary facts are cleaned up.

### Emotion pipeline

Emotion analysis uses the HuggingFace `transformers` pipeline with `j-hartmann/emotion-english-distilroberta-base`, a DistilRoBERTa text classifier that scores a set of emotion labels. The top label and its score are logged to an `emotion_logs` table per message. The recent-emotion summary is injected into the chat prompt, which is how the assistant knows to acknowledge stress before jumping to a solution.

### Goal lifecycle

A goal is created explicitly or detected from chat. Decomposition normalizes the duration to the chosen granularity (weeks to days, months to weeks, etc.), then asks the reasoning model for a labelled task list ("Day 1: …", "Week 2: …") covering every interval. Subtasks and generated quizzes are stored as JSON on the goal row. Reminders and quizzes are generated on demand from those subtasks.

### Integrations

GitHub calls hit the REST API (`api.github.com`) with the user's stored token. OneNote calls hit Microsoft Graph (`graph.microsoft.com/v1.0`) as read-only operations. The chat endpoint has an intent detector that matches phrases like "list repos" or "how many pages" and sends them straight to the integration service, so you can manage repos from the chat. Tokens are stored per provider in an `integrations` table.

### Frontend

The React app is a single-page client with routes for login/register and the main workspace. `App.tsx` holds the chat surface (message list, mode badges, markdown, math and code highlighting, profile/memory modal). Three dashboards cover the rest: `GoalDashboard` (goals, subtasks, quizzes), `RewardDashboard` (coin balance, catalogue, redeem) and `IntegrationDashboard` (connect/disconnect GitHub and OneNote). Axios wraps the API with the JWT attached, framer-motion handles transitions, and a theme provider toggles light/dark.

## Results / Highlights

- **About 36 routes** across auth, chats, goals (plus decompose / quiz / reminders), rewards/redeem, profile, chat, and the GitHub/OneNote integration routes.
- **Four-model routing** with a fallback path, all behind one chat endpoint.
- **Six-table data model**: users (coins, coin history, favourites, rewards cache), emotion logs, goals, user facts, integrations and purchased rewards.
- **Reward catalogue** of about 50 AI-generated items per user across four rarity tiers (Common 20–50, Rare 50–150, Epic 150–500, Legendary 500–1000 coins), cached so it isn't regenerated on every load.
- **Two live third-party integrations**: GitHub (full create/read/update/delete) and OneNote (read-only), usable from a dashboard and from plain-English chat commands.
- **Large frontend components**: `App.tsx` (~47 KB) and `GoalDashboard.tsx` (~51 KB) are the two biggest.

## Tech Stack

- **Languages:** Python (backend), TypeScript (frontend).
- **Backend frameworks / libraries:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, python-jose + bcrypt (JWT auth), python-multipart.
- **Frontend frameworks / libraries:** React 18, Vite 6, Tailwind CSS, framer-motion, react-router v7, react-markdown with remark-gfm / remark-math / rehype-katex, react-syntax-highlighter, axios, lucide-react icons.
- **Data / ML:** Groq SDK (Llama 3.1 / 3.3, GPT-OSS-120B, Llama 4 Maverick), HuggingFace `transformers` + `torch` (`j-hartmann/emotion-english-distilroberta-base`).
- **Infra / services:** PostgreSQL (via psycopg2), Redis, GitHub REST API, Microsoft Graph (OneNote).

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- A running PostgreSQL instance
- A running Redis instance
- A Groq API key

### Installation

```bash
git clone https://github.com/DCode-v05/Lumina-Digital-Companion.git
cd Lumina-Digital-Companion
```

**Backend**

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# configure environment
cp .env.template .env
# then fill in GROQ_API_KEY, Postgres credentials, Redis host/port, SECRET_KEY
```

**Frontend**

```bash
cd ../frontend
npm install
```

### Running

Backend (from `backend/`):

```bash
uvicorn main:app --reload
# API on http://localhost:8000
```

Frontend (from `frontend/`):

```bash
npm run dev
# App on http://localhost:5173
```

The database tables are created on startup. Make sure PostgreSQL and Redis are reachable with the credentials in your `.env`.

Two things to know before you run it:

- `config.py` falls back to hard-coded Postgres credentials, a default JWT secret and `allow_origins=["*"]` when env vars are missing. Set everything in `.env`.
- `google-generativeai` is listed in `requirements.txt` but nothing in the backend imports it.

## Usage

1. Register an account and log in. Your first login adds 50 coins, and each new day you check in adds 20 more.
2. Set your favourites in the profile so the reward catalogue is built around your interests.
3. Start a chat. Ask a question, ask to learn something, or mention a goal with a deadline. The assistant picks a persona, remembers facts about you, and creates a goal if you gave it a timeframe.
4. Open the Goals dashboard to see subtasks, request a quiz on a learning goal, and check reminders.
5. Open the Rewards dashboard to spend coins on collectibles.
6. Open the Integrations tab to connect GitHub (a classic PAT with `repo` scope) or OneNote (a Microsoft Graph token with `Notes.Read`), then manage repos and browse notes from the dashboard or directly in chat ("how many repos do I have?", "list my OneNote pages").

## Project Structure

```
Lumina-Digital-Companion/
├── backend/
│   ├── main.py                 # FastAPI app, ~36 routes, chat orchestration
│   ├── groq_service.py         # 4-model router, prompts, goal/quiz/reward generation
│   ├── emotion_service.py      # DistilRoBERTa emotion classification + logging
│   ├── github_service.py       # GitHub REST API (list/create/get/update/delete)
│   ├── onenote_service.py      # Microsoft Graph OneNote (read-only)
│   ├── integration_service.py  # aggregator re-exporting the integration functions
│   ├── redis_client.py         # chat sessions, message history, profile/facts memory
│   ├── models.py               # SQLAlchemy tables (users, goals, emotions, etc.)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── auth.py                 # JWT + bcrypt auth
│   ├── database.py             # SQLAlchemy engine/session
│   ├── config.py               # model config, DB/Redis/auth settings
│   ├── .env.template           # environment variable template
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── index.css
│       ├── App.tsx                         # chat UI, routing, profile modal
│       ├── api.ts                          # axios API client (JWT attached)
│       ├── components/
│       │   ├── GoalDashboard.tsx           # goals, subtasks, quizzes
│       │   ├── RewardDashboard.tsx         # coins, catalogue, redeem
│       │   ├── IntegrationDashboard.tsx    # GitHub / OneNote connect
│       │   ├── ThemeProvider.tsx
│       │   └── ThemeToggle.tsx
│       └── pages/
│           ├── Login.tsx
│           └── Register.tsx
└── README.md
```

---

## Contact

<table>
  <tr><td><b>Portfolio:</b> <a href="https://www.denistan.me">Denistan</a></td><td><b>LinkedIn:</b> <a href="https://www.linkedin.com/in/denistanb">denistanb</a></td></tr>
  <tr><td><b>GitHub:</b> <a href="https://github.com/DCode-v05">DCode-v05</a></td><td><b>LeetCode:</b> <a href="https://leetcode.com/u/Denistan_B">Denistan_B</a></td></tr>
  <tr><td colspan="2" align="center"><b>Email:</b> <a href="mailto:denistanb05@gmail.com">denistanb05@gmail.com</a></td></tr>
</table>

Made with ❤️ by **Denistan B**
