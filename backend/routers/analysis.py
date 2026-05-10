# -*- coding: utf-8 -*-
"""
Analysis Bot Router
Handles text and image analysis for scam detection using AWS Bedrock.
"""

import os
import uuid
import json
import base64
import boto3
from functools import lru_cache
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

from models.schemas import (
    AnalysisChatRequest,
    AnalysisChatResponse,
    AnalysisUploadResponse,
)

load_dotenv()

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# ─────────────────────────────────────────────
# Models
# Chat  → Haiku 4.5  (fast, cost-efficient, text)
# Upload → Sonnet 3.5 v2 (best vision on Bedrock)
# ─────────────────────────────────────────────
CHAT_MODEL_ID   = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
UPLOAD_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# ─────────────────────────────────────────────
# Bedrock client — singleton
# ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_bedrock_client():
    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"):
        if not os.getenv(var):
            raise RuntimeError(f"Missing required environment variable: {var}")
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

# ─────────────────────────────────────────────
# In-memory chat history store  { session_id: [messages] }
# Each message: {"role": "user"|"assistant", "content": ...}
# ─────────────────────────────────────────────
_history: dict[str, list] = {}
MAX_TURNS = 20  # keep last 20 messages (10 user + 10 assistant)

# ─────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Language-aware system prompt builders
# ─────────────────────────────────────────────

def _chat_system_prompt(language: str = "en") -> str:
    if language == "ms":
        lang_rule = (
            "- Balas SEPENUHNYA dalam Bahasa Malaysia (Melayu). "
            "Jangan gunakan bahasa Inggeris kecuali untuk nama jenama, nombor hotline, atau istilah teknikal yang tiada padanan Melayu."
        )
    else:
        lang_rule = (
            "- Reply ENTIRELY in English. "
            "Do not use Bahasa Malaysia except for Malaysian brand names or hotline numbers."
        )

    return f"""You are ScamShield, an expert anti-scam analyst specialising in Malaysia.
Your job is to analyse messages submitted by Malaysian users and determine whether they are scams.

Consider these Malaysia-specific scam types:
- Bank impersonation: Maybank (hotline 1-300-88-6688), CIMB (1-300-880-900), RHB, Public Bank
- Authority impersonation: PDRM (Royal Malaysia Police), LHDN (Inland Revenue Board), MCMC
- E-commerce scams: Shopee, Lazada parcel/delivery scams
- Macau scam (phone call impersonating authorities)
- Love scam (romantic interest requesting money)
- Investment scam (guaranteed returns, forex, crypto, MLM)
- Job scam (too-good-to-be-true offers, upfront fees)
- Phishing links (bit.ly, tinyurl, suspicious domains)

Rules:
{lang_rule}
- Be direct and clear about the risk level
- Always recommend official reporting channels when risk is HIGH or CRITICAL:
  CCID Polis: 03-2610 5000 | BNMTELELINK: 1-300-88-5465 | MCMC: 1-800-188-030

You MUST respond with ONLY a valid JSON object — no markdown, no code fences, no extra text.
The JSON must have exactly these fields:
{{
  "reply": "<analysis and advice as a readable string>",
  "risk_score": <integer 0-100>,
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "indicators": ["<indicator 1>", "<indicator 2>"],
  "confidence": <integer 0-100>
}}"""


def _upload_system_prompt(language: str = "en") -> str:
    if language == "ms":
        lang_rule = (
            "- Balas SEPENUHNYA dalam Bahasa Malaysia (Melayu). "
            "Jangan gunakan bahasa Inggeris kecuali untuk nama jenama, nombor hotline, atau istilah teknikal."
        )
    else:
        lang_rule = (
            "- Reply ENTIRELY in English. "
            "Do not use Bahasa Malaysia except for Malaysian brand names or hotline numbers."
        )

    return f"""You are ScamShield, an expert anti-scam analyst specialising in Malaysia.
Your job is to analyse images submitted by Malaysian users — these may be screenshots of messages,
fake bank notices, suspicious QR codes, phishing emails, or fraudulent documents.

Consider these Malaysia-specific scam types:
- Fake bank notices: Maybank, CIMB, RHB, Public Bank
- Fake authority letters: PDRM, LHDN, MCMC, court summons
- Fake e-commerce notifications: Shopee, Lazada
- Phishing pages or QR codes
- Fake job offers or investment schemes
- Counterfeit receipts or transfer confirmations

Rules:
{lang_rule}
- Describe what you see in the image and why it is or isn't suspicious
- Always recommend official reporting channels when risk is HIGH or CRITICAL:
  CCID Polis: 03-2610 5000 | BNMTELELINK: 1-300-88-5465

You MUST respond with ONLY a valid JSON object — no markdown, no code fences, no extra text.
The JSON must have exactly these fields:
{{
  "reply": "<analysis and advice as a readable string>",
  "risk_score": <integer 0-100>,
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "indicators": ["<indicator 1>", "<indicator 2>"],
  "confidence": <integer 0-100>
}}"""


