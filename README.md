# 🛡️ Anti-Scam Malaysia

AI-powered scam detection and education platform for Malaysians.


To deploy your own instance, configure the backend and frontend `.env` files
described below with your own AWS resources and API URL.

---

## Features / Ciri-ciri

| Feature | Description |
|---------|-------------|
| 🔍 **Analysis Bot** | Analyse suspicious messages, URLs, phone numbers, and images using AWS Bedrock (Claude Haiku 4.5). Guardrail-protected. |
| 🎮 **Scam Simulator** | Practice identifying real Malaysian scam scenarios — Claude generates unique scenarios each session. Guardrail-protected. |
| 📋 **Report Generator** | Generate structured bilingual incident reports and export as PDF (official Layout 2 design) |
| 👥 **Community** | Share scam screenshots with PII auto-censored. Claude extracts the suspicious message, strips prompt wrappers, and redacts names, phones, ICs, addresses, URLs from both text and images. Anonymous posting supported. |
| 🔐 **Auth** | JWT-based signup/login with bcrypt password hashing. Automatic token refresh via Axios interceptor. |

---

## Project Structure

```
Anti_Scam_Malaysia/
├── frontend/                  # React + Vite + Tailwind CSS
│   ├── public/
│   │   └── shield.svg         # Favicon
│   ├── src/
│   │   ├── pages/             # Home, AnalysisBot, ScamSimulator, ReportSimulator, Community, AuthPage
│   │   ├── components/        # Navbar, ChatBubble, RiskGauge, ShareModal, ConfirmDialog
│   │   ├── context/           # AuthContext (with token refresh), LanguageContext (EN/MS)
│   │   └── services/api.js    # Axios instance with 401 auto-refresh interceptor
│   ├── .env.example           # Frontend configuration template
│   └── package.json
├── backend/                   # Python FastAPI
│   ├── routers/
│   │   ├── analysis.py        # Scam analysis (text + image) with Bedrock guardrail
│   │   ├── simulator.py       # Scam simulator with Bedrock guardrail
│   │   ├── community.py       # Community posts with 4-layer PII censorship pipeline
│   │   ├── auth.py            # JWT auth endpoints
│   │   └── report.py          # PDF report generation (Layout 2 — official bilingual design)
│   ├── models/                # schemas.py (Pydantic), orm.py (SQLAlchemy)
│   ├── migrations/            # Alembic migration files
│   ├── database.py            # Async SQLAlchemy engine (fetches password from Secrets Manager)
│   ├── auth.py                # JWT + bcrypt utilities
│   ├── main.py
│   └── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Axios, React Router, Lucide React |
| Backend | FastAPI, SQLAlchemy (async), Alembic, Pydantic, Uvicorn |
| AI | AWS Bedrock — Claude Haiku 4.5 (chat/analysis/community), with Bedrock Guardrails |
| OCR | AWS Textract (FORMS + TABLES) — pixel-perfect PII redaction on images |
| Database | Amazon RDS PostgreSQL |
| Storage | Amazon S3 (community images — presigned URLs) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Secrets | AWS Secrets Manager |
| Frontend Hosting | AWS Amplify |
| Backend Hosting | AWS EC2 |

---

## Collaborator Setup Guide

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI (optional — credentials go in `.env`)
- Git

---

### Step 1 — Clone the repo

```bash
git clone <repo-url>
cd Anti_Scam_Malaysia
```

---

### Step 2 — Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Copy the configuration template, then replace every `your_...` value with
credentials and AWS resources you control:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

`JWT_SECRET_KEY` must be a long, unique random value and must remain the same
across all instances of one deployment. `CORS_ORIGINS` must list the URL(s) of
the frontend that may call your backend, separated by commas.

For the database, set `DATABASE_URL` to your PostgreSQL connection URL. This
same value is used by the application and Alembic migrations. If you prefer
AWS Secrets Manager, leave `DATABASE_URL` blank and provide the `RDS_*`
settings instead; the application will retrieve the password from
`RDS_SECRET_ARN`. Alembic still requires `DATABASE_URL` when running migrations.

**Run database migrations:**

```bash
alembic upgrade head
```

**Test the database connection:**

```bash
# Windows
venv\Scripts\python.exe test_db.py

