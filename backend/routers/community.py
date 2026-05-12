# -*- coding: utf-8 -*-
"""
Community Router
Handles community posts with optional image uploads to S3.
When an image is shared, Bedrock extracts the suspicious message text from it.
Supports upvoting — posts sorted by upvote count descending.
"""

import os
import uuid
import json
import base64
import io
import re
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

router = APIRouter(prefix="/api/community", tags=["community"])

S3_BUCKET        = os.getenv("S3_BUCKET_NAME")
AWS_REGION       = os.getenv("AWS_REGION", "us-east-1")
EXTRACT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
# VISION_MODEL_ID removed — image censorship now uses AWS Textract for pixel-accurate OCR
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


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
    _get_s3_client().put_object(
        Bucket=S3_BUCKET, Key=key, Body=file_bytes, ContentType=content_type
    )
    return key


def _get_presigned_url(key: str, expires: int = 3600) -> str:
    return _get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


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
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": content_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract the suspicious or scam-related message text visible in this image. "
                            "Return ONLY the extracted message text as plain text, nothing else. "
                            "If the image contains a chat message, SMS, email, or notice, copy the text exactly. "
                            "If no suspicious text is found, return an empty string."
                        ),
                    },
                ],
            }],
        })
        response = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
        result = json.loads(response["body"].read())
        extracted = result["content"][0]["text"].strip()
        return extracted if extracted else ""
    except Exception:
        return ""


# ─────────────────────────────────────────────
# PII censorship helpers
# ─────────────────────────────────────────────

def _censor_text(text: str) -> str:
    """
    Use Claude to replace PII in extracted text with placeholders.
    Falls back to regex-based censorship if Bedrock fails.
    """
    if not text:
        return text
    try:
        client = get_bedrock_client()
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": (
                    "You are a privacy protection tool. Replace ALL personally identifiable information (PII) "
                    "in the following text with these exact placeholders:\n"
                    "- Full names → [NAME]\n"
                    "- Malaysian IC numbers (e.g. 901231-14-5678) → [IC NUMBER]\n"
                    "- Phone numbers (Malaysian or international) → [PHONE NUMBER]\n"
                    "- Email addresses → [EMAIL]\n"
                    "- Bank account numbers → [BANK ACCOUNT]\n"
                    "- Home/office addresses → [ADDRESS]\n"
                    "- Passport numbers → [PASSPORT]\n\n"
                    "Keep all other text exactly as-is. Return ONLY the censored text, nothing else.\n\n"
                    f"Text to censor:\n{text}"
                ),
            }],
        })
        response = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
        result = json.loads(response["body"].read())
        censored = result["content"][0]["text"].strip()
        return censored if censored else text
    except Exception:
        # Fallback: regex-based censorship
        # Malaysian IC: YYMMDD-PB-XXXX
        text = re.sub(r'\b\d{6}-\d{2}-\d{4}\b', '[IC NUMBER]', text)
        # Phone numbers
        text = re.sub(r'(\+?60|0)[1-9]\d{7,9}', '[PHONE NUMBER]', text)
        # Email
        text = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
        return text


def _extract_pii_values(original_text: str, censored_text: str) -> list[str]:
    """
    Compare original and censored text to extract the actual PII values that were replaced.
    Returns a list of original PII strings found.
    """
    pii_values = []
    # Use regex to find what was replaced by placeholders
    placeholders = [
        r'\[NAME\]', r'\[IC NUMBER\]', r'\[PHONE NUMBER\]',
        r'\[EMAIL\]', r'\[BANK ACCOUNT\]', r'\[ADDRESS\]', r'\[PASSPORT\]'
    ]
    # Split both texts into tokens and find differences
    orig_words = original_text.split()
    cens_words = censored_text.split()

    # Simple diff: find spans in original that map to placeholders in censored
    i, j = 0, 0
    while i < len(orig_words) and j < len(cens_words):
        is_placeholder = any(
            re.match(p.replace('\\[', r'\[').replace('\\]', r'\]'), cens_words[j])
            for p in placeholders
        )
        if is_placeholder:
            # Collect original words until we find alignment again
            pii_span = []
            while i < len(orig_words) and (j + 1 >= len(cens_words) or orig_words[i] != cens_words[j + 1]):
                pii_span.append(orig_words[i])
                i += 1
            if pii_span:
                pii_values.append(' '.join(pii_span))
            j += 1
        else:
            i += 1
            j += 1

    return pii_values


