# -*- coding: utf-8 -*-
"""
Community Router
Handles community posts with optional image uploads to S3.
PII censorship pipeline:
  1. Textract analyze_document (FORMS + TABLES) - pixel-perfect word boxes + KV pairs
  2. Regex pre-filter - catches IC, phone, email, passport deterministically
  3. Bedrock (structured context) - classifies remaining ambiguous words using KV context
  4. Pillow - draws tight black boxes over flagged words only
"""

import os
import uuid
import json
import base64
import io
import re
import logging
import difflib
import boto3
from PIL import Image, ImageDraw
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.orm import CommunityPost, PostUpvote, User
from auth import get_current_user, get_current_user_optional
from routers.analysis import get_bedrock_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/community", tags=["community"])

S3_BUCKET        = os.getenv("S3_BUCKET_NAME")
AWS_REGION       = os.getenv("AWS_REGION", "us-east-1")
EXTRACT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB — Textract hard limit

PII_FIELD_KEYS = {
    "ic", "ic no", "ic number", "mykad", "nric", "phone", "tel",
    "telefon", "mobile", "hp", "email", "e-mail", "name", "nama",
    "address", "alamat", "passport", "akaun", "account", "bank",
    "no ic", "no. ic", "nombor ic", "no telefon", "no. telefon",
}

PII_PATTERNS = [
    re.compile(r'^\d{6}-\d{2}-\d{4}$'),
    re.compile(r'^(\+?60|0)[1-9]\d{7,9}$'),
    re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'),
    re.compile(r'^\d{10,16}$'),
    re.compile(r'^[A-Z]\d{7,9}$'),
    re.compile(r'^\+?\d[\d\s\-]{8,14}\d$'),
    re.compile(r'^\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}$'),
    # URLs: full http(s):// links, www. links, or bare domains with paths
    re.compile(r'^https?://\S*$', re.IGNORECASE),
    re.compile(r'^www\.\S+\.\S*$', re.IGNORECASE),
    re.compile(r'^[a-zA-Z0-9\-]+\.(com|net|org|io|my|co|info|biz|xyz|top|club|site|online|shop|link|click|live|app|web|tech|store|vip|pro|cc|tv|me|us|uk|sg|id|ph|th|vn)(/\S*)?$'),
]


# ─────────────────────────────────────────────
# S3 helpers
# ─────────────────────────────────────────────

def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def _upload_to_s3(file_bytes: bytes, content_type: str, key: str) -> str:
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    _get_s3_client().put_object(Bucket=S3_BUCKET, Key=key, Body=file_bytes, ContentType=content_type)
    return key


def _get_presigned_url(key: str, expires: int = 3600) -> str:
    return _get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def _build_s3_url(key: str) -> str:
    """Construct a direct S3 URL without an API call."""
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"


# ─────────────────────────────────────────────
# Bedrock: extract suspicious message from image
# ─────────────────────────────────────────────

def _extract_message_from_image(image_bytes: bytes, content_type: str) -> str:
    try:
        client = get_bedrock_client()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": b64}},
                {"type": "text", "text": (
                    "Extract the suspicious or scam-related message text visible in this image. "
                    "Return ONLY the extracted message text as plain text, nothing else. "
                    "If the image contains a chat message, SMS, email, or notice, copy the text exactly. "
                    "If no suspicious text is found, return an empty string."
                )},
            ]}],
        })
        response = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
        extracted = json.loads(response["body"].read())["content"][0]["text"].strip()
        return extracted if extracted else ""
    except Exception as exc:
        logger.warning("_extract_message_from_image failed: %s", exc, exc_info=True)
        return ""


