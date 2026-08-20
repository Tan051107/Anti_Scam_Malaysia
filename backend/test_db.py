#!/usr/bin/env python3
"""Test the configured PostgreSQL connection without exposing credentials."""

import json
import os
from urllib.parse import quote_plus

import boto3
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url.removeprefix("postgresql+asyncpg://")
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg2://")
    if url.startswith("postgres://"):
        return "postgresql://" + url.removeprefix("postgres://")
    return url


def _database_url() -> str:
    direct_url = os.getenv("DATABASE_URL", "").strip()
    if direct_url:
        return _sync_url(direct_url)

    region = _required("AWS_REGION")
    secret_arn = _required("RDS_SECRET_ARN")
    client = boto3.client(
        "secretsmanager",
        region_name=region,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    secret = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
    password = quote_plus(secret["password"])
    return (
        f"postgresql://{_required('RDS_USER')}:{password}"
        f"@{_required('RDS_HOST')}:{_required('RDS_PORT')}/{_required('RDS_DB')}"
    )


connect_args = {"connect_timeout": 10}
certificate = os.getenv("RDS_SSL_CERT", "").strip()
if certificate:
    if not os.path.isfile(certificate):
        raise RuntimeError(f"RDS_SSL_CERT does not exist: {certificate}")
    connect_args.update({"sslmode": "verify-full", "sslrootcert": certificate})

print("Connecting to the configured PostgreSQL database...")
conn = None
try:
    conn = psycopg2.connect(_database_url(), **connect_args)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("[OK] Connected successfully!")
    print(f"[OK] PostgreSQL: {cur.fetchone()[0]}")
    cur.close()
except Exception as error:
    print(f"[FAIL] {type(error).__name__}: {error}")
    raise
finally:
    if conn:
        conn.close()
