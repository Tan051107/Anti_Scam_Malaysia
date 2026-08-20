# -*- coding: utf-8 -*-
"""Database connection and session management.

Set ``DATABASE_URL`` for a direct PostgreSQL connection. Alternatively, set
the RDS variables plus ``RDS_SECRET_ARN`` to retrieve the password from AWS
Secrets Manager. No deployment-specific database settings are stored here.
"""

import json
import os
import ssl
from urllib.parse import quote_plus

import boto3
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


def _required(name: str) -> str:
    """Return a required setting or explain how to configure the backend."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} must be set in the backend environment. "
            "Copy .env.example to .env and configure the database."
        )
    return value


def _async_database_url(url: str) -> str:
    """Convert common PostgreSQL URLs to SQLAlchemy's asyncpg dialect."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql+psycopg2://")
    raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URL.")


def _get_db_password() -> str:
    """Retrieve the RDS password from AWS Secrets Manager."""
    secret_arn = _required("RDS_SECRET_ARN")
    region = _required("AWS_REGION")
    client = boto3.client(
        "secretsmanager",
        region_name=region,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    secret = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
    password = secret.get("password")
    if not password:
        raise RuntimeError("The AWS secret must contain a non-empty 'password' field.")
    return password


def _rds_database_url() -> str:
    """Build an async PostgreSQL URL from RDS settings and a managed secret."""
    host = _required("RDS_HOST")
    port = _required("RDS_PORT")
    database = _required("RDS_DB")
    user = _required("RDS_USER")
    password = quote_plus(_get_db_password())
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def _ssl_connect_args() -> dict:
    """Build SSL options only when a certificate path is explicitly configured."""
    certificate = os.getenv("RDS_SSL_CERT", "").strip()
    if not certificate:
        return {}
    if not os.path.isfile(certificate):
        raise RuntimeError(f"RDS_SSL_CERT does not exist: {certificate}")
    return {"ssl": ssl.create_default_context(cafile=certificate)}


def _build_engine():
    direct_url = os.getenv("DATABASE_URL", "").strip()
    url = _async_database_url(direct_url) if direct_url else _rds_database_url()
    return create_async_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        connect_args=_ssl_connect_args(),
    )


engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Yield one transactional database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