def _extract_scam_content(text: str) -> str:
    """
    Strip prompt wrappers from user-submitted text and return only the
    suspicious/scam message content. Uses Bedrock with a structured prompt.
    Falls back to the original text if Bedrock fails.
    """
    if not text:
        return text
    try:
        client = get_bedrock_client()
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "system": (
                "You are a text extraction tool. Your only job is to extract the scam or suspicious "
                "message content from user-submitted text. Users sometimes wrap the actual scam message "
                "with their own commentary or questions — either before the message (e.g. 'Is this a scam?', "
                "'Check this:', 'My friend sent me this message:') or after it (e.g. '...check if it's scam', "
                "'...is this legit?', '...scam ke?'). Remove the user's commentary whether it appears at "
                "the start or end, and return only the scam/suspicious message itself. "
                "If there is no wrapper and the text is already just the message, return it unchanged. "
                "Return ONLY the extracted message text, nothing else."
            ),
            "messages": [{"role": "user", "content": (
                f"<user_submitted_text>\n{text}\n</user_submitted_text>\n\n"
                "Extract and return only the scam/suspicious message content from the text above."
            )}],
        })
        response = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
        extracted = json.loads(response["body"].read())["content"][0]["text"].strip()
        return extracted if extracted else text
    except Exception as exc:
        logger.warning("_extract_scam_content failed: %s", exc, exc_info=True)
        return text


# ─────────────────────────────────────────────
# PII censorship helpers
# ─────────────────────────────────────────────

def _censor_text(text: str) -> str:
    if not text:
        return text
    try:
        client = get_bedrock_client()
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": (
                "You are a privacy protection tool. Replace ALL personally identifiable information (PII) "
                "in the following text with these exact placeholders:\n"
                "- Full names -> [NAME]\n"
                "- Malaysian IC numbers (e.g. 901231-14-5678) -> [IC NUMBER]\n"
                "- Phone numbers (Malaysian or international) -> [PHONE NUMBER]\n"
                "- Email addresses -> [EMAIL]\n"
                "- Bank account numbers -> [BANK ACCOUNT]\n"
                "- Home/office addresses -> [ADDRESS]\n"
                "- Passport numbers -> [PASSPORT]\n"
                "- URLs and web links (http, https, www, or any domain link) -> [URL]\n\n"
                "Keep all other text exactly as-is. Return ONLY the censored text, nothing else.\n\n"
                f"Text to censor:\n{text}"
            )}],
        })
        response = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
        censored = json.loads(response["body"].read())["content"][0]["text"].strip()
        return censored if censored else text
    except Exception:
        text = re.sub(r'\b\d{6}-\d{2}-\d{4}\b', '[IC NUMBER]', text)
        text = re.sub(r'(\+?60|0)[1-9]\d{7,9}', '[PHONE NUMBER]', text)
        text = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
        text = re.sub(r'\b\d{10,16}\b', '[BANK ACCOUNT]', text)
        text = re.sub(r'\b[A-Za-z]\d{7,9}\b', '[PASSPORT]', text)
        text = re.sub(r'https?://[^\s]+|www\.[^\s]+', '[URL]', text)
        return text


