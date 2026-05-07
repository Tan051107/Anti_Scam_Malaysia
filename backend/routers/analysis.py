# -*- coding: utf-8 -*-
"""
Analysis Bot Router
Handles text and image analysis for scam detection.
"""

import uuid
import random
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from models.schemas import (
    AnalysisChatRequest,
    AnalysisChatResponse,
    AnalysisUploadResponse,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# ─────────────────────────────────────────────
# Malaysia-specific scam keyword dictionaries
# ─────────────────────────────────────────────

HIGH_RISK_KEYWORDS = [
    # English
    "transfer", "otp", "one time password", "bank account", "urgent",
    "winner", "prize", "congratulations", "claim", "verify your account",
    "suspended", "blocked", "arrest", "warrant", "police", "court",
    "investment", "profit", "guaranteed return", "bitcoin", "crypto",
    "forex", "love", "darling", "sweetheart", "send money",
    "western union", "gift card", "itunes", "google play",
    # Malay
    "pindah", "wang", "akaun", "menang", "hadiah", "tahniah",
    "tuntut", "segera", "tangkap", "waran", "mahkamah", "polis",
    "pelaburan", "keuntungan", "dijamin", "hantar duit", "nombor ic",
    "kata laluan", "pin", "cvv",
]

MEDIUM_RISK_KEYWORDS = [
    # English
    "click link", "verify", "confirm", "update", "expire", "limited time",
    "act now", "free", "bonus", "reward", "parcel", "delivery", "package",
    "customs", "duty", "fee", "refund", "rebate",
    # Malay
    "klik pautan", "sahkan", "kemaskini", "tamat tempoh", "percuma",
    "bonus", "ganjaran", "bungkusan", "penghantaran", "kastam",
    "bayaran", "bayar balik",
]

LOW_RISK_KEYWORDS = [
    "hello", "hi", "help", "question", "ask", "info",
    "helo", "hai", "tolong", "soalan", "tanya", "maklumat",
]

SCAM_TYPES = {
    "maybank": "Bank Impersonation (Maybank)",
    "cimb": "Bank Impersonation (CIMB)",
    "rhb": "Bank Impersonation (RHB)",
    "public bank": "Bank Impersonation (Public Bank)",
    "pdrm": "Authority Impersonation (PDRM)",
    "lhdn": "Authority Impersonation (LHDN)",
    "polis": "Authority Impersonation (PDRM)",
    "shopee": "E-Commerce Scam (Shopee)",
    "lazada": "E-Commerce Scam (Lazada)",
    "macau": "Macau Scam",
    "love": "Love Scam",
    "bitcoin": "Investment Scam (Crypto)",
    "forex": "Investment Scam (Forex)",
    "pelaburan": "Investment Scam",
    "investment": "Investment Scam",
    "parcel": "Parcel Delivery Scam",
    "bungkusan": "Parcel Delivery Scam",
    "job": "Job Scam",
    "kerja": "Job Scam",
}

INDICATOR_TEMPLATES = {
    "otp": "Requesting OTP/one-time password — legitimate banks never ask for this",
    "transfer": "Requesting money transfer to unknown account",
    "pdrm": "Impersonating PDRM (Royal Malaysia Police)",
    "lhdn": "Impersonating LHDN (Inland Revenue Board)",
    "maybank": "Impersonating Maybank — verify via official hotline 1-300-88-6688",
    "cimb": "Impersonating CIMB — verify via official hotline 1-300-880-900",
    "prize": "Unsolicited prize/lottery claim — classic advance-fee fraud",
    "winner": "Claiming you are a winner without prior participation",
    "urgent": "Creating false urgency to pressure immediate action",
    "investment": "Promising guaranteed high returns — hallmark of investment scam",
    "bitcoin": "Cryptocurrency investment with guaranteed profits — likely scam",
    "love": "Romantic interest requesting financial assistance",
    "parcel": "Parcel held at customs requiring payment — common delivery scam",
    "warrant": "Threatening arrest warrant to coerce compliance",
    "ic": "Requesting IC (identity card) number — identity theft risk",
    "cvv": "Requesting CVV/card security code — never share this",
}


def analyze_text(text: str):
    """
    Analyze input text for scam indicators.
    Returns risk_score, risk_level, indicators, confidence, detected_type.
    """
    text_lower = text.lower()
    score = 0
    indicators = []
    detected_type = "Unknown Scam Pattern"

    # Check high-risk keywords
    high_hits = [kw for kw in HIGH_RISK_KEYWORDS if kw in text_lower]
    score += len(high_hits) * 20

    # Check medium-risk keywords
    medium_hits = [kw for kw in MEDIUM_RISK_KEYWORDS if kw in text_lower]
    score += len(medium_hits) * 10

    # Build indicators list
    for key, indicator_text in INDICATOR_TEMPLATES.items():
        if key in text_lower:
            indicators.append(indicator_text)

    # Detect scam type
    for keyword, scam_type in SCAM_TYPES.items():
        if keyword in text_lower:
            detected_type = scam_type
            break

    # URL detection
    if "http" in text_lower or "bit.ly" in text_lower or "tinyurl" in text_lower:
        score += 25
        indicators.append("Suspicious shortened/unverified URL detected")

    # Phone number pattern (Malaysian)
    import re
    if re.search(r"(\+?60|0)[1-9]\d{7,9}", text):
        score += 5
        indicators.append("Malaysian phone number detected — verify caller identity independently")

    # Cap score at 100
    score = min(score, 100)

    # Add base noise for realism
    if score == 0 and len(text) > 10:
        score = random.randint(5, 15)

    # Determine risk level
    if score <= 30:
        risk_level = "LOW"
    elif score <= 60:
        risk_level = "MEDIUM"
    elif score <= 80:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Confidence based on number of indicators found
    confidence = min(60 + len(indicators) * 8 + len(high_hits) * 5, 98)
    if score < 15:
        confidence = random.randint(40, 65)

    return score, risk_level, indicators, confidence, detected_type


def build_reply(risk_level: str, indicators: list, detected_type: str, message: str) -> str:
    """Build a contextual bot reply based on analysis results."""

    if risk_level == "CRITICAL":
        return (
            f"🚨 **AMARAN KRITIKAL / CRITICAL WARNING** 🚨\n\n"
            f"Analisis saya menunjukkan ini adalah **{detected_type}** dengan risiko yang sangat tinggi!\n\n"
            f"My analysis indicates this is a **{detected_type}** with extremely high risk!\n\n"
            f"Saya mengesan {len(indicators)} petanda penipuan. Jangan ikut arahan mereka. "
            f"I detected {len(indicators)} scam indicator(s). Do NOT comply with their instructions.\n\n"
            f"**Tindakan segera / Immediate action:**\n"
            f"• Hentikan semua komunikasi / Stop all communication\n"
            f"• Laporkan ke CCID Polis: 03-2610 5000\n"
            f"• Hubungi bank anda segera jika ada transaksi / Contact your bank immediately if any transaction occurred\n"
            f"• Laporkan ke BNMTELELINK: 1-300-88-5465"
        )
    elif risk_level == "HIGH":
        return (
            f"⚠️ **RISIKO TINGGI / HIGH RISK DETECTED**\n\n"
            f"Mesej ini menunjukkan ciri-ciri **{detected_type}**.\n"
            f"This message shows characteristics of **{detected_type}**.\n\n"
            f"Saya mengesan {len(indicators)} petanda yang membimbangkan. "
            f"I found {len(indicators)} concerning indicator(s).\n\n"
            f"**Nasihat / Advice:** Jangan berkongsi maklumat peribadi atau membuat sebarang pembayaran. "
            f"Do not share personal information or make any payments. Verify through official channels first."
        )
    elif risk_level == "MEDIUM":
        return (
            f"🔶 **RISIKO SEDERHANA / MEDIUM RISK**\n\n"
            f"Terdapat beberapa petanda yang mencurigakan dalam mesej ini. "
            f"There are some suspicious indicators in this message.\n\n"
            f"Kemungkinan berkaitan dengan: **{detected_type}**.\n"
            f"Possibly related to: **{detected_type}**.\n\n"
            f"**Syor / Recommendation:** Sahkan identiti penghantar melalui saluran rasmi sebelum mengambil sebarang tindakan. "
            f"Verify the sender's identity through official channels before taking any action."
        )
    else:
        return (
            f"✅ **RISIKO RENDAH / LOW RISK**\n\n"
            f"Mesej ini tidak menunjukkan petanda penipuan yang ketara pada masa ini. "
            f"This message does not show significant scam indicators at this time.\n\n"
            f"Walau bagaimanapun, sentiasa berhati-hati. Jika anda rasa ada sesuatu yang tidak kena, percayai naluri anda. "
            f"However, always stay vigilant. If something feels off, trust your instincts.\n\n"
            f"💡 Tip: Jangan sekali-kali berkongsi OTP, nombor IC, atau maklumat bank dengan sesiapa. "
            f"Never share OTP, IC number, or banking details with anyone."
        )


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/chat", response_model=AnalysisChatResponse)
async def analysis_chat(request: AnalysisChatRequest):
    """
    Analyze a text message for scam indicators.
    Accepts: free text, URLs, phone numbers, email content, suspicious messages.
    """

    # ============================================================
    # TODO: WIRE BEDROCK HERE
    # Replace this mock response with actual AWS Bedrock API call
    # Model: Use BEDROCK_MODEL_ID from .env
    # boto3 client: bedrock_runtime.invoke_model(...)
    #
    # Suggested prompt structure:
    # system_prompt = """You are an expert anti-scam analyst for Malaysia.
    # Analyze the following message for scam indicators specific to Malaysia.
    # Consider: Maybank/CIMB/RHB impersonation, PDRM/LHDN authority scams,
    # Shopee/Lazada parcel scams, Macau scam, love scam, investment scams.
    # Respond in both English and Malay. Return JSON with:
    # reply, risk_score (0-100), risk_level (LOW/MEDIUM/HIGH/CRITICAL),
    # indicators (list), confidence (0-100)"""
    #
    # body = json.dumps({
    #     "anthropic_version": "bedrock-2023-05-31",
    #     "max_tokens": 1024,
    #     "system": system_prompt,
    #     "messages": [{"role": "user", "content": request.message}]
    # })
    # response = bedrock_runtime.invoke_model(
    #     modelId=os.getenv("BEDROCK_MODEL_ID"),
    #     body=body
    # )
    # result = json.loads(response["body"].read())
    # ============================================================

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    score, risk_level, indicators, confidence, detected_type = analyze_text(request.message)
    reply = build_reply(risk_level, indicators, detected_type, request.message)

    session_id = request.session_id or str(uuid.uuid4())

    return AnalysisChatResponse(
        reply=reply,
        risk_score=score,
        risk_level=risk_level,
        indicators=indicators if indicators else ["No specific scam indicators detected"],
        confidence=confidence,
        session_id=session_id,
    )


@router.post("/upload", response_model=AnalysisUploadResponse)
async def analysis_upload(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """
    Analyze an uploaded image for scam indicators.
    Supports: screenshots of messages, fake bank notices, suspicious QR codes.
    """

    # ============================================================
    # TODO: WIRE BEDROCK HERE
    # Replace this mock response with actual AWS Bedrock API call
    # Model: Use BEDROCK_MODEL_ID from .env (Claude 3 supports vision)
    #
    # Steps:
    # 1. Read image bytes: image_data = await file.read()
    # 2. Encode to base64: import base64; b64 = base64.b64encode(image_data).decode()
    # 3. Detect media type from file.content_type
    # 4. Call Bedrock with vision payload:
    #
    # body = json.dumps({
    #     "anthropic_version": "bedrock-2023-05-31",
    #     "max_tokens": 1024,
    #     "messages": [{
    #         "role": "user",
    #         "content": [
    #             {
    #                 "type": "image",
    #                 "source": {
    #                     "type": "base64",
    #                     "media_type": file.content_type,
    #                     "data": b64,
    #                 }
    #             },
    #             {
    #                 "type": "text",
    #                 "text": "Analyze this image for scam indicators in Malaysian context..."
    #             }
    #         ]
    #     }]
    # })
    # response = bedrock_runtime.invoke_model(modelId=os.getenv("BEDROCK_MODEL_ID"), body=body)
    # ============================================================

    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files are supported (JPEG, PNG, GIF, WEBP)")

    # Mock image analysis — simulate finding scam content in image
    mock_score = random.randint(45, 95)
    mock_indicators = [
        "Image contains text requesting urgent action",
        "Suspicious bank logo detected — may be counterfeit",
        "QR code or link detected in image — do not scan without verification",
        "Official-looking letterhead that may be forged",
    ]
    selected_indicators = random.sample(mock_indicators, k=random.randint(1, 3))

    if mock_score <= 60:
        risk_level = "MEDIUM"
    elif mock_score <= 80:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    reply = (
        f"🖼️ **Analisis Imej / Image Analysis**\n\n"
        f"Saya telah menganalisis imej yang anda hantar. "
        f"I have analyzed the uploaded image.\n\n"
        f"**Penemuan / Findings:** Imej ini menunjukkan ciri-ciri yang mencurigakan. "
        f"This image shows suspicious characteristics.\n\n"
        f"Skor risiko: **{mock_score}/100** — Tahap: **{risk_level}**\n\n"
        f"⚠️ Jangan ikut arahan dalam imej ini tanpa mengesahkan melalui saluran rasmi. "
        f"Do not follow instructions in this image without verifying through official channels."
    )

    return AnalysisUploadResponse(
        reply=reply,
        risk_score=mock_score,
        risk_level=risk_level,
        indicators=selected_indicators,
        confidence=random.randint(70, 90),
        filename=file.filename,
    )