# ─────────────────────────────────────────────
# Helper: invoke Bedrock and parse JSON response
# ─────────────────────────────────────────────

def _invoke(model_id: str, system_prompt: str, messages: list, max_tokens: int = 1024) -> dict:
    """Call Bedrock and return the parsed JSON dict from Claude's reply."""
    client = get_bedrock_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    })
    try:
        response = client.invoke_model(modelId=model_id, body=body)
    except client.exceptions.AccessDeniedException:
        raise HTTPException(status_code=502, detail="Bedrock access denied — check IAM permissions and model access.")
    except client.exceptions.ValidationException as e:
        raise HTTPException(status_code=502, detail=f"Bedrock validation error — check model ID or payload: {e}")
    except Exception:
        raise HTTPException(status_code=502, detail="Bedrock service error — please try again.")

    raw = json.loads(response["body"].read())
    text = raw["content"][0]["text"].strip()

    # Strip accidental markdown code fences if Claude adds them
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Model returned an unparseable response. Please try again.")


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/chat", response_model=AnalysisChatResponse)
async def analysis_chat(request: AnalysisChatRequest):
    """
    Analyse a text message for scam indicators using Claude Haiku 4.5.
    Maintains per-session conversation history.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id or str(uuid.uuid4())
    language = request.language or "en"

    # Retrieve or initialise history for this session
    history = _history.setdefault(session_id, [])

    # Build the new user turn
    new_user_turn = {"role": "user", "content": request.message}

    # Assemble messages: history + new turn
    messages = history + [new_user_turn]

    # Call Bedrock with the language-aware system prompt
    result = _invoke(
        model_id=CHAT_MODEL_ID,
        system_prompt=_chat_system_prompt(language),
        messages=messages,
    )

    # Append user turn and assistant reply to history
    history.append(new_user_turn)
    history.append({"role": "assistant", "content": result.get("reply", "")})

    # Enforce rolling window: keep last MAX_TURNS messages
    if len(history) > MAX_TURNS:
        _history[session_id] = history[-MAX_TURNS:]

    indicators = result.get("indicators") or ["No specific scam indicators detected"]

    return AnalysisChatResponse(
        reply=result.get("reply", ""),
        risk_score=int(result.get("risk_score", 0)),
        risk_level=result.get("risk_level", "LOW"),
        indicators=indicators,
        confidence=int(result.get("confidence", 0)),
        session_id=session_id,
    )


@router.delete("/chat/history/{session_id}", status_code=204)
async def clear_chat_history(session_id: str):
    """Clear conversation history for a given session."""
    if session_id not in _history:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    del _history[session_id]


@router.post("/upload", response_model=AnalysisUploadResponse)
async def analysis_upload(
    file: UploadFile = File(...),
    language: str = "en",
):
    """
    Analyse an uploaded image for scam indicators using Claude Sonnet 3.5 v2 (vision).
    Supports: screenshots of messages, fake bank notices, suspicious QR codes.
    """
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, GIF, WEBP."
        )

    image_data = await file.read()
    b64 = base64.b64encode(image_data).decode("utf-8")

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": file.content_type,
                    "data": b64,
                },
            },
            {
                "type": "text",
                "text": (
                    "Please analyse this image for scam indicators in the Malaysian context. "
                    "Describe what you see and assess whether it is a scam."
                ),
            },
        ],
    }]

    result = _invoke(
        model_id=UPLOAD_MODEL_ID,
        system_prompt=_upload_system_prompt(language),
        messages=messages,
        max_tokens=1536,
    )

    indicators = result.get("indicators") or ["No specific scam indicators detected"]

    return AnalysisUploadResponse(
        reply=result.get("reply", ""),
        risk_score=int(result.get("risk_score", 0)),
        risk_level=result.get("risk_level", "LOW"),
        indicators=indicators,
        confidence=int(result.get("confidence", 0)),
        filename=file.filename,
    )