def _censor_image(image_bytes: bytes, content_type: str, pii_values: list[str] = None) -> bytes:
    """
    Accurate PII censorship using a two-step pipeline:
    1. AWS Textract — detects every word with pixel-perfect bounding boxes
    2. Bedrock (Haiku) — classifies which words/phrases are PII
    3. Pillow — draws tight black redaction boxes over only the PII words

    Falls back to returning the original image if any step fails.
    """
    try:
        # ── Step 1: Textract — get all words with exact bounding boxes ──
        textract = boto3.client(
            "textract",
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        response = textract.detect_document_text(Document={"Bytes": image_bytes})

        words = []
        for block in response["Blocks"]:
            if block["BlockType"] == "WORD":
                bb = block["Geometry"]["BoundingBox"]
                words.append({
                    "text": block["Text"],
                    "left":   bb["Left"],
                    "top":    bb["Top"],
                    "width":  bb["Width"],
                    "height": bb["Height"],
                })

        if not words:
            return image_bytes

        # ── Step 2: Bedrock — identify which words are PII ──
        full_text = " ".join(w["text"] for w in words)

        # If we already know the PII values from text censorship, use them directly
        pii_set: set[str] = set()
        if pii_values:
            # Normalize for matching
            for v in pii_values:
                for token in v.split():
                    pii_set.add(token.lower().strip(".,!?;:\"'"))
        else:
            # Ask Bedrock to identify PII tokens from the full text
            client = get_bedrock_client()
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "messages": [{
                    "role": "user",
                    "content": (
                        "From the following text, extract ONLY the words/tokens that are personally "
                        "identifiable information (PII): names, IC numbers, phone numbers, emails, "
                        "bank account numbers, addresses, passport numbers.\n\n"
                        "Return ONLY a JSON array of the exact PII strings as they appear in the text. "
                        "Example: [\"Ahmad\", \"bin\", \"Ali\", \"901231-14-5678\", \"0123456789\"]\n\n"
                        f"Text: {full_text}"
                    ),
                }],
            })
            r = client.invoke_model(modelId=EXTRACT_MODEL_ID, body=body)
            raw_text = json.loads(r["body"].read())["content"][0]["text"].strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()
            pii_tokens = json.loads(raw_text)
            for token in pii_tokens:
                pii_set.add(token.lower().strip(".,!?;:\"'"))

        if not pii_set:
            return image_bytes

        # ── Step 3: Pillow — draw precise redaction boxes ──
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img)
        iw, ih = img.size
        pad = 3  # pixels of padding around each word

        for word in words:
            token = word["text"].lower().strip(".,!?;:\"'")
            if token in pii_set:
                x1 = max(0, int(word["left"] * iw) - pad)
                y1 = max(0, int(word["top"] * ih) - pad)
                x2 = min(iw, int((word["left"] + word["width"]) * iw) + pad)
                y2 = min(ih, int((word["top"] + word["height"]) * ih) + pad)
                draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))

        out = io.BytesIO()
        fmt = "JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"
        img.save(out, format=fmt, quality=90)
        return out.getvalue()

    except Exception:
        return image_bytes

        out = io.BytesIO()
        fmt = "JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"
        img.save(out, format=fmt, quality=90)
        return out.getvalue()

    except Exception:
        return image_bytes


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
    has_upvoted: bool   # whether the current user has upvoted this post
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
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a community post with optional image upload.
    If an image is provided and no original_message is set,
    Bedrock will extract the suspicious message text from the image automatically.
    """
    if not caption and not original_message and not image:
        raise HTTPException(status_code=400, detail="Post must have content or an image.")

    image_key = None
    image_bytes = None
    image_content_type = None

    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type '{image.content_type}'. Allowed: JPEG, PNG, WEBP, GIF."
            )
        image_bytes = await image.read()
        image_content_type = image.content_type
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        image_key = f"community/{current_user.id}/{uuid.uuid4()}.{ext}"

        # Step 1: Extract text from original image
        extracted_raw = ""
        if not original_message:
            extracted_raw = _extract_message_from_image(image_bytes, image_content_type)

        # Step 2: Censor PII in extracted text
        if extracted_raw:
            censored_text = _censor_text(extracted_raw)
            original_message = censored_text
            # Step 3: Find what PII values were replaced (to guide image censorship)
            pii_values = _extract_pii_values(extracted_raw, censored_text)
        else:
            pii_values = []

        # Step 4: Censor image — pass known PII values for targeted redaction
        censored_bytes = _censor_image(image_bytes, image_content_type, pii_values or None)

        # Step 5: Upload only the censored image to S3
        _upload_to_s3(censored_bytes, image.content_type, image_key)

    post = CommunityPost(
        user_id=current_user.id,
        caption=caption,
        scam_type=scam_type,
        original_message=original_message,
        note=note,
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=indicators,
        image_key=image_key,
    )
    db.add(post)
    await db.flush()

    image_url = _get_presigned_url(image_key) if image_key else None
    indicators_list = json.loads(indicators) if indicators else []

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        author_name=current_user.full_name or current_user.username,
        caption=post.caption,
        scam_type=post.scam_type,
        original_message=post.original_message,
        note=post.note,
        risk_score=post.risk_score,
        risk_level=post.risk_level,
        indicators=indicators_list,
        image_url=image_url,
        upvote_count=0,
        has_upvoted=False,
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List community posts sorted by upvote count (highest first). Public endpoint."""

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    # Upvote count subquery
    upvote_count_sq = (
        select(PostUpvote.post_id, func.count(PostUpvote.id).label("upvote_count"))
        .group_by(PostUpvote.post_id)
        .subquery()
    )

    # Posts with author info and upvote count, sorted by upvotes desc then newest
    result = await db.execute(
        select(
            CommunityPost,
            User.username,
            User.full_name,
            func.coalesce(upvote_count_sq.c.upvote_count, 0).label("upvote_count"),
        )
        .join(User, CommunityPost.user_id == User.id)
        .outerjoin(upvote_count_sq, CommunityPost.id == upvote_count_sq.c.post_id)
        .where(CommunityPost.is_published == True)
        .order_by(
            desc(func.coalesce(upvote_count_sq.c.upvote_count, 0)),
            desc(CommunityPost.created_at),
        )
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    # Get current user's upvoted post IDs for has_upvoted flag
    upvoted_ids: set[str] = set()
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
            id=post.id,
            user_id=post.user_id,
            author_name=full_name or username,
            caption=post.caption,
            scam_type=post.scam_type,
            original_message=post.original_message,
            note=post.note,
            risk_score=post.risk_score,
            risk_level=post.risk_level,
            indicators=indicators_list,
            image_url=image_url,
            upvote_count=upvote_count,
            has_upvoted=post.id in upvoted_ids,
            created_at=post.created_at.isoformat(),
        ))

    return PostListResponse(posts=posts, total=total)