# Mac/Linux
python test_db.py
```

**Start the backend:**

```bash
# Windows
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Mac/Linux
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

---

### Step 3 — Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:5173**

Copy the frontend template before starting the development server:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

Set `VITE_API_PROXY_TARGET` to the backend URL for local development. For a
production build, set `VITE_API_BASE_URL` to your deployed backend API URL.

---

### Step 4 — Frontend deployment

Set `VITE_API_BASE_URL` in your hosting provider's build environment to your
public backend API URL. If your host serves a single-page app, add a rewrite
from unknown routes to `/index.html` for React Router.

---

### Step 5 — Verify everything works

| Check | Expected result |
|-------|----------------|
| `GET http://localhost:8000/api/health` | `{"status":"ok","bedrock_configured":true}` |
| `http://localhost:5173` | Home page loads |
| Analysis Bot — send a message | AI response with risk score |
| Analysis Bot — upload an image | Vision analysis response |
| Signup / Login | JWT stored, auto-refreshes on expiry |
| Community — share a post with image | Post appears with PII-redacted image and extracted message |
| Community — anonymous post | Shows "anonymous" badge instead of username |
| Scam Simulator — start simulation | Claude generates a unique scam scenario |
| Report Generator — export PDF | Downloads official bilingual PDF report |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | — | Health check |
| `POST` | `/api/auth/signup` | — | Register new user |
| `POST` | `/api/auth/login` | — | Login, returns JWT |
| `POST` | `/api/auth/refresh` | — | Refresh access token |
| `GET` | `/api/auth/me` | ✅ | Get current user profile |
| `POST` | `/api/analysis/chat` | — | Analyse text message (with history) |
| `POST` | `/api/analysis/upload` | — | Analyse uploaded image |
| `DELETE` | `/api/analysis/chat/history/{session_id}` | — | Clear chat history |
| `POST` | `/api/simulator/chat` | — | Scam simulator chat turn |
| `POST` | `/api/simulator/reset` | — | Reset simulator session |
| `POST` | `/api/simulator/report/export-pdf` | — | Export incident report as PDF |
| `GET` | `/api/community/posts` | — | List community posts (paginated) |
| `GET` | `/api/community/posts/mine` | ✅ | List own posts |
| `POST` | `/api/community/posts` | ✅ | Create community post (with optional image) |
| `POST` | `/api/community/posts/{post_id}/upvote` | ✅ | Upvote / un-upvote a post |
| `DELETE` | `/api/community/posts/{post_id}` | ✅ | Delete own post |

---

## Community PII Censorship Pipeline

When a user uploads an image to the community, it goes through a 4-layer pipeline:

1. **AWS Textract** (`analyze_document` FORMS+TABLES) — extracts pixel-perfect word bounding boxes and key-value pairs
2. **Regex pre-filter** — deterministically catches IC numbers, phone numbers (including split tokens like `+1 (307) 209-2175`), emails, bank accounts, passport numbers, and URLs
3. **AWS Bedrock (Claude)** — classifies ambiguous words (names, addresses) using structured KV context
4. **Pillow** — draws precise black redaction boxes over flagged words only

Text content is also censored via Bedrock with fallback regex covering: names, IC numbers, phone numbers, emails, bank accounts, addresses, passport numbers, and URLs.

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, username, password hash) |
| `community_posts` | Community scam reports with optional S3 image key, extracted message, and `is_anonymous` flag |
| `post_upvotes` | Upvote records (unique per user per post) |
| `incident_reports` | Formal scam incident reports from the Report Generator |
| `alembic_version` | Alembic migration tracking |
