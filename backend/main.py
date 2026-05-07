# -*- coding: utf-8 -*-
"""
Anti-Scam Malaysia — FastAPI Backend
Main application entry point.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import analysis, simulator
from models.schemas import HealthResponse

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = FastAPI(
    title="Anti-Scam Malaysia API",
    description="Backend API for Anti-Scam Malaysia — scam analysis and simulation platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.
    Returns API status and whether AWS Bedrock credentials are configured.
    """
    bedrock_configured = bool(
        os.getenv("AWS_ACCESS_KEY_ID") and
        os.getenv("AWS_SECRET_ACCESS_KEY") and
        os.getenv("BEDROCK_MODEL_ID")
    )

    return HealthResponse(
        status="ok",
        version="1.0.0",
        bedrock_configured=bedrock_configured,
    )


# ─────────────────────────────────────────────
# AWS Bedrock Client (initialized when credentials are present)
# ─────────────────────────────────────────────

# ============================================================
# TODO: WIRE BEDROCK HERE
# Uncomment and configure the Bedrock client when AWS credentials are ready.
#
# import boto3
# import json
#
# bedrock_runtime = None
#
# def get_bedrock_client():
#     global bedrock_runtime
#     if bedrock_runtime is None:
#         bedrock_runtime = boto3.client(
#             service_name="bedrock-runtime",
#             region_name=os.getenv("AWS_REGION", "ap-southeast-1"),
#             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#         )
#     return bedrock_runtime
#
# Then pass get_bedrock_client() into your router functions via dependency injection:
# from fastapi import Depends
# def analysis_chat(request: AnalysisChatRequest, bedrock=Depends(get_bedrock_client)):
#     ...
# ============================================================


# ─────────────────────────────────────────────
# Run (development)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
