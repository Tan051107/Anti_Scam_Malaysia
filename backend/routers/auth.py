# -*- coding: utf-8 -*-
"""
Authentication Router
Handles user signup, login, token refresh, and profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, field_validator
import re

from database import get_db
from models.orm import User
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("Username must be 3–50 characters: letters, numbers, underscores only.")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str | None
    is_verified: bool
    created_at: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""

    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Check username uniqueness
    existing_username = await db.execute(select(User).where(User.username == request.username))
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This username is already taken.")

    user = User(
        email=request.email,
        username=request.username,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    await db.flush()  # get the generated ID before commit

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login with email/username and password. Returns JWT tokens."""

    # Accept either email or username in the `username` field
    if "@" in form.username:
        result = await db.execute(select(User).where(User.email == form.username))
    else:
        result = await db.execute(select(User).where(User.username == form.username))

    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
    )
