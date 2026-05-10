# -*- coding: utf-8 -*-
"""
Database connection and session management.
Uses SQLAlchemy async engine with asyncpg driver for Amazon RDS PostgreSQL.

Password is fetched from AWS Secrets Manager at startup so it never needs
to be stored in .env or committed to source control.
"""

import json
import os
import boto3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

RDS_HOST     = os.getenv("RDS_HOST", "anti-scam-db.c6r4gac2i011.us-east-1.rds.amazonaws.com")
RDS_PORT     = os.getenv("RDS_PORT", "5432")
RDS_DB       = os.getenv("RDS_DB", "postgres")
RDS_USER     = os.getenv("RDS_USER", "postgres")
RDS_SECRET   = os.getenv(
    "RDS_SECRET_ARN",
    "arn:aws:secretsmanager:us-east-1:037427723047:secret:rds!db-ea21ed4f-c3d6-4285-b3df-b1e6023b8477-SZ2WJ8",
)
AWS_REGION   = os.getenv("AWS_REGION", "us-east-1")
SSL_CERT     = os.path.join(os.path.dirname(__file__), "global-bundle.pem")


# ─────────────────────────────────────────────
# Fetch password from Secrets Manager
# ─────────────────────────────────────────────

def _get_db_password() -> str:
    """Retrieve the RDS password from AWS Secrets Manager."""
    sm = boto3.client(
        "secretsmanager",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    secret = sm.get_secret_value(SecretId=RDS_SECRET)["SecretString"]
    return json.loads(secret)["password"]


# ─────────────────────────────────────────────
# Build async engine
# ─────────────────────────────────────────────

def _build_engine():
    password = _get_db_password()

    # URL-encode special characters in password
    from urllib.parse import quote_plus
    encoded_password = quote_plus(password)

    url = (
        f"postgresql+asyncpg://{RDS_USER}:{encoded_password}"
        f"@{RDS_HOST}:{RDS_PORT}/{RDS_DB}"
    )

    # SSL connect args for asyncpg
    ssl_args = {}
    if os.path.exists(SSL_CERT):
        import ssl
        ssl_ctx = ssl.create_default_context(cafile=SSL_CERT)
        ssl_args = {"ssl": ssl_ctx}

    return create_async_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        connect_args=ssl_args,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─────────────────────────────────────────────
# Base class for all ORM models
# ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────
# FastAPI dependency — yields a DB session per request
# ─────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
