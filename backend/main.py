# -*- coding: utf-8 -*-
"""
Anti-Scam Malaysia — FastAPI Backend
Main application entry point.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base
from routers import analysis, simulator
from routers.auth import router as auth_router
from routers.community import router as community_router
from models.schemas import HealthResponse
import models.orm  # noqa: F401 — ensure ORM models are registered on Base.metadata

load_dotenv()


# ─────────────────────────────────────────────
# Lifespan — create DB tables on startup
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = FastAPI(
    title="Anti-Scam Malaysia API",
    description="Backend API for Anti-Scam Malaysia — scam analysis and simulation platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# CORS Middleware
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────

app.include_router(analysis.router)
app.include_router(simulator.router)
app.include_router(auth_router)
app.include_router(community_router)

# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    bedrock_configured = bool(
        os.getenv("AWS_ACCESS_KEY_ID") and
        os.getenv("AWS_SECRET_ACCESS_KEY") and
        os.getenv("AWS_REGION")
    )
    return HealthResponse(
        status="ok",
        version="1.0.0",
        bedrock_configured=bedrock_configured,
    )


# ─────────────────────────────────────────────
# Run (development)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
