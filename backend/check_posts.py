#!/usr/bin/env python3
"""Check community posts in DB and S3 image keys."""
import asyncio, os, json, ssl, boto3
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()

async def check():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    sm = boto3.client("secretsmanager", region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
    pw = json.loads(sm.get_secret_value(SecretId=os.getenv("RDS_SECRET_ARN"))["SecretString"])["password"]

    ssl_ctx = ssl.create_default_context(cafile="global-bundle.pem")
    url = "postgresql+asyncpg://postgres:{}@{}/postgres".format(quote_plus(pw), os.getenv("RDS_HOST"))
    engine = create_async_engine(url, connect_args={"ssl": ssl_ctx})

    async with engine.connect() as conn:
        rows = (await conn.execute(text(
            "SELECT id, image_key, original_message, risk_level FROM community_posts ORDER BY created_at DESC LIMIT 5"
        ))).fetchall()

        if not rows:
            print("[INFO] No posts in community_posts table yet — share a post first")
        else:
            print(f"[OK] Found {len(rows)} post(s):")
            for r in rows:
                print(f"  id={str(r[0])[:8]}... image_key={r[1]} risk={r[3]} msg={str(r[2])[:50]}")

    await engine.dispose()

asyncio.run(check())
