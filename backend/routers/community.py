# -*- coding: utf-8 -*-
"""
Community Router
Handles community posts with optional image uploads to S3.
When an image is shared, Bedrock extracts the suspicious message text from it.
"""

import os
import uuid
import json
import base64
import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.orm import CommunityPost, User
from auth import get_current_user, get_current_user_optional
from routers.analysis import get_bedrock_client

router = APIRouter(prefix="/api/community", tags=["community"])

S3_BUCKET  = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
EXTRACT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

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
    """
    Use Claude Haiku to extract the suspicious message text visible in the image.
    Returns the extracted text, or empty string if nothing useful found.
    """
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
        return ""  # Non-critical — don't fail the post if extraction fails


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
    indicators: Optional[str] = Form(None),  # JSON array string
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
        _upload_to_s3(image_bytes, image.content_type, image_key)

        # Auto-extract message from image if not already provided
        if not original_message and image_bytes:
            extracted = _extract_message_from_image(image_bytes, image_content_type)
            if extracted:
                original_message = extracted

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
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List community posts, newest first. Public endpoint."""
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(CommunityPost, User.username, User.full_name)
        .join(User, CommunityPost.user_id == User.id)
        .where(CommunityPost.is_published == True)
        .order_by(desc(CommunityPost.created_at))
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    posts = []
    for post, username, full_name in rows:
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
            created_at=post.created_at.isoformat(),
        ))

    return PostListResponse(posts=posts, total=total)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a post. Only the author can delete their own post."""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

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

S3_BUCKET  = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

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
    indicators: Optional[str] = Form(None),  # JSON array string
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a community post with optional image upload."""
    if not caption and not original_message and not image:
        raise HTTPException(status_code=400, detail="Post must have content or an image.")

    image_key = None
    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type '{image.content_type}'. Allowed: JPEG, PNG, WEBP, GIF."
            )
        file_bytes = await image.read()
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        image_key = f"community/{current_user.id}/{uuid.uuid4()}.{ext}"
        _upload_to_s3(file_bytes, image.content_type, image_key)

    post = CommunityPost(
        user_id=current_user.id,
        caption=caption,
        scam_type=scam_type,
        original_message=original_message,
        note=note,
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=indicators,  # stored as JSON string
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
        created_at=post.created_at.isoformat(),
    )


@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List community posts, newest first. Public endpoint."""
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(CommunityPost).where(CommunityPost.is_published == True)
    )
    total = count_result.scalar()

    # Get posts with author username
    result = await db.execute(
        select(CommunityPost, User.username, User.full_name)
        .join(User, CommunityPost.user_id == User.id)
        .where(CommunityPost.is_published == True)
        .order_by(desc(CommunityPost.created_at))
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    posts = []
    for post, username, full_name in rows:
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
            created_at=post.created_at.isoformat(),
        ))

    return PostListResponse(posts=posts, total=total)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a post. Only the author can delete their own post."""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

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