def _extract_pii_values(original_text: str, censored_text: str) -> list:
    if not original_text or not censored_text:
        return []
    placeholder_re = re.compile(
        r'^\[(?:NAME|IC NUMBER|PHONE NUMBER|EMAIL|BANK ACCOUNT|ADDRESS|PASSPORT|URL)\]$'
    )
    orig_words = original_text.split()
    cens_words = censored_text.split()
    pii_values = []

    matcher = difflib.SequenceMatcher(None, orig_words, cens_words, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            # The censored slice may be one or more placeholder tokens
            cens_slice = cens_words[j1:j2]
            if all(placeholder_re.match(t) for t in cens_slice):
                span = " ".join(orig_words[i1:i2])
                if span:
                    pii_values.append(span)
    return pii_values


def _censor_image(image_bytes: bytes, content_type: str, pii_values: list = None) -> bytes:
    """
    Four-layer PII censorship pipeline:
    1. Textract analyze_document (FORMS+TABLES) - pixel-perfect word boxes + KV pairs
    2. Regex pre-filter - catches IC, phone, email, passport deterministically
    3. Bedrock with structured context - KV pairs + line context sent instead of raw word blob
    4. Pillow - draws tight black boxes over flagged words only
    """
    try:
        # ── Layer 1: Textract analyze_document ──────────────────────────────
        textract = boto3.client(
            "textract", region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        response = textract.analyze_document(
            Document={"Bytes": image_bytes},
            FeatureTypes=["FORMS", "TABLES"],
        )

        blocks_by_id = {b["Id"]: b for b in response["Blocks"]}

        words = []
        for block in response["Blocks"]:
            if block["BlockType"] == "WORD":
                bb = block["Geometry"]["BoundingBox"]
                words.append({
                    "id": block["Id"],
                    "text": block["Text"],
                    "left": bb["Left"],
                    "top": bb["Top"],
                    "width": bb["Width"],
                    "height": bb["Height"],
                })

        if not words:
            return image_bytes

        # Build LINE blocks for context (group words into lines by top position)
        lines = {}
        for block in response["Blocks"]:
            if block["BlockType"] == "LINE":
                line_words = []
                for rel in block.get("Relationships", []):
                    if rel["Type"] == "CHILD":
                        for wid in rel["Ids"]:
                            if wid in blocks_by_id and blocks_by_id[wid]["BlockType"] == "WORD":
                                line_words.append(blocks_by_id[wid]["Text"])
                if line_words:
                    line_text = " ".join(line_words)
                    for wid in [r_id for rel in block.get("Relationships", [])
                                for r_id in rel["Ids"] if rel["Type"] == "CHILD"]:
                        lines[wid] = line_text

        # Extract KV pairs — build structured context list
        kv_value_ids: set = set()
        kv_pairs = []  # [{"key": "IC No", "value": "901231-14-5678", "value_ids": [...]}]

        for block in response["Blocks"]:
            if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", []):
                key_text = ""
                for rel in block.get("Relationships", []):
                    if rel["Type"] == "CHILD":
                        key_text = " ".join(
                            blocks_by_id[wid]["Text"]
                            for wid in rel["Ids"]
                            if wid in blocks_by_id and blocks_by_id[wid]["BlockType"] == "WORD"
                        )

                value_text = ""
                value_word_ids = []
                for rel in block.get("Relationships", []):
                    if rel["Type"] == "VALUE":
                        for val_id in rel["Ids"]:
                            val_block = blocks_by_id.get(val_id)
                            if val_block:
                                for child_rel in val_block.get("Relationships", []):
                                    if child_rel["Type"] == "CHILD":
                                        for wid in child_rel["Ids"]:
                                            if wid in blocks_by_id:
                                                value_text += blocks_by_id[wid]["Text"] + " "
                                                value_word_ids.append(wid)

                if key_text and value_text.strip():
                    kv_pairs.append({
                        "key": key_text.strip(),
                        "value": value_text.strip(),
                        "value_ids": value_word_ids,
                    })
                    # Auto-flag values of known PII keys
                    if any(pk in key_text.lower() for pk in PII_FIELD_KEYS):
                        kv_value_ids.update(value_word_ids)

        # ── Layer 2: Regex pre-filter ────────────────────────────────────────
        pii_set: set = set()
        regex_flagged_ids: set = set()
        remaining_words = []

        # Word-level patterns (single-token PII)
        for word in words:
            token = word["text"].strip(".,!?;:\"'()[]")
            if any(p.match(token) for p in PII_PATTERNS):
                regex_flagged_ids.add(word["id"])
                pii_set.add(token.lower())
            else:
                remaining_words.append(word)

        # Line-level phone scan — catches numbers split across tokens by Textract
        # e.g. "+1 (307) 209-2175" → tokens "+1", "(307)", "209-2175" each fail
        # word-level patterns but the full line text matches a phone pattern.
        LINE_PHONE_PATTERNS = [
            # International: +1 (307) 209-2175, +44 7911 123456, etc.
            re.compile(r'(\+\d{1,3}[\s\-.]?\(?\d{1,4}\)?[\s\-.]?\d{3,5}[\s\-.]?\d{3,5})'),
            # Malaysian: 012-345 6789, 03-1234 5678, +60 12-345 6789
            re.compile(r'(\+?6?0[\s\-]?\d{1,2}[\s\-]?\d{3,4}[\s\-]?\d{4})'),
            # Generic: any sequence of digits/spaces/dashes/parens that looks like a phone
            re.compile(r'(\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4})'),
        ]
        # Build reverse map: word_id → line block (need word_ids per line)
        line_word_ids: dict = {}  # line_text → [word_ids]
        for block in response["Blocks"]:
            if block["BlockType"] == "LINE":
                wids = []
                for rel in block.get("Relationships", []):
                    if rel["Type"] == "CHILD":
                        for wid in rel["Ids"]:
                            if wid in blocks_by_id and blocks_by_id[wid]["BlockType"] == "WORD":
                                wids.append(wid)
                if wids:
                    line_text = " ".join(blocks_by_id[wid]["Text"] for wid in wids)
                    # Strip common punctuation for matching
                    clean_line = line_text.replace("(", "").replace(")", "")
                    if any(p.search(clean_line) for p in LINE_PHONE_PATTERNS):
                        for wid in wids:
                            regex_flagged_ids.add(wid)
                            # Remove from remaining_words if it was added there
                        remaining_words = [w for w in remaining_words if w["id"] not in regex_flagged_ids]

        # Add tokens from text censorship diff
        if pii_values:
            for v in pii_values:
                for token in v.split():
                    pii_set.add(token.lower().strip(".,!?;:\"'()[]"))

        # ── Layer 3: Bedrock with structured context ─────────────────────────
        # Build structured prompt: KV pairs + line context for ambiguous words
        already_flagged = kv_value_ids | regex_flagged_ids
        ambiguous_words = [w for w in remaining_words if w["id"] not in already_flagged]

        if ambiguous_words:
            # Build structured context: KV pairs first, then line context
            structured_lines = []

            # Section 1: KV pairs from Textract FORMS
            if kv_pairs:
                structured_lines.append("=== Detected Form Fields ===")
                for kv in kv_pairs:
                    structured_lines.append(f"  {kv['key']}: {kv['value']}")

            # Section 2: Line context for each ambiguous word
            structured_lines.append("=== Lines Containing Unclassified Words ===")
            seen_lines = set()
            for word in ambiguous_words:
                line_ctx = lines.get(word["id"], word["text"])
                if line_ctx not in seen_lines:
                    structured_lines.append(f"  Line: \"{line_ctx}\"")
                    seen_lines.add(line_ctx)

            structured_context = "\n".join(structured_lines)

            try:
                client = get_bedrock_client()
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": (
                        "You are a PII detection tool. Using the structured document context below, "
                        "identify which of these specific words are personally identifiable information. "
                        "Flag ALL of the following regardless of where they appear in the document:\n"
                        "- Personal names (first names, last names, full names, partial names)\n"
                        "- Physical addresses (street names, house numbers, city names, postcodes)\n"
                        "- Any other PII not already handled (phone/IC/email are already redacted)\n\n"
                        f"Words to classify: {json.dumps([w['text'] for w in ambiguous_words])}\n\n"
                        f"Document context:\n{structured_context}\n\n"
                        "Return ONLY a JSON array of the exact PII tokens from the words list above.\n"
                        "Example: [\"Ahmad\", \"bin\", \"Ali\", \"Jalan\", \"Ampang\"]\n"
                        "If none are PII, return: []"
                    )}],
                })
                r = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
                raw = json.loads(r["body"].read())["content"][0]["text"].strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()
                for token in json.loads(raw):
                    pii_set.add(token.lower().strip(".,!?;:\"'()[]"))
            except Exception as exc:
                logger.warning(
                    "_censor_image Layer 3 Bedrock call failed — continuing with Layers 1+2 only: %s",
                    exc, exc_info=True,
                )

        # ── Layer 4: Pillow — draw precise redaction boxes ───────────────────
        pad = 3

        def _redact_frame(frame: "Image.Image") -> "Image.Image":
            """Apply redaction boxes to a single Pillow frame."""
            frame = frame.convert("RGBA")
            draw = ImageDraw.Draw(frame)
            iw, ih = frame.size
            for word in words:
                token = word["text"].lower().strip(".,!?;:\"'()[]")
                if token in pii_set or word["id"] in kv_value_ids or word["id"] in regex_flagged_ids:
                    x1 = max(0,  int(word["left"] * iw) - pad)
                    y1 = max(0,  int(word["top"]  * ih) - pad)
                    x2 = min(iw, int((word["left"] + word["width"])  * iw) + pad)
                    y2 = min(ih, int((word["top"]  + word["height"]) * ih) + pad)
                    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 255))
            return frame

        if content_type == "image/gif":
            src = Image.open(io.BytesIO(image_bytes))
            gif_frames = []
            durations = []
            try:
                while True:
                    redacted = _redact_frame(src.copy())
                    gif_frames.append(redacted.convert("P", palette=Image.ADAPTIVE))
                    durations.append(src.info.get("duration", 100))
                    src.seek(src.tell() + 1)
            except EOFError:
                pass
            out = io.BytesIO()
            gif_frames[0].save(
                out, format="GIF", save_all=True, append_images=gif_frames[1:],
                loop=src.info.get("loop", 0), duration=durations, disposal=2,
            )
            return out.getvalue()
        else:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = _redact_frame(img).convert("RGB")
            out = io.BytesIO()
            fmt = "JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"
            img.save(out, format=fmt, quality=90)
            return out.getvalue()

    except Exception as exc:
        logger.error(
            "_censor_image pipeline failed — refusing to return uncensored bytes: %s",
            exc, exc_info=True,
        )
        raise


