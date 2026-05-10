# 🛡️ Anti-Scam Malaysia

AI-powered scam detection and education platform for Malaysians.
Platform pengesanan dan pendidikan penipuan berkuasa AI untuk rakyat Malaysia.

---

## Features / Ciri-ciri

| Feature | Description |
|---------|-------------|
| 🔍 **Analysis Bot** | Analyse suspicious messages, URLs, phone numbers, and images using AWS Bedrock (Claude) |
| 🎮 **Scam Simulator** | Practice identifying real Malaysian scam scenarios — Claude generates unique scenarios each session |
| 📋 **Report Generator** | Generate structured incident reports and export as PDF |
| 👥 **Community** | Share scam screenshots — Claude auto-extracts the suspicious message from images |
| 🔐 **Auth** | JWT-based signup/login with bcrypt password hashing |

---

## Project Structure

```
Anti_Scam_Malaysia/
├── frontend/                  # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── pages/             # Home, AnalysisBot, ScamSimulator, ReportSimulator, Community, AuthPage
│   │   ├── components/        # Navbar, ChatBubble, RiskGauge, ShareModal, ConfirmDialog
│   │   ├── context/           # AuthContext, LanguageContext
│   │   └── services/api.js    # All API calls (axios)
│   └── package.json
├── backend/                   # Python FastAPI
│   ├── routers/               # analysis.py, simulator.py, auth.py, community.py
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
| AI | AWS Bedrock — Claude Haiku 4.5 (chat/simulator), Claude Sonnet 4.5 (image analysis) |
| Database | Amazon RDS PostgreSQL 18 |
| Storage | Amazon S3 (community images) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Secrets | AWS Secrets Manager |

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

**Create `backend/.env`** with the following (get values from team lead):

```env
# ─── AWS Credentials ──────────────────────────────────────────
AWS_ACCESS_KEY_ID=<ask team lead>
AWS_SECRET_ACCESS_KEY=<ask team lead>
AWS_REGION=us-east-1

# ─── Bedrock ──────────────────────────────────────────────────
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0

# ─── RDS PostgreSQL ───────────────────────────────────────────
# Password is fetched automatically from Secrets Manager at startup
RDS_HOST=anti-scam-db.c6r4gac2i011.us-east-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DB=postgres
RDS_USER=postgres
RDS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:037427723047:secret:rds!db-ea21ed4f-c3d6-4285-b3df-b1e6023b8477-SZ2WJ8

# Used by Alembic migrations only (sync driver)
DATABASE_URL=postgresql+psycopg2://postgres:<password>@anti-scam-db.c6r4gac2i011.us-east-1.rds.amazonaws.com:5432/postgres

# ─── JWT ──────────────────────────────────────────────────────
JWT_SECRET_KEY=<ask team lead — must be same across all instances>
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── S3 ───────────────────────────────────────────────────────
S3_BUCKET_NAME=anti-scam-malaysia-bucket
```

**Download the RDS SSL certificate:**

```bash
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem" -OutFile "global-bundle.pem"

# Mac/Linux
curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
```

**Test the database connection:**

```bash
# Windows
venv\Scripts\python.exe test_db.py

# Mac/Linux
python test_db.py
```

Expected output:
```
[OK] Credentials retrieved from Secrets Manager
[OK] Connected successfully!
[OK] PostgreSQL: PostgreSQL 18.x ...
[OK] Existing tables: ['alembic_version', 'community_posts', 'incident_reports', 'users']
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

---

### Step 4 — Verify everything works

| Check | Expected result |
|-------|----------------|
| `GET http://localhost:8000/api/health` | `{"status":"ok","bedrock_configured":true}` |
| `http://localhost:5173` | Home page loads |
| Analysis Bot — send a message | AI response with risk score |
| Analysis Bot — upload an image | Vision analysis response |
| Signup / Login | JWT stored, username shown in navbar |
| Community — share a post with image | Post appears with extracted message |
| Scam Simulator — start simulation | Claude generates a unique scam scenario |

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
| `GET` | `/api/simulator/report/{session_id}/pdf` | — | Download simulation report PDF |
| `POST` | `/api/simulator/report/export-pdf` | — | Export incident report as PDF |
| `GET` | `/api/community/posts` | — | List community posts |
| `POST` | `/api/community/posts` | ✅ | Create community post (with optional image) |
| `DELETE` | `/api/community/posts/{post_id}` | ✅ | Delete own post |

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, username, password hash) |
| `community_posts` | Community scam reports with optional S3 image key and extracted message |
| `incident_reports` | Formal scam incident reports from the Report Generator |
| `alembic_version` | Alembic migration tracking |

---

## Malaysian Scam Scenarios Covered

| Scam Type | Bahasa Malaysia |
|-----------|----------------|
| Macau Scam | Penipuan Macau |
| Love Scam | Penipuan Cinta |
| Investment Scam (Crypto/Forex) | Penipuan Pelaburan |
| Parcel Delivery Scam | Penipuan Bungkusan |
| LHDN Tax Scam | Penipuan LHDN |
| Bank Impersonation (Maybank/CIMB) | Peniruan Bank |
| Online Shopping Scam | Penipuan Beli-belah |
| Job Scam | Penipuan Kerja |

---

## Emergency Contacts / Hubungi Kecemasan

| Agency | Number |
|--------|--------|
| 🚨 Emergency / Kecemasan | **997** |
| CCID Polis Malaysia | **03-2610 5000** |
| BNM TELELINK | **1-300-88-5465** |
| MCMC Aduan | **aduan.mcmc.gov.my** |
| Semak Mule | **www.semakmule.rmp.gov.my** |

---

## License

MIT — Built for educational purposes to protect Malaysians from scams.
