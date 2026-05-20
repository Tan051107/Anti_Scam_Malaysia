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
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from dotenv import load_dotenv

from models.schemas import (
    AnalysisChatRequest,
    AnalysisChatResponse,
    AnalysisUploadResponse,
)
from bedrock_models import ANALYSIS_MODEL_ENV, get_model_id

load_dotenv()

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

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

    RISK SCORE RUBRIC (use this to assign risk_score and risk_level consistently):
    - 0-24   → LOW      (no suspicious signals; routine message)
    - 25-49  → MEDIUM   (some suspicious elements; proceed with caution)
    - 50-79  → HIGH     (strong scam indicators; likely a scam)
    - 80-100 → CRITICAL (confirmed scam pattern; do not engage)

    Rules:
    {lang_rule}
    - Be direct and clear about the risk level
    - Always recommend official reporting channels when risk is HIGH or CRITICAL:
      CCID Polis: 03-2610 5000 | BNMTELELINK: 1-300-88-5465 | MCMC: 1-800-188-030
    - List ONLY indicators actually present in the submitted message; do not list generic indicators
    - If no indicators are present, return an empty array []. Never fabricate indicators.
    - risk_level MUST match risk_score exactly: 0-24=LOW, 25-49=MEDIUM, 50-79=HIGH, 80-100=CRITICAL. Never contradict these bands.
    - confidence reflects how certain you are of the risk assessment given the available evidence:
      80-100: clear, unambiguous signals present
      50-79: some signals present but message is vague or partial
      20-49: very little to go on; assessment is tentative
      0-19: insufficient information to assess

    INDICATOR FORMAT RULES — strictly enforced:
    - Each indicator must be a short, factual noun phrase describing a scam signal (e.g. "Threat of account closure", "Unsolicited request for OTP", "Suspicious shortened URL").
    - Each indicator must be 2–8 words. No full sentences, no punctuation at the end.
    - NEVER include meta-commentary such as "I've reviewed...", "I understand you've provided...", "This text contains...", or any reference to your own analysis process.
    - NEVER repeat or quote the user's raw input inside an indicator string.
    - NEVER explain what an indicator is — just name it.

    You MUST respond with ONLY a valid JSON object — no markdown, no code fences, no extra text.
    The JSON must have exactly these fields:
    {{
      "reply": "<analysis and advice as a readable string>",
      "risk_score": <integer 0-100>,
      "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "indicators": ["<indicator 1>", "<indicator 2>"],
      "confidence": <integer 0-100>
    }}

    Before writing the JSON, silently reason: (1) what type of message is this, (2) which specific indicators from the message support your assessment, (3) assign risk_score, then derive risk_level from the rubric above. Never assign risk_level first and fit the score to it."""


def _upload_system_prompt(language: str = "en") -> str:
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

    RISK SCORE RUBRIC (use this to assign risk_score and risk_level consistently):
    - 0-24   → LOW      (no suspicious signals; routine message)
    - 25-49  → MEDIUM   (some suspicious elements; proceed with caution)
    - 50-79  → HIGH     (strong scam indicators; likely a scam)
    - 80-100 → CRITICAL (confirmed scam pattern; do not engage)

    Rules:
    {lang_rule}
    - Be direct and clear about the risk level
    - Always recommend official reporting channels when risk is HIGH or CRITICAL:
      CCID Polis: 03-2610 5000 | BNMTELELINK: 1-300-88-5465 | MCMC: 1-800-188-030
    - List ONLY indicators actually present in the submitted message; do not list generic indicators
    - If no indicators are present, return an empty array []. Never fabricate indicators.
    - risk_level MUST match risk_score exactly: 0-24=LOW, 25-49=MEDIUM, 50-79=HIGH, 80-100=CRITICAL. Never contradict these bands.
    - confidence reflects how certain you are of the risk assessment given the available evidence:
      80-100: clear, unambiguous signals present
      50-79: some signals present but message is vague or partial
      20-49: very little to go on; assessment is tentative
      0-19: insufficient information to assess

    INDICATOR FORMAT RULES — strictly enforced:
    - Each indicator must be a short, factual noun phrase describing a scam signal (e.g. "Threat of account closure", "Unsolicited request for OTP", "Suspicious shortened URL").
    - Each indicator must be 2–8 words. No full sentences, no punctuation at the end.
    - NEVER include meta-commentary such as "I've reviewed...", "I understand you've provided...", "This text contains...", or any reference to your own analysis process.
    - NEVER repeat or quote the user's raw input inside an indicator string.
    - NEVER explain what an indicator is — just name it.

    You MUST respond with ONLY a valid JSON object — no markdown, no code fences, no extra text.
    The JSON must have exactly these fields:
    {{
      "reply": "<analysis and advice as a readable string>",
      "risk_score": <integer 0-100>,
      "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "indicators": ["<indicator 1>", "<indicator 2>"],
      "confidence": <integer 0-100>
    }}

    Before writing the JSON, silently reason: (1) what type of message is this, (2) which specific indicators from the message support your assessment, (3) assign risk_score, then derive risk_level from the rubric above. Never assign risk_level first and fit the score to it."""


# ─────────────────────────────────────────────
# Helper: invoke Bedrock and parse JSON response
# ─────────────────────────────────────────────