# ─────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────

class PostResponse(BaseModel):
    id: str
    user_id: str
    author_name: str
    caption: str | None
    scam_type: str | None
    original_message: str | None
    note: str | None
    risk_score: int | None
    risk_level: str | None
    indicators: list[str]
    image_url: str | None
    upvote_count: int
    has_upvoted: bool
    is_anonymous: bool
    created_at: str
    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    posts: list[PostResponse]
    total: int


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    caption: Optional[str] = Form(None),
    scam_type: Optional[str] = Form(None),
    original_message: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    risk_score: Optional[int] = Form(None),
    risk_level: Optional[str] = Form(None),
    indicators: Optional[str] = Form(None),
    is_anonymous: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not caption and not original_message and not image:
        raise HTTPException(status_code=400, detail="Post must have content or an image.")

    image_key = None

    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400,
                detail=f"Unsupported image type '{image.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.")
        image_bytes = await image.read()
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Image exceeds the {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB size limit.",
            )
        image_content_type = image.content_type
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        image_key = f"community/{current_user.id}/{uuid.uuid4()}.{ext}"

        extracted_raw = ""
        if not original_message:
            extracted_raw = _extract_message_from_image(image_bytes, image_content_type)

        if extracted_raw:
            censored_text = _censor_text(extracted_raw)
            original_message = censored_text
            pii_values = _extract_pii_values(extracted_raw, censored_text)
        elif original_message:
            # Strip any prompt wrapper the user typed before the scam content
            clean_content = _extract_scam_content(original_message)
            censored_text = _censor_text(clean_content)
            pii_values = _extract_pii_values(clean_content, censored_text)
            original_message = censored_text
        else:
            pii_values = []

        try:
            censored_bytes = _censor_image(image_bytes, image_content_type, pii_values or None)
        except Exception:
            raise HTTPException(status_code=500, detail="Image censorship failed. Upload rejected to protect privacy.")
        _upload_to_s3(censored_bytes, image.content_type, image_key)

    # For text-only posts (no image), still scrub the original_message
    elif original_message:
        clean_content = _extract_scam_content(original_message)
        original_message = _censor_text(clean_content)

    # Scrub PII from indicators before storing
    indicators_list: list[str] = []
    if indicators:
        try:
            raw_indicators = json.loads(indicators)
            indicators_list = [_censor_text(ind) for ind in raw_indicators if isinstance(ind, str)]
        except (json.JSONDecodeError, TypeError):
            indicators_list = []
    indicators_json = json.dumps(indicators_list) if indicators_list else indicators

    post = CommunityPost(
        user_id=current_user.id,
        caption=caption,
        scam_type=scam_type,
        original_message=original_message,
        note=note,
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=indicators_json,
        image_key=image_key,
        is_anonymous=is_anonymous,
    )
    db.add(post)
    await db.flush()

    image_url = _get_presigned_url(image_key) if image_key else None

    return PostResponse(
        id=post.id, user_id=post.user_id,
        author_name="Anonymous" if is_anonymous else (current_user.full_name or current_user.username),
        caption=post.caption, scam_type=post.scam_type,
        original_message=post.original_message, note=post.note,
        risk_score=post.risk_score, risk_level=post.risk_level,
        indicators=indicators_list, image_url=image_url,
        upvote_count=0, has_upvoted=False,
        is_anonymous=post.is_anonymous,
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    limit: int = 20, offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    upvote_sq = (
        select(PostUpvote.post_id, func.count(PostUpvote.id).label("upvote_count"))
        .group_by(PostUpvote.post_id).subquery()
    )
    result = await db.execute(
        select(CommunityPost, User.username, User.full_name,
               func.coalesce(upvote_sq.c.upvote_count, 0).label("upvote_count"))
        .join(User, CommunityPost.user_id == User.id)
        .outerjoin(upvote_sq, CommunityPost.id == upvote_sq.c.post_id)
        .where(CommunityPost.is_published == True)
        .order_by(desc(func.coalesce(upvote_sq.c.upvote_count, 0)), desc(CommunityPost.created_at))
        .limit(limit).offset(offset)
    )
    rows = result.all()

    upvoted_ids: set = set()
    if current_user:
        upvoted_result = await db.execute(
            select(PostUpvote.post_id).where(PostUpvote.user_id == current_user.id)
        )
        upvoted_ids = {row[0] for row in upvoted_result.fetchall()}

    posts = []
    for post, username, full_name, upvote_count in rows:
        image_url = _get_presigned_url(post.image_key) if post.image_key else None
        try:
            indicators_list = json.loads(post.indicators) if post.indicators else []
        except (json.JSONDecodeError, TypeError):
            indicators_list = []
        posts.append(PostResponse(
            id=post.id, user_id=post.user_id,
            author_name="Anonymous" if post.is_anonymous else (full_name or username),
            caption=post.caption, scam_type=post.scam_type,
            original_message=post.original_message, note=post.note,
            risk_score=post.risk_score, risk_level=post.risk_level,
            indicators=indicators_list, image_url=image_url,
            upvote_count=upvote_count, has_upvoted=post.id in upvoted_ids,
            is_anonymous=post.is_anonymous,
            created_at=post.created_at.isoformat(),
        ))
    return PostListResponse(posts=posts, total=total)


@router.get("/posts/mine", response_model=PostListResponse)
async def list_my_posts(
    limit: int = 20, offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost)
        .where(CommunityPost.user_id == current_user.id, CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    upvote_sq = (
        select(PostUpvote.post_id, func.count(PostUpvote.id).label("upvote_count"))
        .group_by(PostUpvote.post_id).subquery()
    )
    result = await db.execute(
        select(CommunityPost, func.coalesce(upvote_sq.c.upvote_count, 0).label("upvote_count"))
        .outerjoin(upvote_sq, CommunityPost.id == upvote_sq.c.post_id)
        .where(CommunityPost.user_id == current_user.id, CommunityPost.is_published == True)
        .order_by(desc(CommunityPost.created_at))
        .limit(limit).offset(offset)
    )
    rows = result.all()

    posts = []
    for post, upvote_count in rows:
        image_url = _get_presigned_url(post.image_key) if post.image_key else None
        try:
            indicators_list = json.loads(post.indicators) if post.indicators else []
        except (json.JSONDecodeError, TypeError):
            indicators_list = []
        posts.append(PostResponse(
            id=post.id, user_id=post.user_id,
            author_name=current_user.full_name or current_user.username,
            caption=post.caption, scam_type=post.scam_type,
            original_message=post.original_message, note=post.note,
            risk_score=post.risk_score, risk_level=post.risk_level,
            indicators=indicators_list, image_url=image_url,
            upvote_count=upvote_count, has_upvoted=False,
            is_anonymous=post.is_anonymous,
            created_at=post.created_at.isoformat(),
        ))
    return PostListResponse(posts=posts, total=total)


@router.post("/posts/{post_id}/upvote", status_code=200)
async def upvote_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot upvote your own post.")

    existing = (await db.execute(
        select(PostUpvote).where(PostUpvote.post_id == post_id, PostUpvote.user_id == current_user.id)
    )).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        has_upvoted = False
    else:
        db.add(PostUpvote(post_id=post_id, user_id=current_user.id))
        has_upvoted = True

    await db.flush()
    count_result = await db.execute(
        select(func.count(PostUpvote.id)).where(PostUpvote.post_id == post_id)
    )
    return {"upvote_count": count_result.scalar(), "has_upvoted": has_upvoted}


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts.")

    if post.image_key and S3_BUCKET:
        try:
            _get_s3_client().delete_object(Bucket=S3_BUCKET, Key=post.image_key)
        except Exception:
            pass
    await db.delete(post)
