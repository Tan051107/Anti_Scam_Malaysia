# -*- coding: utf-8 -*-
"""
Pydantic schemas for Anti-Scam Malaysia API request/response models.
"""

from pydantic import BaseModel
from typing import Optional, List, Any


# ─────────────────────────────────────────────
# Analysis Bot Schemas
# ─────────────────────────────────────────────

class AnalysisChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class AnalysisChatResponse(BaseModel):
    reply: str
    risk_score: int          # 0–100
    risk_level: str          # LOW | MEDIUM | HIGH | CRITICAL
    indicators: List[str]
    confidence: int          # 0–100
    session_id: Optional[str] = None


class AnalysisUploadResponse(BaseModel):
    reply: str
    risk_score: int
    risk_level: str
    indicators: List[str]
    confidence: int
    filename: Optional[str] = None


# ─────────────────────────────────────────────
# Scam Simulator Schemas
# ─────────────────────────────────────────────

class SimulatorChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ScamReport(BaseModel):
    scam_type: str
    red_flags: List[str]
    summary: str
    outcome: str             # "FAILED" | "SUCCESS"
    advice: str


class SimulatorChatResponse(BaseModel):
    reply: str
    session_id: str
    scam_ended: bool
    user_caught_scam: bool
    report: Optional[ScamReport] = None


class SimulatorResetRequest(BaseModel):
    session_id: Optional[str] = None


class SimulatorResetResponse(BaseModel):
    session_id: str
    message: str


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    bedrock_configured: bool