@router.get("/posts/mine", response_model=PostListResponse)
async def list_my_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List posts created by the current user, sorted by newest first."""
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost)
        .where(CommunityPost.user_id == current_user.id, CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    upvote_count_sq = (
        select(PostUpvote.post_id, func.count(PostUpvote.id).label("upvote_count"))
        .group_by(PostUpvote.post_id)
        .subquery()
    )

    result = await db.execute(
        select(
            CommunityPost,
            func.coalesce(upvote_count_sq.c.upvote_count, 0).label("upvote_count"),
        )
        .outerjoin(upvote_count_sq, CommunityPost.id == upvote_count_sq.c.post_id)
        .where(CommunityPost.user_id == current_user.id, CommunityPost.is_published == True)
        .order_by(desc(CommunityPost.created_at))
        .limit(limit)
        .offset(offset)
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
            id=post.id,
            user_id=post.user_id,
            author_name=current_user.full_name or current_user.username,
            caption=post.caption,
            scam_type=post.scam_type,
            original_message=post.original_message,
            note=post.note,
            risk_score=post.risk_score,
            risk_level=post.risk_level,
            indicators=indicators_list,
            image_url=image_url,
            upvote_count=upvote_count,
            has_upvoted=False,  # own posts — upvote button is hidden anyway
            created_at=post.created_at.isoformat(),
        ))

    return PostListResponse(posts=posts, total=total)


@router.post("/posts/{post_id}/upvote", status_code=200)
async def upvote_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle upvote on a post. Cannot upvote own post. Returns new upvote count."""
    post = (await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot upvote your own post.")

    existing = (await db.execute(
        select(PostUpvote).where(PostUpvote.post_id == post_id, PostUpvote.user_id == current_user.id)
    )).scalar_one_or_none()

    if existing:
        # Already upvoted — remove it (toggle off)
        await db.delete(existing)
        has_upvoted = False
    else:
        db.add(PostUpvote(post_id=post_id, user_id=current_user.id))
        has_upvoted = True

    await db.flush()

    count_result = await db.execute(
        select(func.count(PostUpvote.id)).where(PostUpvote.post_id == post_id)
    )
    upvote_count = count_result.scalar()

    return {"upvote_count": upvote_count, "has_upvoted": has_upvoted}


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a post. Only the author can delete their own post."""
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