def _invoke(model_id: str, system_prompt: str, messages: list, max_tokens: int = 1024) -> dict:
    """Call Bedrock and return the parsed JSON dict from Claude's reply."""
    client = get_bedrock_client()

    body_dict = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature" : 0,
        "system": system_prompt,
        "messages": messages,
    }

    # Attach guardrail if configured — passed as API kwargs, not in body
    guardrail_id = os.getenv("ANALYSIS_GUARDRAIL_ID", "").strip()
    guardrail_version = os.getenv("ANALYSIS_GUARDRAIL_VERSION", "DRAFT").strip()

    body = json.dumps(body_dict)

    # Build invoke_model kwargs — guardrail params are API-level, not in the body
    invoke_kwargs = {"modelId": model_id, "body": body}
    if guardrail_id:
        invoke_kwargs["guardrailIdentifier"] = guardrail_id
        invoke_kwargs["guardrailVersion"] = guardrail_version

    try:
        response = client.invoke_model(**invoke_kwargs)
    except client.exceptions.AccessDeniedException:
        raise HTTPException(status_code=502, detail="Bedrock access denied — check IAM permissions and model access.")
    except client.exceptions.ValidationException as e:
        raise HTTPException(status_code=502, detail=f"Bedrock validation error — check model ID or payload: {e}")
    except Exception:
        raise HTTPException(status_code=502, detail="Bedrock service error — please try again.")

    raw = json.loads(response["body"].read())

    # Check if guardrail blocked the request — must check BEFORE accessing content
    stop_reason = raw.get("stop_reason", "")
    if stop_reason == "guardrail_intervened":
        # Extract the guardrail's output message if available, otherwise use a default
        guardrail_text = "I can't process that request, but I can help you check if a message might be a scam."
        for block in raw.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                guardrail_text = block.get("text", guardrail_text).strip()
                break
        return {
            "reply": guardrail_text,
            "risk_score": 0,
            "risk_level": "LOW",
            "indicators": [],
            "confidence": 0,
        }

    # Extract text from content array defensively
    content = raw.get("content", [])
    text = None
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "").strip()
            break

    if not text:
        # Log raw response to help diagnose guardrail or model issues
        import logging
        logging.getLogger(__name__).error("Unparseable Bedrock response: %s", json.dumps(raw)[:500])
        raise HTTPException(status_code=502, detail="Model returned an unparseable response. Please try again.")

    # Strip accidental markdown code fences if Claude adds them
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import logging
        logging.getLogger(__name__).error("JSON decode failed for Bedrock response text: %s", text[:300])
        # Guardrail blocked the message — Claude returned plain text refusal instead of JSON.
        # Return it as a structured low-risk response so the frontend can display it gracefully.
        return {
            "reply": text,
            "risk_score": 0,
            "risk_level": "LOW",
            "indicators": [],
            "confidence": 0,
            "blocked": True,
        }


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/chat", response_model=AnalysisChatResponse)
async def analysis_chat(request: AnalysisChatRequest):
    """
    Analyse a text message for scam indicators using Claude Sonnet 4.6.
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
        model_id=get_model_id(ANALYSIS_MODEL_ENV),
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
    language: str = Query("en", description="Response language: en or ms"),
    session_id: str = Query(None, description="Session ID to persist image analysis in chat history"),
    message: str = Query(None, description="Optional text message to include with the image analysis"),
):
    """
    Analyse an uploaded image for scam indicators using Claude Sonnet 4.6 (vision).
    Supports: screenshots of messages, fake bank notices, suspicious QR codes.
    If session_id is provided, the image analysis is stored in chat history so
    follow-up text questions have context.
    If message is provided, it's included alongside the image for combined analysis.
    """
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, GIF, WEBP."
        )

    image_data = await file.read()
    b64 = base64.b64encode(image_data).decode("utf-8")

    # Build the text prompt — include user's message if provided
    text_prompt = message.strip() if message and message.strip() else (
        "Please analyse this image for scam indicators in the Malaysian context. "
        "Describe what you see and assess whether it is a scam."
    )

    user_turn = {
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
                "text": text_prompt,
            },
        ],
    }

    # Include existing history so the model has full context
    sid = session_id or str(uuid.uuid4())
    history = _history.setdefault(sid, [])
    messages = history + [user_turn]

    result = _invoke(
        model_id=get_model_id(ANALYSIS_MODEL_ENV),
        system_prompt=_upload_system_prompt(language),
        messages=messages,
        max_tokens=1536,
    )

    # Store the image turn and reply in history so follow-up text questions have context.
    # Store a text-only summary of the user turn (base64 is too large to keep in history).
    history.append({
        "role": "user",
        "content": f"[User uploaded an image: {file.filename}] Please analyse this image for scam indicators.",
    })
    history.append({"role": "assistant", "content": result.get("reply", "")})
    if len(history) > MAX_TURNS:
        _history[sid] = history[-MAX_TURNS:]

    indicators = result.get("indicators") or ["No specific scam indicators detected"]

    return AnalysisUploadResponse(
        reply=result.get("reply", ""),
        risk_score=int(result.get("risk_score", 0)),
        risk_level=result.get("risk_level", "LOW"),
        indicators=indicators,
        confidence=int(result.get("confidence", 0)),
        filename=file.filename,
        session_id=sid,
    )
