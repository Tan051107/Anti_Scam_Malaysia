#!/usr/bin/env python3
"""
RDS PostgreSQL connection test.
Retrieves password from AWS Secrets Manager via boto3 and connects with SSL.
"""

import json
import os
import boto3
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SECRET_ARN = "arn:aws:secretsmanager:us-east-1:037427723047:secret:rds!db-ea21ed4f-c3d6-4285-b3df-b1e6023b8477-SZ2WJ8"
RDS_HOST   = "anti-scam-db.c6r4gac2i011.us-east-1.rds.amazonaws.com"
RDS_PORT   = 5432
RDS_DB     = "postgres"
RDS_USER   = "postgres"
SSL_CERT   = "./global-bundle.pem"

# ── 1. Fetch password from Secrets Manager ────────────────────
print("Fetching credentials from AWS Secrets Manager...")
try:
    sm = boto3.client(
        "secretsmanager",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    secret_str = sm.get_secret_value(SecretId=SECRET_ARN)["SecretString"]
    password = json.loads(secret_str)["password"]
    print("[OK] Credentials retrieved from Secrets Manager")
except Exception as e:
    print(f"[FAIL] Could not fetch secret: {type(e).__name__}: {e}")
    raise

# ── 2. Connect to RDS ─────────────────────────────────────────
print(f"Connecting to {RDS_HOST}:{RDS_PORT}/{RDS_DB} with SSL...")
conn = None
try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database=RDS_DB,
        user=RDS_USER,
        password=password,
        sslmode="verify-full",
        sslrootcert=SSL_CERT,
        connect_timeout=10,
    )
    cur = conn.cursor()

    cur.execute("SELECT version();")
    print(f"[OK] Connected successfully!")
    print(f"[OK] PostgreSQL: {cur.fetchone()[0]}")

    cur.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    )
    tables = [row[0] for row in cur.fetchall()]
    if tables:
        print(f"[OK] Existing tables: {tables}")
    else:
        print("[OK] No tables yet — ready for first migration.")

    cur.close()
    print("\n✅ Database connection is working correctly.")

except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    raise
finally:
    if conn:
        conn.close()
