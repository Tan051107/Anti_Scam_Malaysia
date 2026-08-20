#!/usr/bin/env python3
"""Check recent community posts using the configured database connection."""
import asyncio

async def check():
    from sqlalchemy import text
    from database import engine

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
